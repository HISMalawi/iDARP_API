from main.utils.mail_sender import MailSender
from settings.models import Setting, UserSetting
from users.serializers import *
from rest_framework import generics
from users.models import User, Organization, OrgRole, Role, AssignedRole, TempOtp, AssignedRoleStatus, RoleStatus
from rest_framework import permissions
from rest_framework.authtoken.models import Token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from rest_framework.response import Response
from rest_framework import status, serializers
from email_validator import validate_email, EmailNotValidError
from rest_framework.exceptions import ValidationError
from django.contrib.auth import authenticate
import uuid
import logging
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q, Max, F
from users.backends.authenticate_email_or_phone import EmailOrPhoneModelBackend
from django.utils import timezone
import random
from .utils.otp_sms_sender import VonageSender, TwilioSender
from django.db import IntegrityError, transaction
from twilio.rest import Client
import ast

logger = logging.getLogger(__name__)


@method_decorator(ensure_csrf_cookie, name='dispatch')
class OrganizationList(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer


@method_decorator(ensure_csrf_cookie, name='dispatch')
class OrganizationRoles(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = OrgRoleSerializer

    def get_object(self):
        # Assuming the URL pattern includes the organization ID
        org_id = self.kwargs.get('pk')
        try:
            org = Organization.objects.get(org_id=org_id)
            org_roles = OrgRole.objects.filter(org=org)
            return org_roles
        except Organization.DoesNotExist:
            raise serializers.ValidationError(
                {'code': '404', 'message': 'Organization not found'})

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except serializers.ValidationError as e:
            return Response({'code': '404', 'message': 'Organization not found'}, status=status.HTTP_200_OK)


class UserList(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


@method_decorator(ensure_csrf_cookie, name='dispatch')
class RoleStatusListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = RoleStatus.objects.all()
    serializer_class = RoleStatusSerializer


class UserDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


@method_decorator(ensure_csrf_cookie, name='dispatch')
class AssignRoleView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AssignRoleSerializer
    queryset = AssignedRole.objects.all()

    def get_queryset(self):
        user_id = self.request.query_params.get('user_id')
        queryset = self.queryset.all()  # Use .all() instead of accessing .queryset directly

        if user_id:
            queryset = queryset.filter(user_id=user_id)

        return queryset

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serialized_data = self.get_serializer(queryset, many=True).data

        response_data = []
        for data in serialized_data:
            instance = AssignedRole.objects.get(
                assigned_role_id=data['assigned_role_id'])

            # Use OrgRoleSerializer to serialize org_role
            org_role_serializer = OrgRoleSerializer(instance.org_role)
            assigned_role_status = AssignedRoleStatus.objects.filter(
                assigned_role=instance)
            assigned_role_status_serializer = AssignedRoleStatusSerializer(
                assigned_role_status, many=True)

            data['org_role'] = org_role_serializer.data
            # Serialize assigned_role_status as an object
            data['assigned_role_status'] = assigned_role_status_serializer.data
            response_data.append(data)

        return Response(response_data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        org_role_id = request.data.get('org_role')
        user_id = request.data.get('user')

        try:
            org_role = OrgRole.objects.get(org_role_id=org_role_id)

        except OrgRole.DoesNotExist:
            return Response({'code': '400', 'message': 'Invalid org role ID.'}, status=status.HTTP_200_OK)

        try:
            user = User.objects.get(user_id=user_id)

        except User.DoesNotExist:
            return Response({'code': '400', 'message': 'Invalid user ID.'}, status=status.HTTP_200_OK)

        try:
            assigned_role = AssignedRole(org_role=org_role, user=user)
            assigned_role.save()

            assigned_role.process()

        except IntegrityError:
            return Response({'code': '400', 'message': 'User already has a Role.'}, status=status.HTTP_200_OK)

        org_role_serializer = OrgRoleSerializer(org_role)
        assigned_role_status_serializer = AssignedRoleStatusSerializer(
            [], many=True)

        response_data = {
            'assigned_role_id': assigned_role.assigned_role_id,
            'org_role': org_role_serializer.data,
            'org_role_id': org_role.org_role_id,
            'assigned_role_status': assigned_role_status_serializer.data,
            'user': user.user_id,
            'created_on': assigned_role.created_on,
            'assigned_by': assigned_role.assigned_by
        }

        return Response({'code': '201', 'message': 'Role request created successfully', 'request': response_data},
                        status=status.HTTP_201_CREATED)


@method_decorator(ensure_csrf_cookie, name='dispatch')
class AssignRoleApprovingView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AssignRoleSerializer
    queryset = AssignedRole.objects.all()

    def get_queryset(self):
        return self.queryset.all()

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        # org_role_id = self.request.query_params.get('org_role_id')

        role_status = self.request.query_params.get('role_status', [])

        if not role_status:
            return Response({'code': '400', 'message': 'Invalid input.'}, status=status.HTTP_200_OK)

        user = request.user
        role_status = ast.literal_eval(role_status)

        logged_user_roles = AssignedRole.objects.filter(
            user_id=user.user_id,
            assignedrolestatus__role_status__status__in=['Activated']
        ).values(
            'org_role_id__role_id',
        )

        is_authorized = False
        for role in logged_user_roles:
            if role['org_role_id__role_id'] in [1, 7]:
                is_authorized = True

        if not is_authorized:
            return Response({'code': '401', 'message': 'User not authorized.'}, status=status.HTTP_200_OK)

        # Fetching AssignedRoles that match the given criteria
        assigned_roles = AssignedRole.objects.all().filter(
            org_role__org_id=user.org_id,
            assignedrolestatus__role_status__status__in=role_status
        ).values()

        other_assigned_roles = assigned_roles.exclude(user_id=user.user_id)

        response_data = []
        for data in other_assigned_roles:
            instance = AssignedRole.objects.get(
                assigned_role_id=data['assigned_role_id']
            )

            # Use OrgRoleSerializer to serialize org_role
            org_role_serializer = OrgRoleSerializer(instance.org_role)
            assigned_role_status = AssignedRoleStatus.objects.filter(
                assigned_role=instance.assigned_role_id)
            assigned_role_status_serializer = AssignedRoleStatusSerializer(
                assigned_role_status, many=True)

            user_data = User.objects.filter(user_id=instance.user.user_id).values(
                'user_id',
                'fname',
                'sname',
                'middle_name',
                'designation',
                'org_email',
                'phone',
                'org_id',
                'org_id__name',
                'org_id__domain',
                'org_id__description',
                'org_id__active',
                'org_id__country',
            ).first()

            data['user'] = {

                'user_id': user_data['user_id'],
                'fname': user_data['fname'],
                'middle_name': user_data['middle_name'],
                'sname': user_data['sname'],
                'designation': user_data['designation'],
                'org_email': user_data['org_email'],
                'phone': user_data['phone'],
                'org': {
                    'org_id': user_data['org_id'],
                    'name': user_data['org_id__name'],
                    'domain': user_data['org_id__domain'],
                    'description': user_data['org_id__description'],
                    'active': user_data['org_id__active'],
                    'country': user_data['org_id__country'],
                }

            }

            data['org_role'] = org_role_serializer.data
            # Serialize assigned_role_status as an object
            data['assigned_role_status'] = assigned_role_status_serializer.data
            response_data.append(data)

        return Response(response_data, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        serializer = AssignRoleCustomSerializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)

        user = EmailOrPhoneModelBackend.authenticate(
            self, request, request.user.phone, serializer.validated_data['password'])

        if not user:
            return Response({'code': '401', 'message': 'Invalid password'}, status=status.HTTP_200_OK)

        logged_user_roles = AssignedRole.objects.filter(
            user_id=user.user_id,
            assignedrolestatus__role_status__status__in=['Activated']
        ).values(
            'org_role_id__role_id',
        )

        is_authorized = False
        for role in logged_user_roles:
            if role['org_role_id__role_id'] in [1, 7]:
                is_authorized = True

        if not is_authorized:
            return Response({'code': '401', 'message': 'User not authorized.'}, status=status.HTTP_200_OK)

        data = serializer.validated_data

        assigned_role_status = AssignedRoleStatus.objects.get(pk=data['assigned_role_status_id'])

        new_status = RoleStatus.objects.get(pk=data['role_status_id'])

        assigned_role_status.role_status = new_status

        assigned_role_status.save()

        return Response({'code': '200', 'message': 'Status updated successfully.'}, status=status.HTTP_200_OK)


# @method_decorator(ensure_csrf_cookie, name='dispatch')
class SignInView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = UserSignInSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():

            user = EmailOrPhoneModelBackend.authenticate(
                self, request, serializer.validated_data['username'], serializer.validated_data['password'])

            if user:
                # Check if the user is active
                if not user.is_active:
                    return Response({'code': '401', 'message': 'Your User Account has been revoked or suspended. '
                                                               'Contact your Organisation Admin or System '
                                                               'Administrator for assistance.'},
                                    status=status.HTTP_200_OK)

                assigned_roles = AssignedRole.objects.filter(
                    user=user.user_id)

                # Check if at least one assigned role is activated
                if assigned_roles.filter(assignedrolestatus__role_status__status='Activated').exists():
                    # At least one assigned role is activated, allow the login
                    pass
                else:
                    # None of the assigned roles are activated, return failure response
                    return Response({'code': '401',
                                     'message': 'At least one of your assigned roles must be activated. Contact your '
                                                'Organization Admin or System Administrator for assistance.'},
                                    status=status.HTTP_200_OK)

                try:
                    assigned_roles = AssignedRole.objects.filter(
                        user=user.user_id)
                    org_role_ids = assigned_roles.values_list(
                        'org_role', flat=True)

                except AssignedRole.DoesNotExist:
                    org_role_ids = None

                if org_role_ids is not None:
                    try:
                        role_d = OrgRole.objects.filter(
                            Q(org_role_id__in=org_role_ids)).values()

                    except OrgRole.DoesNotExist:
                        pass

                roles = None
                if role_d is not None:
                    try:
                        roles = Role.objects.filter(Q(role_id__in=role_d.values('role'))).values(
                            'role_id', 'role', 'rank')
                    except Role.DoesNotExist:
                        pass

                query = User.objects.filter(user_id=user.user_id).annotate(
                    latest_status=Max(
                        'assignedrole__assignedrolestatus__state_changed_on'),
                    assigned_role_id=F('assignedrole__assigned_role_id'),
                    role=F('assignedrole__org_role__role__role'),
                    user_id_alias=F('user_id'),
                    fname_alias=F('fname'),
                    sname_alias=F('sname'),
                    organization=F('assignedrole__org_role__org__name'),
                    role_status_id=F(
                        'assignedrole__assignedrolestatus__role_status__role_status_id'),
                    status=F(
                        'assignedrole__assignedrolestatus__role_status__status')
                ).filter(
                    Q(assignedrole__assignedrolestatus__state_changed_on=F('latest_status')) |
                    Q(assignedrole__assignedrolestatus__state_changed_on__isnull=True)
                ).values(
                    'role',
                    'role_status_id',
                    'status',
                ).distinct()

                for role in roles:
                    role['latest_role_status'] = [
                        {key: value for key, value in status.items() if key !=
                         'role'}
                        for status in query
                        if status['role'] == role['role'] and status['role_status_id'] == 2
                    ]

                    try:
                        # Add assigned_role_id to the role
                        role['assigned_role_id'] = assigned_roles.get(
                            org_role__role__role_id=role['role_id'],
                            assignedrolestatus__role_status__role_status_id=2).assigned_role_id
                    except AssignedRole.DoesNotExist:
                        role['assigned_role_id'] = None

                if role_d is not None:
                    for r in role_d.values():
                        for role in roles:
                            if role['role_id'] == r['role_id']:
                                role['org_role_id'] = r['org_role_id']

                token, created = Token.objects.get_or_create(user=user)

                user_json = {'user_id': user.user_id,
                             'fname': user.fname,
                             'middle_name': user.middle_name,
                             'sname': user.sname,
                             'org_email': user.org_email,
                             'phone': user.phone,
                             'designation': user.designation,
                             'department': user.department,
                             'is_active': user.is_active,
                             'is_staff': user.is_staff,
                             'is_superuser': user.is_superuser,
                             'tentative_organization': user.tentative_organization,
                             'assigned_roles': roles,
                             'org': {
                                 'org_id': user.org.org_id,
                                 'name': user.org.name,
                                 'domain': user.org.domain,
                                 'description': user.org.description,
                                 'active': user.org.active,
                                 'country': user.org.country,
                             },
                             'token': token.key,
                             }
                return Response({'code': '200', 'message': 'Login Successful', 'user': user_json},
                                status=status.HTTP_200_OK)

        else:
            return Response({'code': '401', 'message': 'Invalid username or password'}, status=status.HTTP_200_OK)


class GetUpdatedUserDetails(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    @method_decorator(ensure_csrf_cookie)
    def get(self, request, *args, **kwargs):
        user_id = request.query_params.get('user_id')
        try:
            user = User.objects.get(user_id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            assigned_roles = AssignedRole.objects.filter(user=user_id)
            org_role_ids = assigned_roles.values_list('org_role', flat=True)
            role_d = OrgRole.objects.filter(Q(org_role_id__in=org_role_ids)).values()

            roles = Role.objects.filter(Q(role_id__in=role_d.values('role'))).values(
                'role_id', 'role', 'rank'
            )

            query = User.objects.filter(user_id=user_id).annotate(
                latest_status=Max('assignedrole__assignedrolestatus__state_changed_on'),
                assigned_role_id=F('assignedrole__assigned_role_id'),
                role=F('assignedrole__org_role__role__role'),
                user_id_alias=F('user_id'),
                fname_alias=F('fname'),
                sname_alias=F('sname'),
                organization=F('assignedrole__org_role__org__name'),
                role_status_id=F('assignedrole__assignedrolestatus__role_status'),
                status=F('assignedrole__assignedrolestatus__role_status__status')
            ).filter(
                Q(assignedrole__assignedrolestatus__state_changed_on=F('latest_status')) |
                Q(assignedrole__assignedrolestatus__state_changed_on__isnull=True)
            ).values(
                'role',
                'role_status_id',
                'status'
            ).distinct()

            roles_data = []
            for role in roles:
                try:
                    # Add assigned_role_id to the role
                    assigned_role_id = assigned_roles.get(
                        org_role__role__role_id=role['role_id'],
                        assignedrolestatus__role_status__role_status_id=2).assigned_role_id
                except AssignedRole.DoesNotExist:
                    assigned_role_id = None
                role_data = {
                    'role_id': role['role_id'],
                    'role': role['role'],
                    'rank': role['rank'],
                    'latest_role_status': [
                        {key: value for key, value in status.items() if key != 'role'}
                        for status in query
                        if status['role'] == role['role']
                    ],
                    'assigned_role_id': assigned_role_id
                }
                roles_data.append(role_data)

            for r in role_d.values():
                for role_data in roles_data:
                    if role_data['role_id'] == r['role_id']:
                        role_data['org_role_id'] = r['org_role_id']

            user_json = {
                'user_id': user_id,
                'fname': user.fname,
                'middle_name': user.middle_name,
                'sname': user.sname,
                'org_email': user.org_email,
                'phone': user.phone,
                'designation': user.designation,
                'department': user.department,
                'is_active': user.is_active,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
                'tentative_organization': user.tentative_organization,
                'assigned_roles': roles_data,
                'org': {
                    'org_id': user.org.org_id,
                    'name': user.org.name,
                    'domain': user.org.domain,
                    'description': user.org.description,
                    'active': user.org.active,
                    'country': user.org.country,
                }
            }
            return Response(user_json, status=status.HTTP_200_OK)

        except AssignedRole.DoesNotExist:
            return Response({'error': 'Assigned roles not found'}, status=status.HTTP_404_NOT_FOUND)

        except OrgRole.DoesNotExist:
            return Response({'error': 'Org roles not found'}, status=status.HTTP_404_NOT_FOUND)

        except Role.DoesNotExist:
            return Response({'error': 'Roles not found'}, status=status.HTTP_404_NOT_FOUND)


@method_decorator(ensure_csrf_cookie, name='dispatch')
class ForgotPasswordView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = OTPVerificationSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)  # data: ['username', 'otp', 'password']

        try:
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError as e:
            return Response({'error': e.detail}, status=e.status_code)

        validated_data = serializer.validated_data

        try:
            # Check if the phone number or email already exists
            if '@' in validated_data['username']:
                user = User.objects.filter(org_email=validated_data['username']).first()
            else:
                user = User.objects.filter(phone=validated_data['username']).first()
        except User.DoesNotExist:
            return Response({'error': 'User with this phone number or email does not exist'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Update Password
        user.update_password(request.data['password'])

        return Response({'code': '200', 'message': 'Password Updated Successfully'},
                        status=status.HTTP_200_OK)


@method_decorator(ensure_csrf_cookie, name='dispatch')
class VerifyOTP(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OTPVerificationSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)  # data: ['username', 'otp']

        try:
            serializer.is_valid(raise_exception=True)
            return Response({'message': 'OTP Verified'}, status=status.HTTP_200_OK)
        except serializers.ValidationError as e:
            return Response({'error': e.detail}, status=e.status_code)


def assign_default_settings(user):
    all_settings = Setting.objects.all()

    user_settings = [
        UserSetting(user=user, setting=setting, setting_value=setting.default_value) for setting in all_settings
    ]

    UserSetting.objects.bulk_create(user_settings)


@method_decorator(ensure_csrf_cookie, name='dispatch')
class SignUpOtpVerificationView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = UserSignUpOTPVerificationSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError as e:
            if 'non_field_errors' in e.detail:
                # Handle the specific error for username
                error_message = e.detail['non_field_errors'][0]
                return Response({'code': '605', 'message': 'OTP does not exist', 'errors': e.detail},
                                status=status.HTTP_200_OK)
            else:
                return Response({'code': '401', 'message': 'Invalid input', 'errors': e.detail},
                                status=status.HTTP_200_OK)

        validated_data = serializer.validated_data
        user_serializer = UserSerializer(data=validated_data)
        try:
            user_serializer.is_valid(raise_exception=True)
            user_serializer.save()

        except serializers.ValidationError as e:

            return Response({'code': '401', 'message': 'Invalid input', 'errors': e.detail},
                            status=status.HTTP_200_OK)

        user = EmailOrPhoneModelBackend.authenticate(
            self, request, validated_data['username'], validated_data['password'])

        if user:

            with transaction.atomic():

                # Assign Default Settings
                assign_default_settings(user)

                # Assign default requester role
                org_role = OrgRole.objects.select_related('role', 'org').get(
                    role__role_id=2,
                    org_id=user.org_id
                )

                requester_role = AssignedRole.objects.create(
                    org_role_id=org_role.pk,
                    user_id=user.user_id,
                    created_on=timezone.now(),
                    assigned_by="Default",
                )

                requester_role.save()

                assigned_role_status = AssignedRoleStatus.objects.create(
                    assigned_role_id=requester_role.pk,
                    role_status_id=2,
                    state_changed_on=timezone.now()
                )

                assigned_role_status.save()

                try:
                    assigned_roles = AssignedRole.objects.filter(
                        user=user.user_id)
                    org_role_ids = assigned_roles.values_list(
                        'org_role', flat=True)
                except AssignedRole.DoesNotExist:
                    org_role_ids = None

                if org_role_ids is not None:
                    try:
                        role_ids = OrgRole.objects.filter(
                            Q(org_role_id__in=org_role_ids)).values()
                    except OrgRole.DoesNotExist:
                        pass

                roles = None
                if role_ids is not None:
                    try:
                        roles = Role.objects.filter(Q(role_id__in=role_ids.values('role'))).values(
                            'role_id', 'role', 'rank')
                    except Role.DoesNotExist:
                        pass

                query = User.objects.filter(user_id=user.user_id).annotate(
                    latest_status=Max(
                        'assignedrole__assignedrolestatus__state_changed_on'),
                    assigned_role_id=F('assignedrole__assigned_role_id'),
                    role=F('assignedrole__org_role__role__role'),
                    user_id_alias=F('user_id'),
                    fname_alias=F('fname'),
                    sname_alias=F('sname'),
                    organization=F('assignedrole__org_role__org__name'),
                    role_status_id=F(
                        'assignedrole__assignedrolestatus__role_status'),
                    status=F(
                        'assignedrole__assignedrolestatus__role_status__status')
                ).filter(
                    Q(assignedrole__assignedrolestatus__state_changed_on=F('latest_status')) |
                    Q(assignedrole__assignedrolestatus__state_changed_on__isnull=True)
                ).values(
                    'role',
                    'role_status_id',
                    'status',
                ).distinct()

                for role in roles:
                    role['latest_role_status'] = [
                        {key: value for key, value in status.items() if key !=
                         'role'}
                        for status in query
                        if status['role'] == role['role']
                    ]

                    try:
                        # Add assigned_role_id to the role
                        role['assigned_role_id'] = assigned_roles.get(
                            org_role__role__role_id=role['role_id'],
                            assignedrolestatus__role_status__role_status_id=2).assigned_role_id
                    except AssignedRole.DoesNotExist:
                        role['assigned_role_id'] = None

                if role_ids is not None:
                    for r in role_ids.values():
                        for role in roles:
                            if role['role_id'] == r['role_id']:
                                role['org_role_id'] = r['org_role_id']

                token, created = Token.objects.get_or_create(user=user)

                user_json = {'user_id': user.user_id,
                             'fname': user.fname,
                             'middle_name': user.middle_name,
                             'sname': user.sname,
                             'org_email': user.org_email,
                             'phone': user.phone,
                             'designation': user.designation,
                             'department': user.department,
                             'is_active': user.is_active,
                             'is_staff': user.is_staff,
                             'is_superuser': user.is_superuser,
                             'tentative_organization': user.tentative_organization,
                             'assigned_roles': roles,
                             'org': {
                                 'org_id': user.org.org_id,
                                 'name': user.org.name,
                                 'domain': user.org.domain,
                                 'description': user.org.description,
                                 'active': user.org.active,
                                 'country': user.org.country,
                             },
                             'token': token.key,
                             }
                return Response({'code': '200', 'message': 'Verification Successful', 'user': user_json},
                                status=status.HTTP_200_OK)

        else:
            return Response({'code': '401', 'message': 'Invalid operation'}, status=status.HTTP_200_OK)


@method_decorator(ensure_csrf_cookie, name='dispatch')
class SignUpOtpView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = UserSignUpOTPSerializer

    def post(self, request):
        # Check if the phone number or email already exists
        if '@' in request.data.get('username'):
            existing_user = User.objects.filter(org_email=request.data.get('username')).first()
            if existing_user:
                return Response({'code': '601', 'message': 'Email already exists'},
                                status=status.HTTP_200_OK)
        else:
            existing_user = User.objects.filter(phone=request.data.get('username')).first()
            if existing_user:
                return Response({'code': '601', 'message': 'Phone already exists'},
                                status=status.HTTP_200_OK)

        otp_code = self.generate_otp()

        # Get the current time
        current_time = timezone.now()

        serializer = self.serializer_class(data=request.data, context={
            'otp': otp_code, 'created_on': current_time, })

        try:
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError as e:
            if 'username' in e.detail:
                # Handle the specific error for username
                error_message = e.detail['username'][0]
                return Response({'code': '601', 'message': 'Username already exists', 'errors': error_message},
                                status=status.HTTP_200_OK)
            # Handle any other validation error
            return Response({'code': '401', 'message': 'Bad request', 'errors': e.detail}, status=status.HTTP_200_OK)

        with transaction.atomic():
            instance = serializer.save()

            res = OtpResendView.send_otp(instance, instance.username)

            if res:
                return Response({'code': '200', 'message': 'OTP sent successfully', 'data': current_time},
                                status=status.HTTP_200_OK)
            else:
                transaction.set_rollback(True)
                return Response({'code': '606', 'message': 'OTP sending failed.'}, status=status.HTTP_200_OK)

    @classmethod
    def generate_otp(cls):
        otp = ""
        for _ in range(6):
            otp += str(random.randint(0, 9))
        return otp


@method_decorator(ensure_csrf_cookie, name='dispatch')
class OtpResendView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = UserOTPResendSerializer

    def post(self, request):
        otp = SignUpOtpView.generate_otp()
        current_time = timezone.now()

        serializer = self.serializer_class(
            data=request.data, context={'request': request})

        try:
            serializer.is_valid(raise_exception=True)
            username = serializer.validated_data['username']

            # Save the new TempOtp object with the generated OTP and current time
            with transaction.atomic():
                instance = TempOtp.objects.create(
                    username=username, otp=otp, created_on=current_time)

                response = self.send_otp(instance, username)

                if response:
                    return Response({'code': '200', 'message': 'OTP sent successfully', 'data': current_time},
                                    status=status.HTTP_200_OK)
                else:
                    transaction.set_rollback(True)
                    return Response({'code': '606', 'message': 'OTP sending failed.'}, status=status.HTTP_200_OK)

        except serializers.ValidationError as e:
            return Response({'code': '401', 'message': 'Bad request', 'errors': e.detail},
                            status=status.HTTP_400_BAD_REQUEST)

    @classmethod
    def send_otp(cls, instance, username):
        if '@' in username:
            mail_otp = MailSender()
            response = mail_otp.send_otp('OTP Verification', instance.otp, [username])
        else:
            sms_otp = TwilioSender()
            response = sms_otp.send_otp(instance.username, instance.otp)
        return response


@method_decorator(ensure_csrf_cookie, name='dispatch')
class Track(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = UserAuditTrailSerializer

    def post(self, request, format=None):

        # logger.debug('Request headers: %s', request.META)

        user_agent = request.META.get('HTTP_USER_AGENT', '')
        referer = request.META.get('HTTP_REFERER', '')
        script_name = request.META.get('SCRIPT_NAME', '')

        # Get the request data
        data = request.data

        # Loop through the data and concatenate referer with each object
        for obj in data:
            obj['referer'] = referer + obj['page']

        serializer = self.serializer_class(data=request.data, many=True, context={
            'user_agent': user_agent, 'script_name': script_name, })

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(ensure_csrf_cookie, name='dispatch')
class GenerateUUID(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        new_uuid = uuid.uuid4()

        return Response({'uuid': str(new_uuid)}, status=status.HTTP_200_OK)


class TestView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = OrgRoleStatusSerializer
    queryset = OrgRoleStatus.objects.all()

    def get(self, request, *args, **kwargs):
        queryset = OrgRoleStatus.objects.select_related('org_role').values(
            'org_role_id',
            'status',
            'changed_on',
        ).annotate(
            role=F('org_role__role__role'),
            role_id=F('org_role__role__role_id'),
            org_id=F('org_role__org_id'),
            org_name=F('org_role__org__name')
        )
        print(queryset)
        data = list(queryset)
        # response = JsonResponse(data, safe=False)
        return Response({'code': '200', 'message': 'Verification Successful', 'user': data},
                        status=status.HTTP_200_OK)


@method_decorator(ensure_csrf_cookie, name='dispatch')
class OrganizationUserList(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get_queryset(self):
        org_id = self.request.query_params.get('org_id')

        if org_id:
            return User.objects.filter(org_id=org_id).exclude(user_id=self.request.user.user_id)

        user_list = User.objects.all().exclude(user_id=self.request.user.id)

        return Response({'code': '200', 'message': 'Retrieved all users successfully', 'user': user_list},
                        status=status.HTTP_200_OK)


@method_decorator(ensure_csrf_cookie, name='dispatch')
class UserActivationView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = User.objects.all()
    serializer_class = UserActivationSerializer

    def patch(self, request, *args, **kwargs):
        user_id = kwargs.get('pk')
        try:
            user = self.queryset.get(user_id=user_id)
        except User.DoesNotExist:
            return Response({'code': '404', 'message': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(user, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({'code': '200', 'message': 'User updated successfully', 'user': serializer.data},
                            status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(ensure_csrf_cookie, name='dispatch')
class CheckPhoneNumber(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = CheckPhoneNumberSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data['phone']

        account_sid = settings.TWILIO_SID
        auth_token = settings.TWILIO_AUTH_TOKEN

        client = Client(account_sid, auth_token)

        try:
            response = client.lookups.phone_numbers(phone).fetch()
            result_message = f'Phone number {phone} exists and is active. {response}'
            state = True
        except Exception as e:
            result_message = f'Phone number {phone} does not exist or is not active. Error: {str(e)}'
            state = False

        return Response({'result_message': result_message, 'state': state})


@method_decorator(ensure_csrf_cookie, name='dispatch')
class IsADuplicatePhoneNumber(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = CheckPhoneNumberSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data['phone']

        # Check if the phone number already exists
        existing_user = User.objects.filter(phone=phone).first()
        if existing_user:
            return Response({'code': '601', 'result_message': 'Phone already exists', 'state': True},
                            status=status.HTTP_200_OK)

        else:
            return Response({'code': '200', 'result_message': 'Phone is not registered', 'state': False},
                            status=status.HTTP_200_OK)


@method_decorator(ensure_csrf_cookie, name='dispatch')
class IsADuplicateEmailAddress(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = EmailVerificationSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        org_email = serializer.validated_data['org_email']

        # Check if the email already exists
        existing_user = User.objects.filter(org_email=org_email).first()
        if existing_user:
            return Response({'code': '601', 'result_message': 'Email already registered', 'state': True},
                            status=status.HTTP_200_OK)

        else:
            return Response({'code': '200', 'result_message': 'Email is not registered', 'state': False},
                            status=status.HTTP_200_OK)


@method_decorator(ensure_csrf_cookie, name='dispatch')
class ValidateEmailView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = EmailVerificationSerializer

    def post(self, request):
        print(request.data)  # Add this line for debugging
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['org_email']

        try:
            # Validate the email address using the email-validator library
            is_valid = validate_email(email, check_deliverability=True, globally_deliverable=True).email
            return JsonResponse({'valid': is_valid, 'message': 'Email is valid.'}, status=200)
        except EmailNotValidError as e:
            # The email is not valid
            return JsonResponse({'valid': False, 'message': str(e)}, status=400)


@method_decorator(ensure_csrf_cookie, name='dispatch')
class UpdateUserEmailView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = EmailSerializer

    def get_object(self):
        return self.request.user  # Retrieve the authenticated user

    def patch(self, request, *args, **kwargs):
        user = self.get_object()

        serializer = EmailSerializer(instance=user, data=request.data, partial=True)
        if serializer.is_valid():
            # Update org_email and email_is_verified fields
            user.org_email = serializer.validated_data.get('org_email', user.org_email)
            user.email_is_verified = serializer.validated_data.get('email_is_verified', user.email_is_verified)

            # Save the changes
            user.save()

            return Response({'message': 'User email information updated successfully.'}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(ensure_csrf_cookie, name='dispatch')
class UpdateUserPhoneView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PhoneNumberSerializer

    def get_object(self):
        return self.request.user  # Retrieve the authenticated user

    def partial_update(self, request, *args, **kwargs):
        user = self.get_object()

        serializer = PhoneNumberSerializer(instance=user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        # Update phone field
        user.phone = serializer.validated_data.get('phone', user.phone)

        # Save the changes
        user.save()

        return Response({'message': 'User phone number information updated successfully.'}, status=status.HTTP_200_OK)


@method_decorator(ensure_csrf_cookie, name='dispatch')
class SendOTPBasedOnSettingAppView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserOTPResendSerializer

    def get_object(self):
        return self.request.user  # Retrieve the authenticated user

    def post(self, request, *args, **kwargs):
        user = self.get_object()

        # Check if the user has the setting for OTP delivery channel set
        delivery_channel = UserSetting.objects.filter(user=user, setting__setting='OTP Delivery Channel').first()
        otp = SignUpOtpView.generate_otp()
        current_time = timezone.now()

        if delivery_channel:
            if delivery_channel.setting_value.lower() == 'email' and user.org_email:
                # Save the new TempOtp object with the generated OTP and current time
                with transaction.atomic():
                    instance = TempOtp.objects.create(
                        username=user.org_email, otp=otp, created_on=current_time)
                    OtpResendView.send_otp(instance, user.org_email)
                return Response({'message': 'OTP sent via email.', 'time': current_time}, status=status.HTTP_200_OK)
            elif delivery_channel.setting_value.lower() == 'phone' or user.phone:
                # Save the new TempOtp object with the generated OTP and current time
                with transaction.atomic():
                    instance = TempOtp.objects.create(
                        username=user.phone, otp=otp, created_on=current_time)
                    OtpResendView.send_otp(instance, user.phone)
                return Response({'message': 'OTP sent via SMS.', 'time': current_time}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'OTP delivery channel is not set.'}, status=status.HTTP_400_BAD_REQUEST)


class UserProfileUpdateView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = User.objects.all()
    serializer_class = UserProfileUpdateSerializer

    def put(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AssignedRoleStatusListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AssignedRoleStatusAdminSerializer

    def get_queryset(self):
        org_id = self.request.GET.get('org_id')  # Assuming you're passing org_id as a query parameter
        assigned_roles = AssignedRole.objects.filter(user__org_id=org_id)
        return AssignedRoleStatus.objects.filter(assigned_role__in=assigned_roles)


class AssignedRoleStatusPatchView(generics.UpdateAPIView):
    queryset = AssignedRoleStatus.objects.all()
    serializer_class = AssignedRoleStatusPatchSerializer
    partial = True  # Allow partial updates
