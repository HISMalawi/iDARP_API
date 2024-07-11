import ast
import io
import json
from datetime import datetime, timedelta
from collections import deque
from typing import List, Dict, Any

import pdfkit
import requests
from django.conf import settings
from django.db import transaction
from django.db.models import F, OuterRef, Subquery  # , delete_recursively
from django.http import JsonResponse, HttpResponse, HttpResponseNotFound
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import ensure_csrf_cookie
from PyPDF2 import PdfFileReader, PdfFileWriter, PdfWriter, PdfReader
from rest_framework import generics, viewsets
from rest_framework import permissions
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from data_requests.serializers import *
from notifications.views import RequestNotificationCreateView, PatchRequestNotificationView
from .idarp.stateGraph import StatesGraph
from .utils.pad_with_zeros import PadZeros
from .utils.request_error_handler import ExceptionHandler


# Create your views here.


def process_request(request):
    request_purposes = RequestPurpose.objects.filter(
        request_id=request['request_id'])

    request_states = RequestState.objects.filter(request=request['request_id']).values(
        "created_on",
        "request_state_id",
        "request_id",
        "org_role_id",
        "attention",
        "state_lookup_id",
        "reason",
        "responded_on",
        "attended_by_id",
        "reminders_count",
        "stage_order",
        "stage_type",
        "branch_level",
        "pos_x",
        "pos_y",
        "icon",
        "state_lookup__state",
        "attended_by__user__user_id",
        "attended_by__user__fname",
        "attended_by__user__sname",
        "org_role_id__org__org_id",
        "org_role_id__org__name",
        "org_role_id__org__domain",
        "org_role_id__org__description",
        "org_role_id__org__active",
        "org_role_id__org__country"
    ).distinct()

    purpose_list = [
        {
            'purpose_id': rp.purpose.purpose_id,
            'purpose': rp.purpose.purpose,
            'purpose_description': rp.purpose_description,
        }
        for rp in request_purposes
    ]

    request['purposes'] = purpose_list

    request['requester'] = {
        'user_id': request.pop('requester__user__user_id'),
        'fname': request.pop('requester__user__fname'),
        'sname': request.pop('requester__user__sname'),
        'designation': request.pop('requester__user__designation'),
        'phone': request.pop('requester__user__phone'),
        'org_email': request.pop('requester__user__org_email'),
    }

    organization = {
        'org_id': request.pop('requester__org_role__org__org_id'),
        'name': request.pop('requester__org_role__org__name'),
        'domain': request.pop('requester__org_role__org__domain'),
        'description': request.pop('requester__org_role__org__description'),
        'active': request.pop('requester__org_role__org__active'),
        'country': request.pop('requester__org_role__org__country'),
    }

    request['request_states'] = [

        {
            "request_id": state['request_id'],
            "request_state_id": state['request_state_id'],
            "state": state['state_lookup__state'],
            "org_role_id": state['org_role_id'],
            "attention": state['attention'],
            "reason": state['reason'],
            "created_on": state['created_on'],
            "reminders_count": state['reminders_count'],
            "responded_on": state['responded_on'],
            "stage_order": state['stage_order'],
            "stage_type": state['stage_type'],
            "branch_level": state['branch_level'],
            "pos_x": state['pos_x'],
            "pos_y": state['pos_y'],
            "icon": state['icon'],
            "attended_by": {
                "user_id": state['attended_by__user__user_id'],
                "fname": state['attended_by__user__fname'],
                "sname": state['attended_by__user__sname'],
            },
            'org': {
                'org_id': state['org_role_id__org__org_id'],
                'name': state['org_role_id__org__name'],
                'domain': state['org_role_id__org__domain'],
                'description': state['org_role_id__org__description'],
                'active': state['org_role_id__org__active'],
                'country': state['org_role_id__org__country'],
            },
        }

        for state in request_states
    ]

    request['organization'] = organization

    return request


class PurposeView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Purpose.objects.all()
    serializer_class = PurposeSerializer


class DataRequestDeleteView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = DataRequest.objects.all()
    serializer_class = DataRequestSerializer


class SubmitDataRequestView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = GuestDataRequestSerializer

    def handle_exception(self, exc):
        return super().handle_exception(exc)

    def post(self, request, *args, **kwargs):
        client = storage.Client(credentials=settings.GS_CREDENTIALS)
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        bucket_name = settings.GS_BUCKET_NAME
        sub_on = timezone.now() if data['submitted'] == True else None

        try:
            with transaction.atomic():

                savepoint = transaction.savepoint()
                # Create Data Request
                data_request = DataRequest.objects.create(
                    title=data['title'],
                    needed_on=data['needed_on'],
                    requester_id=data['requester'],
                    additional_ethics_committee_name=data['additional_ethics_committee_name'],
                    protocol_ref_num=data['protocol_ref_num'],
                    ethics_committee=data['ethics_committee'],
                    ethics_approval_letter=data['ethics_approval_letter'],
                    exempted=data['exempted'],
                    submitted=data['submitted'],
                    submitted_on=sub_on,
                    data_format=data['data_format'],
                    direct_access_from=data['direct_access_from'],
                    direct_access_to=data['direct_access_to'],
                    no_date_limit=data['no_date_limit'],
                    principal_fname=data['principal_fname'],
                    principal_sname=data['principal_sname'],
                    principal_phone=data['principal_phone'],
                    principal_email=data['principal_email'],
                    principal_occupation=data['principal_occupation'],
                    principal_institution=data['principal_institution']
                )

                # Creating Requested Dataset

                requested_dataset = RequestedDataset.objects.create(
                    request_id=data_request.pk,
                    data_source_id=data['data_source_id'],
                    dataset_description=data['dataset_description'],
                    filters=data['filters']
                    # data_specs_path=data['data_specs_path'],
                )

                def upload_file(file_data, file_mime, blob_name):
                    if data.get(file_data):
                        uploaded_file = data[f'{file_data}']
                        file_path_mime = data[f"{file_mime}"]
                        blob_name = f"idarp_files/{blob_name}_{PadZeros.pad(data_request.pk)}.{file_path_mime.split('/')[1]}"
                        bucket = client.get_bucket(bucket_name)
                        blob = bucket.blob(blob_name, chunk_size=262144)
                        decoded_file = base64.b64decode(uploaded_file)
                        blob.upload_from_string(decoded_file, content_type=file_path_mime)
                        return blob.public_url

                data_request.file_path = upload_file('file_path_data', 'file_path_mime', 'data_sharing_agreement')
                data_request.ethics_doc_path = upload_file('ethics_doc_path_data', 'ethics_doc_path_mime',
                                                           'ethics_approval_letter')
                data_request.additional_IRB_file_path = upload_file('additional_IRB_file_path_data',
                                                                    'additional_IRB_file_path_mime',
                                                                    'additional_IRB_file')
                requested_dataset.data_specs_path = upload_file('data_specs_data', 'data_specs_mime',
                                                                'variable_document')
                data_request.save()
                requested_dataset.save()

                # Add request purposes, list of devices, list of staff, and dataset variables
                for field_name, serializer_class in [
                    ('request_purposes', RequestPurposeSerializer),
                    ('list_of_devices', DataHandlingDeviceSerializer),
                    ('list_of_staff', StaffListSerializer),
                ]:
                    data[field_name] = [item.update({'request': data_request.pk}) or item for item in data[field_name]]
                    serializer = serializer_class(data=data[field_name], many=True, context={'request': data_request})
                    serializer.is_valid(raise_exception=True)
                    serializer.save()

                # Adding Dataset Variables
                for i in request.data['dataset_variables']:
                    i['rdataset'] = requested_dataset.pk

                dateset_variables_serializer = DatasetVariableCustomSerializer(data=request.data['dataset_variables'],
                                                                               many=True)
                dateset_variables_serializer.is_valid(raise_exception=True)
                dateset_variables_serializer.save()

                # Get default approval procedure
                try:
                    default_procedure = ApprovalProcedure.objects.get(
                        is_default=True)

                except ApprovalProcedure.DoesNotExist:
                    # Handle the case when no default procedure is found
                    default_procedure = None

                if default_procedure is not None:
                    assignedroleid = AssignedRole.objects.all().filter(
                        user_id=data_request.requester_id, assigned_by='Default').values(
                        'assigned_role_id'
                    )
                    RequestStateCreateView.createState(data_request.pk, assignedroleid, StageDetailView.getStage(1))

                    return Response(
                        {'code': '201', 'message': 'data request created successfully.', 'request_id': data_request.pk},
                        status=status.HTTP_201_CREATED)

        except Exception as e:
            transaction.rollback(savepoint)
            return Response({'code': '400', 'message': f'bad request.{e}'}, status=status.HTTP_200_OK)


class GetUserRequest(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = self.request.user  # Corrected line

        try:
            data_requests = list(DataRequest.objects.filter(requester__user=user))
        except DataRequest.DoesNotExist:
            return Response({'error': 'DataRequests not found'}, status=status.HTTP_404_NOT_FOUND)

        user_requests: list[dict[str | Any, Any]] = []
        try:
            for data_request in data_requests:
                print(data_request.pk)
                request_states = RequestState.objects.filter(request_id=data_request.pk).distinct()
                request_states_list = []

                for state in request_states:
                    state_dict = {
                        'request_state_id': state.request_state_id,
                        'request': state.request.request_id,
                        'org_role': state.org_role.role.role,
                        'state': state.state_lookup.state,
                        'reason': state.reason,
                        'created_on': state.created_on,
                        'responded_on': state.responded_on,
                        'reminders_count': state.reminders_count,
                        'stage_order': state.stage_order,
                        'stage_type': state.stage_type,
                        'branch_level': state.branch_level
                    }
                    request_states_list.append(state_dict)

                user_requests.append({
                    'request_id': data_request.pk,
                    'requester': data_request.requester.assigned_role_id,
                    'date_created': data_request.date_created,
                    'file_path': data_request.file_path,
                    'title': data_request.title,
                    'department': data_request.department,
                    'needed_on': data_request.needed_on,
                    'ethics_committee': data_request.ethics_committee.irb_name,
                    'additional_ethics_committee_name': data_request.additional_ethics_committee_name,
                    'additional_IRB_file_path': data_request.additional_IRB_file_path,
                    'protocol_ref_num': data_request.protocol_ref_num,
                    'ethics_doc_path': data_request.ethics_doc_path,
                    'ethics_approval_letter': data_request.ethics_approval_letter,
                    'submitted': data_request.submitted,
                    'submitted_on': data_request.submitted_on,
                    'data_format': data_request.data_format,
                    'direct_access_from': data_request.direct_access_from,
                    'direct_access_to': data_request.direct_access_to,
                    'no_date_limit': data_request.no_date_limit,
                    'principal_fname': data_request.principal_fname,
                    'principal_sname': data_request.principal_sname,
                    'principal_phone': data_request.principal_phone,
                    'principal_email': data_request.principal_email,
                    'principal_occupation': data_request.principal_occupation,
                    'principal_institution': data_request.principal_institution,
                    'request_states': request_states_list
                })
            return Response(user_requests, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DataRequestView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = DataRequest.objects.all()
    serializer_class = DataRequestSerializer

    # Process each request and its related data

    def get_queryset(self):
        user = self.request.user
        return DataRequest.objects.filter(requester__user=user)

    def handle_exception(self, exc):
        if isinstance(exc, ValidationError) and hasattr(exc, 'get_codes'):
            error_message = ""
            errors = exc.get_codes()

            if 'rdataset' in errors:
                error_message = ExceptionHandler.handle_error(
                    errors, 'rdataset', 'Data Request')
            elif 'preset' in errors:
                error_message = ExceptionHandler.handle_error(
                    errors, 'preset', 'Preset')
            else:
                return super().handle_exception(exc)

            return Response({'code': '400', 'message': error_message}, status=status.HTTP_200_OK)
        return super().handle_exception(exc)

    def get(self, request, *args, **kwargs):

        queryset = self.get_queryset()

        request_id = self.request.query_params.get('request_id')

        org_role_id = self.request.query_params.get('org_role_id')

        dr_status = self.request.query_params.get('status', [])

        def filter_assigned_roles_by_attended_by(self, attended_by_id):
            return (AssignedRole.objects.filter(assigned_role_id=attended_by_id).select_related('user').values(
                'user__user_id'
            ).annotate(
                user_id=F('user__user_id'), fname=F('user__fname'), sname=F('user__sname'),
                org_email=F('user__org_email'), department=F('user__department'), designation=F('user__designation'),
                phone=F('user__phone'), org_name=F('user__org__name')
            ))

        # Getting the request states attended_by and request_state_id where not null
        def extract_attended_by_not_null_states(request_states):
            attended_by_states = []
            for state in request_states:
                if state['attended_by'] is not None:
                    attended_by_states.append({
                        'request_state_id': state['request_state_id'],
                        'attended_by': state['attended_by'],
                    })
            return attended_by_states

        if request_id:

            try:
                custodianTest = self.getDataSetCustodians(request_id)
                print(custodianTest)
                request = (DataRequest.objects.filter(request_id=request_id)
                           .prefetch_related('requester__user', 'requester__org_role__org').annotate(
                    irb_name=F('ethics_committee__irb_name')
                ).values(
                    'request_id',
                    'requester',
                    'requester__user__user_id',
                    'requester__user__fname',  # Include the desired user fields
                    'requester__user__sname',
                    'requester__user__department',
                    'requester__user__tentative_organization',
                    'requester__user__designation',
                    'requester__user__org_email',
                    'requester__user__phone',
                    'requester__org_role__org__org_id',
                    'requester__org_role__org__name',  # Include the organization name
                    'requester__org_role__org__domain',  # Include the organization domain
                    # Include the organization description
                    'requester__org_role__org__description',
                    'requester__org_role__org__active',  # Include the organization active status
                    'requester__org_role__org__country',
                    'date_created',  # Include the purpose field
                    'title',
                    'exempted',
                    'file_path',
                    'needed_on',
                    'protocol_ref_num',
                    'ethics_doc_path',
                    'ethics_approval_letter',
                    'irb_name',
                    'additional_IRB_file_path',
                    'additional_ethics_committee_name',
                    'submitted',
                    'data_format',
                    'principal_fname',
                    'principal_sname',
                    'principal_phone',
                    'principal_email',
                    'principal_occupation',
                    'principal_institution',
                    'data_format',
                    'no_date_limit',
                    'direct_access_from',
                    'direct_access_to',
                    'submitted_on',
                    data_source=F('requesteddataset__data_source__source'),
                    dataset_description=F('requesteddataset__dataset_description'),
                    filters=F('requesteddataset__filters')
                ).distinct().first())

                if request['filters'] is not None:
                    request['filters'] = json.loads(request['filters'].replace("'", "\"").replace("None", "null"))

                if request is not None:
                    request_states = RequestState.objects.filter(request=request['request_id']).values(
                        "created_on",
                        "request_state_id",
                        "request_id",
                        "org_role_id",
                        "attention",
                        "state_lookup_id",
                        "reason",
                        "responded_on",
                        "attended_by_id",
                        "reminders_count",
                        "stage_order",
                        "stage_type",
                        "branch_level",
                        "pos_x",
                        "pos_y",
                        "icon",
                        "state_lookup__state",
                        "attended_by",
                        "org_role__role__role",
                        "org_role_id__org__org_id",
                        "org_role_id__org__name",
                        "org_role_id__org__domain",
                        "org_role_id__org__description",
                        "org_role_id__org__active",
                        "org_role_id__org__country"
                    ).distinct()

                    attended_by_states = extract_attended_by_not_null_states(request_states)
                    print(attended_by_states)

                    request_purposes = RequestPurpose.objects.filter(
                        request_id=request['request_id'])

                    purpose_list = [
                        {
                            'purpose_id': rp.purpose.purpose_id,
                            'purpose': rp.purpose.purpose,
                            'purpose_description': rp.purpose_description,
                        }
                        for rp in request_purposes
                    ]

                    request['purposes'] = purpose_list

                    request['requester'] = {
                        'user_id': request.pop('requester__user__user_id'),
                        'fname': request.pop('requester__user__fname'),
                        'sname': request.pop('requester__user__sname'),
                        'department': request.pop('requester__user__department'),
                        'designation': request.pop('requester__user__designation'),
                        'tentative_organization': request.pop('requester__user__tentative_organization'),
                        'phone': request.pop('requester__user__phone'),
                        'org_email': request.pop('requester__user__org_email'),
                    }

                    organization = {
                        'org_id': request.pop('requester__org_role__org__org_id'),
                        'name': request.pop('requester__org_role__org__name'),
                        'domain': request.pop('requester__org_role__org__domain'),
                        'description': request.pop('requester__org_role__org__description'),
                        'active': request.pop('requester__org_role__org__active'),
                        'country': request.pop('requester__org_role__org__country'),
                    }

                    # Update attended_by information with user details
                    for attended_state in attended_by_states:
                        user_info = filter_assigned_roles_by_attended_by(self, attended_state['attended_by'])

                        # Check if attended_by is an integer
                        if isinstance(attended_state['attended_by'], int):
                            attended_state['attended_by'] = {}

                        # Updating the attended_by dictionary with user information
                        attended_state['attended_by'].update(user_info[0] if user_info else {})

                    # Create a dictionary to map request state IDs to attended_by information
                    attended_by_info_dict = {state['request_state_id']: state['attended_by'] for state in
                                             attended_by_states}

                    # Add attended_by information to the request_states
                    for state in request_states:
                        # Add attended_by information from the dictionary
                        state['attended_by'] = attended_by_info_dict.get(state['request_state_id'], {})

                    request['request_states'] = [

                        {
                            "request_id": state['request_id'],
                            "request_state_id": state['request_state_id'],
                            "state": state['state_lookup__state'],
                            "org_role_id": state['org_role_id'],
                            "attention": state['attention'],
                            "reason": state['reason'],
                            "created_on": state['created_on'],
                            "reminders_count": state['reminders_count'],
                            "responded_on": state['responded_on'],
                            "stage_order": state['stage_order'],
                            "stage_type": state['stage_type'],
                            "branch_level": state['branch_level'],
                            "pos_x": state['pos_x'],
                            "pos_y": state['pos_y'],
                            "icon": state['icon'],
                            "role": state['org_role__role__role'],
                            "attended_by": state['attended_by'],
                            'org': {
                                'org_id': state['org_role_id__org__org_id'],
                                'name': state['org_role_id__org__name'],
                                'domain': state['org_role_id__org__domain'],
                                'description': state['org_role_id__org__description'],
                                'active': state['org_role_id__org__active'],
                                'country': state['org_role_id__org__country'],
                            },
                        }

                        for state in request_states
                    ]

                    request['organization'] = organization

                # return Response(request, status=status.HTTP_200_OK)
                return JsonResponse(request, safe=False)

            except DataRequest.DoesNotExist:
                return Response({'code': '400', 'message': 'Data Request not found.'}, status=status.HTTP_200_OK)

        if org_role_id:

            try:
                request_states = (RequestState.objects.select_related('request').filter(
                    org_role=org_role_id
                ).values('request_id').distinct())

                if dr_status:
                    dr_status = ast.literal_eval(dr_status)

                    request_states = request_states.filter(
                        state_lookup__state__in=dr_status)
            except RequestState.DoesNotExist:
                return Response({'code': '400', 'message': 'Request state not found.'}, status=status.HTTP_200_OK)

            try:

                requests = DataRequest.objects.filter(
                    Q(request_id__in=request_states)
                ).prefetch_related('requester__user', 'requester__org_role__org').values(
                    'request_id',
                    'requester',
                    'requester__user__user_id',
                    'requester__user__fname',
                    'requester__user__sname',
                    'requester__user__designation',
                    'requester__user__org_email',
                    'requester__user__phone',
                    'requester__org_role__org__org_id',
                    'requester__org_role__org__name',
                    'requester__org_role__org__domain',
                    'requester__org_role__org__description',
                    'requester__org_role__org__active',
                    'requester__org_role__org__country',
                    'date_created',
                    'title',
                    'needed_on',
                    'protocol_ref_num',
                    'ethics_doc_path',
                    'ethics_approval_letter',
                    'ethics_committee__irb_name',
                    'additional_IRB_file_path',
                    'additional_ethics_committee_name',
                    'data_format',
                    'direct_access_from',
                    'direct_access_to',
                    'no_date_limit',
                    'principal_fname',
                    'principal_sname',
                    'principal_phone',
                    'principal_email',
                    'principal_occupation',
                    'principal_institution',
                    'submitted',
                    'submitted_on'
                ).distinct()
                # print(request['data_source'])
                # if request['filters'] is not None:
                #     request['filters'] = json.loads(request['filters'].replace("'", "\""))

                if requests:
                    result = []
                    for request in requests:
                        processed_request = process_request(request)
                        result.append(processed_request)
                    return Response(result, status=status.HTTP_200_OK)

                else:
                    return Response({'code': '400', 'message': 'Data Requests not found.'}, status=status.HTTP_200_OK)

            except DataRequest.DoesNotExist:

                return Response({'code': '400', 'message': 'Data Request not found.'}, status=status.HTTP_200_OK)

        serialized_data = self.get_serializer(queryset, many=True).data
        return Response(serialized_data, status=status.HTTP_200_OK)

    @classmethod
    def getDataSetCustodians(cls, requestId):
        distinct_datasources = list(
            RequestedDataset.objects.filter(request_id=requestId).select_related("data_source").annotate(
                custodian=F('data_source__datacustodian__org_role__org__name'),
                broker=F('data_source__datacustodian__broker'),
                data_source_name=F('data_source__source'),
                org_role_id=F('data_source__datacustodian__org_role__org_role_id'),
                role=F('data_source__datacustodian__org_role__role__role'),
            ).values(
                'data_source_id',
                'data_source_name',
                'custodian',
                'broker',
                'org_role_id',
                'role',
            ).distinct())
        return distinct_datasources

    def update(self, request, *args, **kwargs):

        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            # Store the original instance values
            original_values = instance.__dict__.copy()

            self.perform_update(serializer)

            # Get the updated instance after performing the update
            updated_instance = self.get_object()

            # Compare the original values with the updated values
            changed_fields = {}
            for field, value in updated_instance.__dict__.items():
                if field in original_values and original_values[field] != value:
                    changed_fields[field] = value

            if 'submitted' in changed_fields:
                if original_values['submitted'] is None or original_values['submitted'] == False:
                    updated_instance.submitted = True
                    updated_instance.submitted_on = timezone.now()
                    # Save the changes to the instance
                    updated_instance.save()

                    # Creating Request States
                    try:

                        dar_org_role = OrgRole.objects.filter(role__role='Data Access Reviewer',
                                                              orgrolestatus__status=True).order_by(
                            '-orgrolestatus__changed_on').first()

                        dsr_org_role = OrgRole.objects.filter(role__role='Data Security Reviewer',
                                                              orgrolestatus__status=True).order_by(
                            '-orgrolestatus__changed_on').first()

                        if dar_org_role and dsr_org_role:

                            RequestState.objects.create(
                                request=updated_instance, org_role=dar_org_role, created_on=timezone.now())
                            RequestState.objects.create(
                                request=updated_instance, org_role=dsr_org_role, created_on=timezone.now())

                            return Response({'code': '201', 'message': 'Data request updated successfully.',
                                             'data_request': serializer.data},
                                            status=status.HTTP_201_CREATED)
                        else:

                            transaction.set_rollback(True)
                            return Response({'code': '400', 'message': 'Error saving request states.'},
                                            status=status.HTTP_200_OK)

                    except OrgRole.DoesNotExist:
                        transaction.set_rollback(True)
                        return Response({'code': '400', 'message': 'Data Access and Data Security Reviewers not set.'},
                                        status=status.HTTP_200_OK)
                else:
                    # Rollback the changes
                    transaction.set_rollback(True)
                    return Response({'code': '400', 'message': 'Can not update submitted data request.'},
                                    status=status.HTTP_200_OK)

            else:
                if original_values['submitted'] == True:
                    # Rollback the changes
                    transaction.set_rollback(True)
                    return Response({'code': '400', 'message': 'Can not update submitted data request.'},
                                    status=status.HTTP_200_OK)

                else:
                    # Save the changes to the instance
                    updated_instance.save()

                    return Response({'code': '201', 'message': 'Data request updated successfully.',
                                     'data_request': serializer.data},
                                    status=status.HTTP_201_CREATED)


class RequestedDatasetView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = RequestedDataset.objects.all()
    serializer_class = CustomRequestedDatasetSerializer

    def get_queryset(self):
        return self.queryset.all()

    def get(self, *args, **kwargs):
        queryset = self.get_queryset()
        request_id = self.request.query_params.get('request_id')

        if request_id:
            queryset = queryset.filter(request_id=request_id)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        serializer.save()

        return Response({'code': '201', 'message': 'Requested Dataset added successfully', },
                        status=status.HTTP_201_CREATED)


class DatasetVariableView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = DatasetVariable.objects.all()
    serializer_class = DatasetVariableSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        dataset_variable_id = self.request.query_params.get(
            'dataset_variable_id')
        rdataset_id = self.request.query_params.get('rdataset_id')

        if dataset_variable_id:
            queryset = queryset.filter(dataset_variable_id=dataset_variable_id)

        if rdataset_id:
            queryset = queryset.filter(rdataset_id=rdataset_id)

        return queryset

    def create(self, request, *args, **kwargs):

        serializer = DatasetVariableCustomSerializer(
            data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({'code': '201', 'message': 'Dataset variable added successfully'},
                        status=status.HTTP_201_CREATED)


class DataRequestHistoryView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = DataRequest.objects.all()
    serializer_class = DataRequestSerializer

    def get_queryset(self):
        return self.queryset.all()

    def handle_exception(self, exc):
        if isinstance(exc, ValidationError) and hasattr(exc, 'get_codes'):
            error_message = ""
            errors = exc.get_codes()

            if 'rdataset' in errors:
                error_message = ExceptionHandler.handle_error(
                    errors, 'rdataset', 'Data Request')
            elif 'preset' in errors:
                error_message = ExceptionHandler.handle_error(
                    errors, 'preset', 'Preset')
            else:
                return super().handle_exception(exc)

            return Response({'code': '400', 'message': error_message}, status=status.HTTP_200_OK)
        return super().handle_exception(exc)

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        preset_id = self.request.query_params.get('preset_id')

        if preset_id:

            try:
                preset = DatasetPreset.objects.get(preset_id=preset_id)
                queryset = queryset.filter(preset=preset)

            except DatasetPreset.DoesNotExist:
                return Response({'code': '400', 'message': 'Preset not found'}, status=status.HTTP_200_OK)

        serialized_data = self.get_serializer(queryset, many=True).data
        return Response(serialized_data, status=status.HTTP_200_OK)


class DatasetPresetView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = DatasetPreset.objects.all()
    serializer_class = DatasetPresetSerializer

    def get_queryset(self):
        return self.queryset.all()

    def handle_exception(self, exc):
        if isinstance(exc, ValidationError) and hasattr(exc, 'get_codes'):
            error_message = ""
            errors = exc.get_codes()

            if 'rdataset' in errors:
                error_message = ExceptionHandler.handle_error(
                    errors, 'rdataset', 'Data Request')
            elif 'preset' in errors:
                error_message = ExceptionHandler.handle_error(
                    errors, 'preset', 'Preset')
            else:
                return super().handle_exception(exc)

            return Response({'code': '400', 'message': error_message}, status=status.HTTP_200_OK)
        return super().handle_exception(exc)

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        preset_id = self.request.query_params.get('preset_id')

        if preset_id:

            try:
                preset = DatasetPreset.objects.get(preset_id=preset_id)
                queryset = queryset.filter(preset=preset)

            except DatasetPreset.DoesNotExist:
                return Response({'code': '400', 'message': 'Preset not found'}, status=status.HTTP_200_OK)
        serialized_data = self.get_serializer(queryset, many=True).data
        return Response(serialized_data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        serializer.save()

        return Response({'code': '201', 'message': 'Data request preset added successfully', },
                        status=status.HTTP_201_CREATED)


class DataRequestStateView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = RequestState.objects.all()
    serializer_class = RequestStateUpdateSerializer

    def get_queryset(self):
        return self.queryset.all()

    def handle_exception(self, exc):
        if isinstance(exc, ValidationError) and hasattr(exc, 'get_codes'):
            error_message = ""
            errors = exc.get_codes()

            if 'state_id' in errors:
                error_message = "status field is required."
            elif 'request' in errors:
                error_message = "request field is required."
            elif 'org_role' in errors:
                error_message = "organization role field is required."
            elif 'assigned_role' in errors:
                error_message = "assigned role field is required."
            elif 'status' in errors:
                error_message = "status field is required."
            elif 'reason' in errors:
                error_message = "reason field is required."
            elif 'password' in errors:
                error_message = "password field is required."
            elif 'non_field_errors' in errors:
                return Response({'code': '605', 'message': 'Invalid input', 'errors': exc.detail['non_field_errors']},
                                status=status.HTTP_200_OK)
            else:
                return super().handle_exception(exc)

            return Response({'code': '400', 'message': error_message}, status=status.HTTP_200_OK)

        return super().handle_exception(exc)

    def update(self, request, *args, **kwargs):

        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data

        with transaction.atomic():

            self.perform_update(instance)
            serializer.save()

            if validated_data['status']:
                instance.state_lookup_id = 3
                instance.save()
                PatchRequestNotificationView.update_notification_read_status(instance.pk, validated_data['org_role'])
                self.updateNextStates(instance.pk)

            if not validated_data['status']:
                instance.state_lookup_id = 4
                # Save the updated instance
                instance.save()
                PatchRequestNotificationView.update_notification_read_status(instance.pk, validated_data['org_role'])
                self.denyRemainingStates(instance.request_id, validated_data['assigned_role'], instance.reason)
                RequestNotificationCreateView.create_request_notification(instance.pk)

            org_role = OrgRole.objects.get(pk=validated_data['org_role'])
            role_name = org_role.role.role
            return Response({'code': '200', 'message': 'request state updated successfully'}, status=status.HTTP_200_OK)

    # Looking for the next States and setting them to 2 which is unattended when the previous are Approved
    @classmethod
    def updateNextStates(cls, state_id):
        try:
            with transaction.atomic():
                queryset = NextState.objects.filter(current_state_id=state_id).select_related('next').values(
                    'next_id'
                ).annotate(
                    stage_type=F('next__stage_type')
                )
                for q in queryset:
                    if RequestNotificationCreateView.previousStatesApproved(q['next_id']):
                        next_instance = RequestState.objects.get(pk=q['next_id'])
                        next_instance.state_lookup = StateLookup.objects.get(pk=2)
                        next_instance.created_on = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        next_instance.save()
                RequestNotificationCreateView.create_request_notification(q['next_id'])
        except Exception as e:
            # Handle the exception, log it, or raise it depending on your application's requirements
            print(f"An error occurred: {str(e)}")

    # this deny the remaining states in the request tracking tool.
    @classmethod
    def denyRemainingStates(cls, request_id, attended, reason):
        queryset = RequestState.objects.all().filter(request_id=request_id).select_related('state_lookup').annotate(
            status=F('state_lookup__state')
        ).values(
            'status', 'request_state_id'
        )
        queryset = list(queryset)
        for q in queryset:
            next_instance = RequestState.objects.get(pk=q['request_state_id'])
            if q['status'] in ['Unattended', 'Incoming']:
                next_instance.state_lookup = StateLookup.objects.get(pk=5)
                next_instance.responded_on = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                next_instance.attended_by_id = attended
                next_instance.reason = reason
                next_instance.created_on = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                next_instance.save()


class RequestStateCreateView(generics.CreateAPIView):
    queryset = RequestState.objects.all()
    serializer_class = RequestStateSerializer

    @classmethod
    def createState(cls, requestId, assignedroleId, current):
        visited = deque([])
        request_id = requestId

        def create_state(current):
            graph = {}
            nonlocal visited
            nonlocal request_id
            state_lookup_id = 1
            org_role = current['org_role_id']
            reason = None
            attended_by_id = None
            responded_on = None
            if current['stage_type'] == "Initial" or current['stage_order'] == 2:
                state_lookup_id = 3
                reason = "Interested in data"
                attended_by_id = assignedroleId
                responded_on = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            elif current['stage_activity'] == "Endorsement":
                # Checks for the Custodian assigned to the data source and if not a broker
                results = DataRequestView.getDataSetCustodians(request_id)
                for custodian in results:
                    if custodian["broker"] is not True and custodian["role"] == "Data Custodian":
                        org_role = custodian["org_role_id"]
                    elif custodian["broker"] is True and custodian["role"] == "Data Custodian":
                        org_role = custodian["org_role_id"]
            elif current["stage_activity"] == "Extraction":
                results = DataRequestView.getDataSetCustodians(request_id)
                for data_officer in results:
                    if data_officer["broker"] is not True and data_officer["role"] == "Data Officer":
                        org_role = data_officer["org_role_id"]
                    elif data_officer["broker"] is True and data_officer["role"] == "Data Officer":
                        org_role = data_officer["org_role_id"]
            elif current['stage_order'] == 3:
                state_lookup_id = 2
            else:
                state_lookup_id = 1

            state = RequestState.objects.create(
                state_lookup_id=state_lookup_id,
                reason=reason,
                responded_on=responded_on,
                attended_by_id=attended_by_id,
                org_role_id=org_role,
                request_id=request_id,
                branch_level=current['branch_level'],
                stage_order=current['stage_order'],
                stage_type=current['stage_type'],
                pos_x=current['pos_x'],
                pos_y=current['pos_y'],
                icon=current['icon'],
                reminders_count=0
            )
            state_id = state.pk
            request_state = state
            if request_state.state_lookup_id == 2:
                RequestNotificationCreateView.create_request_notification(state_id)

            for next in current['next']:
                next_state = None
                if next['stage_type'] == 'Merge':
                    if len(visited) > 0:
                        next_state = visited[-1]
                        visited.pop()
                    else:
                        next_state = create_state(next)
                        visited.append(next_state)
                else:
                    next_state = create_state(next)
                NextStateCreateView.createNextState(state_id, next_state)

            return state

        graph = create_state(current)
        visited.clear()
        return graph


class NextStateCreateView(generics.CreateAPIView):
    queryset = RequestState.objects.all()
    serializer_class = NextStateSerializer

    # ToDo: implement this code #####
    @classmethod
    def createNextState(cls, state_id, next_id):
        next = NextState.objects.create(
            current_state_id=state_id,
            next=next_id
        )

        return next


class RequestStateDetailAPIView(generics.RetrieveAPIView):
    queryset = RequestState.objects.all()
    serializer_class = RequestStateSerializer


class DataRequestEdgeView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = NextState.objects.all()
    serializer_class = NextStateSerializer

    def get_queryset(self):
        return self.queryset.all()

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        request_id = self.request.query_params.get('request_id')

        if request_id:
            queryset = queryset.filter(current_state__request__pk=request_id)

        serialized_data = self.get_serializer(queryset, many=True).data

        return Response(serialized_data, status=status.HTTP_200_OK)


class StageDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = StageSerializer

    def get(self, request, *args, **kwargs):
        data = StageDetailView.getStage(1)
        # response = JsonResponse(data, safe=False)
        return Response({'code': '200', 'message': 'Verification Successful', 'approvalProcedure': data},
                        status=status.HTTP_200_OK)

    @classmethod
    def getStage(cls, id=1):
        visited = []

        def get_stage(id):
            nonlocal visited
            activeOrgRoleQueryset = OrgRoleStatus.objects.select_related('org_role').values(
                'org_role_id',
                'status',
                'changed_on',
            ).annotate(
                role=F('org_role__role__role'),
                role_id=F('org_role__role__role_id'),
                org_id=F('org_role__org_id'),
                org_name=F('org_role__org__name')
            )
            approvalProcedureStageQueryset = Stage.objects.select_related(
                'approval_procedure',
                'role',
                'stage_type'
            ).filter(approval_procedure_id=1, stage_id=id).values(
                'stage_id',
                'stage_order',
                'role_id',
                'stage_activity',
                'branch_level',
                'pos_x',
                'pos_y',
                'icon'
            ).annotate(
                stage_type=F('stage_type__stage_type')
            ).order_by('stage_order')

            inner_join_queryset = approvalProcedureStageQueryset.annotate(
                role=Subquery(activeOrgRoleQueryset.filter(role_id=OuterRef('role_id')).values('role')[:1]),
                # I don't like the fact that this subquery is repeated
                org_role_id=Subquery(
                    activeOrgRoleQueryset.filter(role_id=OuterRef('role_id')).values('org_role_id')[:1]),
                # but at the time of coding this I didn't have much choice
                org_name=Subquery(activeOrgRoleQueryset.filter(role_id=OuterRef('role_id')).values('org_name')[:1])
                # as returning more than 1 columns from a subquery cauzed errors
            ).order_by('stage_order')
            data = list(inner_join_queryset)[0]
            data['next'] = []

            if data["stage_type"] == "Junction":
                StatesGraph.branch += 1
            elif data["stage_type"] == "Merge":
                StatesGraph.branch -= 1

            ##### Additional Code #####
            next = NextStage.objects.filter(current_stage_id=data['stage_id']).values()
            next = list(next)
            if id not in visited:
                for n in next:
                    data['next'].append(get_stage(n["next_id"]))
            visited.append(id)
            return data

        stages = get_stage(id)
        return stages


class PostRequestedDatasetView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = RequestedDataset.objects.all()
    serializer_class = PostRequestedDatasetSerializer

    def get_queryset(self):
        return self.queryset.all()

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        serializer.save()

        return Response({'code': '201', 'message': 'Requested Dataset added successfully', },
                        status=status.HTTP_201_CREATED)


class TestView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = StageSerializer

    def get(self, request, *args, **kwargs):
        data = TestView.getStage(1)
        # response = JsonResponse(data, safe=False)
        return Response({'code': '200', 'message': 'Verification Successful', 'approvalProcedure': data},
                        status=status.HTTP_200_OK)

    @classmethod
    def getStage(cls, id):
        visited = []

        def get_stage(id):
            nonlocal visited

            activeOrgRoleQueryset = OrgRoleStatus.objects.select_related('org_role').values(
                'org_role_id',
                'status',
                'changed_on',
            ).annotate(
                role=F('org_role__role__role'),
                role_id=F('org_role__role__role_id'),
                org_id=F('org_role__org_id'),
                org_name=F('org_role__org__name')
            )
            approvalProcedureStageQueryset = Stage.objects.select_related(
                'approval_procedure',
                'role',
                'stage_type'
            ).filter(approval_procedure_id=1, stage_id=id).values(
                'stage_id',
                'stage_order',
                'role_id',
                'stage_activity',
                'branch_level',
                'pos_x',
                'pos_y',
                'icon'
            ).annotate(
                stage_type=F('stage_type__stage_type')
            ).order_by('stage_order')

            inner_join_queryset = approvalProcedureStageQueryset.annotate(
                role=Subquery(activeOrgRoleQueryset.filter(role_id=OuterRef('role_id')).values('role')[:1]),
                # I don't like the fact that this subquery is repeated
                org_role_id=Subquery(
                    activeOrgRoleQueryset.filter(role_id=OuterRef('role_id')).values('org_role_id')[:1]),
                # but at the time of coding this I didn't have much choice
                org_name=Subquery(activeOrgRoleQueryset.filter(role_id=OuterRef('role_id')).values('org_name')[:1])
                # as returning more than 1 columns from a subquery cauzed errors
            ).order_by('stage_order')
            data = list(inner_join_queryset)[0]
            data['next'] = []

            if data["stage_type"] == "Junction":
                StatesGraph.branch += 1
            elif data["stage_type"] == "Merge":
                StatesGraph.branch -= 1

            ##### Additional Code #####
            next = NextStage.objects.filter(current_stage_id=data['stage_id']).values()
            next = list(next)
            if id not in visited:
                for n in next:
                    data['next'].append(get_stage(n["next_id"]))
            visited.append(id)
            return data

        stages = get_stage(id)
        return stages


class FileRetrieveView(View):
    def get(self, request, file_url):
        # Get the file extension from the URL
        file_extension = file_url.split('.')[-1].lower()
        file_name = 'sample'

        # You can add more supported formats if needed
        supported_formats = ['pdf', 'jpg', 'jpeg', 'png', 'gif']

        if file_extension in supported_formats:
            if file_url.startswith("https://storage.googleapis.com"):
                # If the file is in Google Cloud Storage
                # Initialize the GCS client
                storage_client = storage.Client(credentials=settings.GS_CREDENTIALS)

                # Extract the bucket and blob names from the URL
                bucket_name, blob_name = self.extract_bucket_and_blob_names(file_url)

                # Get the bucket
                bucket = storage_client.get_bucket(bucket_name)

                # Get the blob
                blob = bucket.blob(blob_name)

                file_name = blob_name

                # Get the blob's content
                file_content = blob.download_as_bytes()

            else:
                # If the file is not in Google Cloud Storage
                response = requests.get(file_url)
                file_content = response.content

            # return JsonResponse(response_data)
            response = HttpResponse(file_content,
                                    content_type=f'application/{file_extension}' if file_extension == 'pdf' else f'image/{file_extension}')
            response['Content-Disposition'] = f'attachment; filename="{file_name}.{file_extension}"'
            response['Access-Control-Expose-Headers'] = 'Content-Disposition'
            return response

        else:
            return Response("Unsupported file format.", status=400)

    @classmethod
    def extract_bucket_and_blob_names(self, file_url):
        # Extract the bucket and blob names from the URL
        parts = file_url.split('/')
        bucket_name = parts[3]
        blob_name = '/'.join(parts[4:])
        return bucket_name, blob_name


class FileAccessView(View):
    def get(self, request, file_url):
        # Check if the file URL is a GCS URL
        if file_url.startswith("https://storage.googleapis.com"):
            # Initialize the GCS client
            storage_client = storage.Client(credentials=settings.GS_CREDENTIALS)

            # Extract the bucket and blob names from the URL
            bucket_name, blob_name = FileRetrieveView.extract_bucket_and_blob_names(file_url)

            # Get the bucket
            bucket = storage_client.get_bucket(bucket_name)

            # Get the blob
            blob = bucket.blob(blob_name)

            # Generate a signed URL with an expiration time (e.g., 1 hour)
            expiration_time = timedelta(hours=1)
            signed_url = blob.generate_signed_url(
                expiration=expiration_time,
                method="GET"
            )

            # Redirect the user to the signed URL
            return HttpResponse(f'{signed_url}')

        # If it's not a GCS URL, return a 404 error
        return HttpResponseNotFound("File not found or could not be accessed.")


class DataHandlingDeviceList(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DataHandlingDevicePDFSerializer

    @method_decorator(ensure_csrf_cookie)
    def list(self, request, *args, **kwargs):
        request_id = self.request.query_params.get('request_id', None)
        if request_id is None:
            return Response({'message': 'Missing or invalid request_id parameter.'}, status=status.HTTP_400_BAD_REQUEST)

        devices_list = DataHandlingDevice.objects.filter(request_id=request_id, deleted_on__isnull=True)
        serialized_data = DataHandlingDevicePDFSerializer(devices_list, many=True)

        return Response(serialized_data.data, status=status.HTTP_200_OK)


class StaffSharedList(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ListOfStaffSerializer

    @method_decorator(ensure_csrf_cookie)
    def list(self, request, *args, **kwargs):
        request_id = self.request.query_params.get('request_id', None)
        if request_id is None:
            return Response({'message': 'Missing or invalid request_id parameter.'}, status=status.HTTP_400_BAD_REQUEST)

        staff_list = StaffShared.objects.filter(request_id=request_id, deleted_on__isnull=True)
        serialized_data = ListOfStaffSerializer(staff_list, many=True)

        return Response(serialized_data.data, status=status.HTTP_200_OK)


class StateCommentCreateView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = StateComment.objects.all()
    serializer_class = StateCommentSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class StateCommentListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = StateComment.objects.all()
    serializer_class = StateCommentSerializer


class StateCommentListByRequestView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = StateCommentGetSerializer

    def get_queryset(self):
        # Assuming you receive the data_request_id in the query parameters
        data_request_id = self.kwargs.get('data_request_id')

        queryset = StateComment.objects.filter(request_state__request=data_request_id).select_related('request_state')

        return queryset


class StateCommentListBySectionView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = StateCommentGetSerializer

    def post(self, request, *args, **kwargs):
        # Assuming you receive JSON data in the request body
        data_request_id = request.data.get('data_request_id', None)
        section = request.data.get('section', None)

        # Validate the received data
        if data_request_id is None or section is None:
            return Response({'error': 'data_request_id and section are required'}, status=status.HTTP_400_BAD_REQUEST)

        # Filter StateComment instances based on the provided data_request_id
        queryset = StateComment.objects.filter(request_state__request=data_request_id, section=section).select_related(
            'request_state')

        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)


class StateCommentAllSectionsListView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = StateCommentGetSerializer

    def get(self, request, *args, **kwargs):
        queryset = StateComment.objects.values_list('section', flat=True).distinct()
        return Response(queryset)


class StateCommentDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = StateComment.objects.all()
    serializer_class = StateCommentSerializer


class StateCommentUpdateView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = StateComment.objects.all()
    serializer_class = StateCommentSerializer
    lookup_field = 'comment_id'  # Add this line

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

            data = {"code": 200, "message": "Report updated successfully"}
            return JsonResponse(data, safe=False)

        except StateComment.DoesNotExist:
            data = {"code": 404, "message": "Failed to update report"}
            return JsonResponse(data, safe=False)


class StateCommentDestroyView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = StateComment.objects.all()
    serializer_class = StateCommentSerializer


class ReplyCreateView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Reply.objects.all()
    serializer_class = ReplySerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class ReplyListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Reply.objects.all()
    serializer_class = ReplySerializer


class ReplyListByStateCommentView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ReplyGetSerializer

    def get_queryset(self):
        comment_id = self.kwargs.get('comment_id')

        queryset = Reply.objects.filter(comment_id=comment_id)

        return queryset


class ReplyDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Reply.objects.all()
    serializer_class = ReplySerializer


class ReplyUpdateView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Reply.objects.all()
    serializer_class = ReplySerializer


class ReplyDestroyView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Reply.objects.all()
    serializer_class = ReplySerializer


class EquipmentTypeView(viewsets.ModelViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = EquipmentType.objects.all()
    serializer_class = EquipmentTypeSerializer


class IRBViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = IRB.objects.all()
    serializer_class = IRBSerializer


def convert_strings_to_original_data_types(data_request):
    data_request["submitted_on"] = format_date(data_request["submitted_on"])
    data_request["needed_on"] = format_date(data_request["needed_on"])
    for device in data_request["devices"]:
        device["usage_from"] = format_date(device["usage_from"])
        device["usage_to"] = format_date(device["usage_to"])
    for dataset in data_request["requested_datasets"]:
        dataset["date_created"] = format_date(dataset["date_created"])

    if data_request["filters"]:
        # data_request["filters"] = ast.literal_eval(data_request["filters"])
        data_request["filters"]["date_range_filter"]["start_value"] = format_date(
            data_request["filters"]["date_range_filter"]["start_value"])
        data_request["filters"]["date_range_filter"]["end_value"] = format_date(
            data_request["filters"]["date_range_filter"]["end_value"])
    return data_request


def format_date(date_str):
    if not date_str:
        return None
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        date_obj = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%fZ").date()
    return date_obj


def is_image(url):
    return any(url.endswith(ending) for ending in [".jpg", "JPG", "jpeg", "JPEG", "gif", "GIF", "png", "PNG"])


def get_image_html(image_contents):
    image = base64.b64encode(image_contents.content).decode('utf-8')
    html_contents = render_to_string("image.html", {'image': image})

    return html_contents


def combine_pdfs(request, data_request, request_pdf_data, stream):
    scheme = request.scheme
    domain = request.get_host()
    pdf_contents = [request_pdf_data]

    pdf_options = {
        'page-size': 'A4',
        'margin-top': '0mm',
        'margin-right': '0mm',
        'margin-bottom': '0mm',
        'margin-left': '0mm'
    }

    file_path = data_request["file_path"]
    if file_path:
        agreement = requests.get(f'{scheme}://{domain}{reverse("retrieve_file", kwargs={"file_url": file_path})}')
        if is_image(file_path):
            html_contents = get_image_html(agreement)
            pdf_contents.append(pdfkit.from_string(html_contents, False, options=pdf_options))
        else:
            pdf_contents.append(agreement.content)

    ethics_doc_path = data_request["ethics_doc_path"]
    if ethics_doc_path:
        ethics = requests.get(f'{scheme}://{domain}{reverse("retrieve_file", kwargs={"file_url": ethics_doc_path})}')
        if is_image(ethics_doc_path):
            html_contents = get_image_html(ethics)
            pdf_contents.append(pdfkit.from_string(html_contents, False, options=pdf_options))
        else:
            pdf_contents.append(ethics.content)

    additional_irb_file_path = data_request["additional_IRB_file_path"]
    if additional_irb_file_path:
        additional_irb = requests.get(
            f'{scheme}://{domain}{reverse("retrieve_file", kwargs={"file_url": additional_irb_file_path})}')
        if is_image(additional_irb_file_path):
            html_contents = get_image_html(additional_irb)
            pdf_contents.append(pdfkit.from_string(html_contents, False, options=pdf_options))
        else:
            pdf_contents.append(additional_irb.content)

    staff_shared = data_request["staff_shared"]
    if staff_shared:
        for staff in staff_shared:
            staff_doc = requests.get(
                f'{scheme}://{domain}{reverse("retrieve_file", kwargs={"file_url": staff["identification_file_path"]})}')
            if is_image(staff["identification_file_path"]):
                html_contents = get_image_html(staff_doc)
                pdf_contents.append(pdfkit.from_string(html_contents, False, options=pdf_options))
            else:
                pdf_contents.append(staff_doc.content)

    combined_writer = PdfWriter()

    for pdf in pdf_contents:
        pdf_reader = PdfReader(io.BytesIO(pdf))
        for page in pdf_reader.pages:
            # get A4 sizes
            current_width, current_height = page.mediabox.upper_right
            a4_width = 8.27 * 72
            a4_height = 11.69 * 72

            # maintain the page orientation when resizing
            if current_width > current_height:
                page.scale_to(a4_height, a4_width)
            else:
                page.scale_to(a4_width, a4_height)
            combined_writer.add_page(page)

    combined_writer.write(stream)


class DownloadRequestView(View):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, request_id):
        scheme = request.scheme
        domain = request.get_host()
        auth_token = request.META.get('HTTP_AUTHORIZATION')
        url = reverse('data-request')
        url_with_params = f'{scheme}://{domain}{url}?request_id={request_id}'

        devices_url = f'{scheme}://{domain}{reverse("data_handling_devices")}?request_id={request_id}'
        staff_url = f'{scheme}://{domain}{reverse("staff_shared")}?request_id={request_id}'
        dataset_url = f'{scheme}://{domain}{reverse("requested-datasets")}?request_id={request_id}'

        data_request = requests.get(url_with_params, headers={'Authorization': auth_token}).json()
        devices = requests.get(devices_url, headers={'Authorization': auth_token}).json()
        data_request["devices"] = devices
        staff_shared = requests.get(staff_url, headers={'Authorization': auth_token}).json()
        data_request["staff_shared"] = staff_shared
        requested_datasets = requests.get(dataset_url, headers={'Authorization': auth_token}).json()
        data_request["requested_datasets"] = requested_datasets

        data_request = convert_strings_to_original_data_types(data_request)
        data_request["tracking_id"] = "REQ" + str(data_request["request_id"]).zfill(6)

        html_contents = render_to_string("pdf_data_request.html", {'request': data_request})
        pdf_options = {
            'page-size': 'A4',
            'margin-top': '0mm',
            'margin-right': '0mm',
            'margin-bottom': '0mm',
            'margin-left': '0mm'
        }
        request_pdf_data = pdfkit.from_string(html_contents, False, options=pdf_options)
        # pdf_data = combine_pdfs(request, data_request, request_pdf_data)
        # response = HttpResponse(request_pdf_data, content_type='application/pdf')
        # response = HttpResponse(pdf_data, content_type='application/pdf')
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{data_request["title"]}.pdf"'
        response['Access-Control-Expose-Headers'] = 'Content-Disposition'
        combine_pdfs(request, data_request, request_pdf_data, response)
        return response


class RequestedDatasetPatchView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = RequestedDatasetPatchSerializer
    queryset = RequestedDataset.objects.all()

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        # Perform partial update
        self.partial_update(request, *args, **kwargs)

        comment = StateComment.objects.get(comment_id=request.data['comment_id'])
        comment.resolved = True
        comment.save()

        return Response("Requested Dataset has been patched successfully", status=status.HTTP_200_OK)


class DataRequestPatchView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DataRequestPatchSerializer
    queryset = DataRequest.objects.all()

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        self.partial_update(request, *args, **kwargs)

        comment = StateComment.objects.get(comment_id=request.data['comment_id'])
        comment.resolved = True
        comment.save()

        return Response("Data Request has been patched successfully", status=status.HTTP_200_OK)


class EthicsDocPatchPatchView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = EthicsPatchSerializer
    queryset = DataRequest.objects.all()

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        if 'ethics_doc_path' in request.data.keys():
            request.data['ethics_doc_path'] = self.handle_file_field(request.data['ethics_doc_path1'], instance,
                                                                     'ethics_doc_path1',
                                                                     'ethics_approval_letter')
        if 'file_path' in request.data.keys():
            request.data['file_path'] = self.handle_file_field(request.data['file_path1'], instance, 'file_path1',
                                                               'data_sharing_agreement')
        if 'additional_IRB_file_path' in request.data.keys():
            request.data['additional_IRB_file_path'] = self.handle_file_field(request.data['additional_IRB_file_path1'],
                                                                              instance,
                                                                              'additional_IRB_file_path1',
                                                                              'additional_IRB_file')

        # Call the superclass's update method to handle other fields
        self.partial_update(request, *args, **kwargs)

        comment = StateComment.objects.get(comment_id=request.data['comment_id'])
        comment.resolved = True
        comment.save()

        return Response("Data Request has been patched successfully", status=status.HTTP_200_OK)

    def handle_file_field(self, file_data, instance, field_name, cloud_storage_prefix):
        cloud_storage_path = None
        if file_data:
            file_mime = file_data.get('mime')
            uploaded_file = file_data.get('data')
            cloud_storage_path = self.get_serializer().upload_data_request_files(
                {'mime': file_mime, 'data': uploaded_file},
                cloud_storage_prefix,
                instance.request_id
            )
        return cloud_storage_path


class DatasetVariablePatchView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DatasetVariableSerializer
    queryset = DatasetVariable.objects.all()

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        for attr, value in validated_data.items():
            if value is not None and value != '':
                setattr(instance, attr, value)
        self.perform_update(serializer)

        comment = StateComment.objects.get(comment_id=request.data['comment_id'])
        comment.resolved = True
        comment.save()
        return Response(serializer.data)


class DataHandlingDevicesPatchView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DataHandlingDeviceSerializer
    queryset = DataHandlingDevice.objects.all()

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        for attr, value in validated_data.items():
            if value is not None and value != '':
                setattr(instance, attr, value)
        self.perform_update(serializer)

        # comment = StateComment.objects.get(comment_id=request.data['comment_id'])
        # comment.resolved = True
        # comment.save()

        return Response(serializer.data)


class StaffSharedPatchView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = StaffListSerializer  # Use StaffListSerializer for the patch view
    queryset = StaffShared.objects.all()

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        # Extract identification_file_path_data if provided
        identification_file_path_data = validated_data.pop('identification_file_path', None)
        request.data['identification_file_path'] = None

        # Call the superclass's update method to handle other fields
        self.partial_update(request, *args, **kwargs)

        # comment = StateComment.objects.get(comment_id=request.data['comment_id'])
        # comment.resolved = True
        # comment.save()

        # Update identification_file_path if provided
        if identification_file_path_data:
            instance = self.get_object()
            file_mime = identification_file_path_data.get('mime')
            uploaded_file = identification_file_path_data.get('data')
            cloud_storage_path = serializer.upload_file_to_cloud_storage(
                {'mime': file_mime, 'data': uploaded_file},
                'identification_file'
            )
            print(cloud_storage_path)
            instance.identification_file_path = cloud_storage_path
            instance.save()

        return Response("List of Staff patched successfully", status=status.HTTP_200_OK)


class DataHandlingDeviceDeleteView(generics.UpdateAPIView):
    queryset = DataHandlingDevice.objects.all()
    serializer_class = DataHandlingDeviceSerializer

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class StaffSharedDeleteView(generics.UpdateAPIView):
    queryset = StaffShared.objects.all()
    serializer_class = StaffSharedSerializer

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class DataHandlingDeviceCreateView(generics.CreateAPIView):
    queryset = DataHandlingDevice.objects.all()
    serializer_class = DataHandlingDeviceSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class StaffSharedCreateView(generics.CreateAPIView):
    queryset = StaffShared.objects.all()
    serializer_class = StaffListAddSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response("Staff successfully created!", status=status.HTTP_201_CREATED)
