import base64
import random
from django.db.models import Q

from data_requests.utils.pad_with_zeros import PadZeros
from main import settings
from google.cloud import storage
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework import serializers
from data_requests.models import *
from users.models import TempOtp
from data_dictionary.serializers import DataSourceSerializer
import logging
from django.utils import timezone
from datetime import timedelta, datetime

from users.serializers import AssignRoleGetSerializer

logger = logging.getLogger(__name__)


class FileObjectSerializer(serializers.Serializer):
    mime = serializers.CharField()
    data = serializers.CharField()


class DataRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataRequest
        fields = [
            'request_id',
            'requester',
            'date_created',
            'file_path',
            'title',
            'department',
            'needed_on',
            'protocol_ref_num',
            'ethics_doc_path',
            'ethics_approval_letter',
            'submitted',
            'submitted_on',
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
            'additional_ethics_committee_name',
            'additional_IRB_file_path',
            'ethics_committee'
        ]
        read_only_fields = ['request_id', 'date_created', ]

    def create(self, validated_data):
        for key, value in self.context.items():
            validated_data[key] = self.context.get(key, '')

        return super().create(validated_data)

    def get_department(self, obj):
        return obj.department


class RequestStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequestState
        fields = '__all__'


class NextStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NextState
        fields = '__all__'


class RequestStateWithNextStateSerializer(serializers.ModelSerializer):
    next_state = NextStateSerializer(many=True, read_only=True)

    class Meta:
        model = RequestState
        fields = '__all__'


class RequestStateUpdateSerializer(serializers.Serializer):
    state_id = serializers.IntegerField(required=False, allow_null=True)
    request = serializers.IntegerField()
    org_role = serializers.IntegerField()
    assigned_role = serializers.IntegerField()
    status = serializers.BooleanField()
    reason = serializers.CharField()
    otp = serializers.CharField()

    def validate(self, attrs):

        # Access the logged-in user
        user = self.context['request'].user

        state_id = attrs.get('state_id')
        request = attrs.get('request')
        org_role = attrs.get('org_role')
        assigned_role = attrs.get('assigned_role')
        otp = attrs.get('otp')

        if not RequestState.objects.filter(pk=state_id, ).exists():
            raise serializers.ValidationError('Request state does not exist.')

        if not DataRequest.objects.filter(pk=request, ).exists():
            raise serializers.ValidationError('Data Request does not exist.')

        if not OrgRole.objects.filter(pk=org_role, ).exists():
            raise serializers.ValidationError(
                'Organization Role does not exist.')

        if not AssignedRole.objects.filter(pk=assigned_role, ).exists():
            raise serializers.ValidationError('Assigned Role does not exist.')

        # Authenticate using phone number
        try:
            temp_otp = TempOtp.objects.filter(otp=otp).filter(
                Q(username=user.phone) | Q(username=user.org_email)).order_by('-created_on').first()

            if temp_otp is None:
                raise serializers.ValidationError('OTP does not exist')

            if temp_otp.created_on is not None:
                record_timestamp = temp_otp.created_on

                # Get the current time
                current_time = timezone.now()

                # Calculate the time difference between the current time and the record timestamp
                time_difference = current_time - record_timestamp

                # Check if the time difference is within the desired range (5 minutes)
                if time_difference > timedelta(minutes=5):
                    raise serializers.ValidationError("OTP Expired")

        except TempOtp.DoesNotExist:
            raise serializers.ValidationError('OTP does not exist')

        return attrs

    def update(self, instance, validated_data):

        assigned_role = AssignedRole.objects.get(
            pk=validated_data['assigned_role'])

        instance.status = validated_data['status']
        instance.reason = validated_data['reason']
        instance.responded_on = timezone.now()
        instance.attended_by = assigned_role
        instance.save()
        return instance


class DatasetPresetSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatasetPreset
        fields = [
            'preset',
            'rdataset',
        ]


class PurposeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Purpose
        fields = [
            'purpose_id',
            'purpose',
        ]


class RequestPurposeSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequestPurpose
        fields = [
            'request_purpose_id',
            'request',
            'purpose',
            'purpose_description',
        ]


class PostRequestPurposeSerializer(serializers.Serializer):
    purpose = serializers.IntegerField()
    purpose_description = serializers.CharField(required=False, allow_null=True)


class RequestedDatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequestedDataset
        fields = '__all__'


class DatasetVariableSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatasetVariable
        fields = [
            'dataset_variable_id',
            'rdataset',
            'var',
            'is_distinct',
            'date_added'
        ]
        depth = 1


class DatasetVariableCustomSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatasetVariable
        fields = [
            'dataset_variable_id',
            'rdataset',
            'var',
            'is_distinct',
            'date_added'
        ]


class CustomRequestedDatasetSerializer(serializers.ModelSerializer):
    dataset_variables = DatasetVariableSerializer(many=True, read_only=True)
    data_source = DataSourceSerializer()

    class Meta:
        model = RequestedDataset
        fields = [
            'rdataset_id',
            'request',
            'dataset_description',
            'data_source',
            'date_created',
            'release_date',
            'data_specs_path',
            'dataset_variables',
            'filters'
        ]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['dataset_variables'] = DatasetVariableSerializer(
            instance.dataset_variables.all(), many=True).data
        return representation


class PostRequestedDatasetSerializer(serializers.ModelSerializer):
    dataset_variables = DatasetVariableSerializer(many=True, read_only=True)

    # data_source = DataSourceSerializer()

    class Meta:
        model = RequestedDataset
        fields = [
            'rdataset_id',
            'request',
            'dataset_description',
            'data_source',
            'date_created',
            'release_date',
            'data_specs_path',
            'dataset_variables'
        ]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['dataset_variables'] = DatasetVariableSerializer(
            instance.dataset_variables.all(), many=True).data
        return representation


class DataRequestBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataRequest
        fields = [
            'request_id',
            'requester',
            'date_created',
            'title',
            'department',
            'needed_on',
            'protocol_ref_num',
            'ethics_doc_path',
            'ethics_approval_letter',
            'submitted',
            'exempted',
            'submitted_on',
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
            'additional_ethics_committee_name',
            'additional_IRB_file_path',
            'ethics_committee'
        ]
        read_only_fields = ['request_id', 'date_created', ]

    def create(self, validated_data):
        for key, value in self.context.items():
            validated_data[key] = self.context.get(key, '')

        return super().create(validated_data)


class StageSerializer(serializers.Serializer):
    class Meta:
        model = Stage
        fields = '__all__'


class EquipmentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentType
        fields = '__all__'


class IRBSerializer(serializers.ModelSerializer):
    class Meta:
        model = IRB
        fields = '__all__'


class DataHandlingDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataHandlingDevice
        fields = '__all__'


class DataHandlingDevicePDFSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataHandlingDevice
        fields = [
            'device_id',
            'equipment_type',
            'serial_number',
            'used_by',
            'organisation',
            'usage_from',
            'usage_to',
            'equipment_name',
            'deleted_on'
        ]
        depth = 1


class StaffSharedSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffShared
        fields = '__all__'

        def update(self, instance, validated_data):
            # Handle special case for identification_file_path
            if 'identification_file_path' in validated_data:
                identification_file_path_data = validated_data.pop('identification_file_path', None)
                if identification_file_path_data:
                    file_mime = identification_file_path_data.get('mime')
                    uploaded_file = identification_file_path_data.get('data')

                    # Upload file to cloud storage
                    cloud_storage_path = StaffListSerializer.upload_file_to_cloud_storage(
                        {'mime': file_mime, 'data': uploaded_file},
                        'identification_file'
                    )
                    instance.identification_file_path = cloud_storage_path

            # Call the superclass's update method
            return super().update(instance, validated_data)


class ListOfDeviceSerializer(serializers.Serializer):
    equipment_name = serializers.CharField()
    serial_number = serializers.CharField()
    used_by = serializers.CharField()
    organisation = serializers.CharField()
    usage_from = serializers.DateField()
    usage_to = serializers.DateField()
    equipment_type = serializers.IntegerField()


class ListOfStaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffShared
        fields = '__all__'


class StateCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = StateComment
        fields = '__all__'


class ReplySerializer(serializers.ModelSerializer):
    class Meta:
        model = Reply
        fields = '__all__'


class ReplyGetSerializer(serializers.ModelSerializer):
    author = AssignRoleGetSerializer()

    class Meta:
        model = Reply
        fields = ['reply_id', 'comment', 'reply', 'responded_on', 'author']


class StateCommentGetSerializer(serializers.ModelSerializer):
    author = AssignRoleGetSerializer()

    class Meta:
        model = StateComment
        fields = '__all__'


class StaffListSerializer(serializers.Serializer):
    staff_shared_id = serializers.IntegerField(read_only=True)
    first_name = serializers.CharField(max_length=255)
    surname = serializers.CharField(max_length=255)
    phone = serializers.CharField(max_length=20)
    email = serializers.EmailField()
    identification_type = serializers.CharField(max_length=255)
    identification_number = serializers.CharField(max_length=255)
    position_in_organisation = serializers.CharField(max_length=255)
    confidentiality_protocols = serializers.BooleanField()
    identification_file_path = FileObjectSerializer(required=False, allow_null=True)

    @classmethod
    def upload_file_to_cloud_storage(cls, file_data, blob_name):
        client = storage.Client(credentials=settings.GS_CREDENTIALS)
        bucket_name = settings.GS_BUCKET_NAME

        if file_data:
            file_mime = file_data['mime']
            uploaded_file = file_data['data']
            random_string = PadZeros.generate_random_string(10)

            # Add the random number to the blob name
            blob_name_with_random = f"idarp_files/{blob_name}_{random_string}.{file_mime.split('/')[1]}"

            bucket = client.get_bucket(bucket_name)
            blob = bucket.blob(blob_name_with_random, chunk_size=262144)
            decoded_file = base64.b64decode(uploaded_file)
            blob.upload_from_string(decoded_file, content_type=file_mime)
            return blob.public_url

    def create(self, validated_data):
        identification_file_path_data = validated_data.pop('identification_file_path', None)
        # Access the request object from the context
        request = self.context.get('request', None)
        validated_data['request'] = request
        test = validated_data
        instance = StaffShared(**validated_data)
        instance.save()

        # Upload identification_file_path to cloud storage if provided
        if identification_file_path_data:
            file_mime = identification_file_path_data.get('mime')
            uploaded_file = identification_file_path_data['data']
            instance.identification_file_path = self.upload_file_to_cloud_storage(
                {'mime': file_mime, 'data': uploaded_file},
                'identification_file'
            )
            instance.save()

        return instance

    def update(self, instance, validated_data):
        # Handle updating the StaffShared instance
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class GuestDataRequestSerializer(serializers.Serializer):
    request_purposes = PostRequestPurposeSerializer(many=True)
    list_of_devices = ListOfDeviceSerializer(many=True)
    list_of_staff = StaffListSerializer(many=True)
    requester = serializers.IntegerField()
    data_source_id = serializers.IntegerField()
    title = serializers.CharField()
    department = serializers.CharField(required=False, allow_null=True)
    needed_on = serializers.DateField()
    protocol_ref_num = serializers.CharField()
    ethics_doc_path = FileObjectSerializer(required=False, allow_null=True)
    ethics_approval_letter = serializers.CharField()
    data_specs_path = FileObjectSerializer(required=False, allow_null=True)
    dataset_description = serializers.CharField()
    exempted = serializers.BooleanField()
    submitted = serializers.BooleanField(required=False, allow_null=True)
    file_path = FileObjectSerializer(required=False, allow_null=True)
    data_format = serializers.CharField()
    direct_access_from = serializers.DateField(required=False, allow_null=True)
    direct_access_to = serializers.DateField(required=False, allow_null=True)
    no_date_limit = serializers.BooleanField()
    principal_fname = serializers.CharField()
    principal_sname = serializers.CharField()
    principal_phone = serializers.CharField()
    principal_email = serializers.CharField()
    principal_occupation = serializers.CharField()
    principal_institution = serializers.CharField()
    additional_ethics_committee_name = serializers.CharField()
    additional_IRB_file_path = FileObjectSerializer(required=False, allow_null=True)
    ethics_committee = serializers.PrimaryKeyRelatedField(queryset=IRB.objects.all())
    filters = serializers.DictField(required=False, allow_null=True)

    def validate(self, attrs):
        # Extract data_specs_path and file_path information
        data_specs_data = attrs.pop('data_specs_path', None)
        file_path_data = attrs.pop('file_path', None)
        ethics_doc_path_data = attrs.pop('ethics_doc_path', None)
        additional_IRB_file_path_data = attrs.pop('additional_IRB_file_path', None)

        if data_specs_data:
            mime = data_specs_data.get('mime')
            data = data_specs_data.get('data')
            if mime and data:
                attrs['data_specs_mime'] = mime
                attrs['data_specs_data'] = data
            else:
                raise serializers.ValidationError('Invalid data_specs_path data')

        if file_path_data:
            mime = file_path_data.get('mime')
            data = file_path_data.get('data')
            if mime and data:
                attrs['file_path_mime'] = mime
                attrs['file_path_data'] = data
            else:
                raise serializers.ValidationError('Invalid file_path data')

        if ethics_doc_path_data:

            mime = ethics_doc_path_data.get('mime')
            data = ethics_doc_path_data.get('data')
            if mime and data:
                attrs['ethics_doc_path_mime'] = mime
                attrs['ethics_doc_path_data'] = data
            else:
                raise serializers.ValidationError('Invalid ethics_doc_path data')

        if additional_IRB_file_path_data:

            mime = additional_IRB_file_path_data.get('mime')
            data = additional_IRB_file_path_data.get('data')
            if mime and data:
                attrs['additional_IRB_file_path_mime'] = mime
                attrs['additional_IRB_file_path_data'] = data
            else:
                raise serializers.ValidationError('Invalid additional_IRB_file_path data')

        return attrs


class StaffListAddSerializer(serializers.Serializer):
    request = serializers.PrimaryKeyRelatedField(queryset=DataRequest.objects.all())
    first_name = serializers.CharField(max_length=255)
    surname = serializers.CharField(max_length=255)
    phone = serializers.CharField(max_length=20)
    email = serializers.EmailField()
    identification_type = serializers.CharField(max_length=255)
    identification_number = serializers.CharField(max_length=255)
    position_in_organisation = serializers.CharField(max_length=255)
    confidentiality_protocols = serializers.BooleanField()
    identification_file_path = FileObjectSerializer(required=False, allow_null=True)

    def create(self, validated_data):
        identification_file_path_data = validated_data.pop('identification_file_path', None)
        instance = StaffShared(**validated_data)
        instance.save()

        # Upload identification_file_path to cloud storage if provided
        if identification_file_path_data:
            file_mime = identification_file_path_data.get('mime')
            uploaded_file = identification_file_path_data['data']
            instance.identification_file_path = StaffListSerializer.upload_file_to_cloud_storage(
                {'mime': file_mime, 'data': uploaded_file},
                'identification_file'
            )
            instance.save()

        return instance

class KeywordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Keyword
        fields = '__all__'


class DataRequestPatchSerializer(serializers.Serializer):
    request_id = serializers.IntegerField(read_only=True)
    title = serializers.CharField()
    department = serializers.CharField()
    needed_on = serializers.DateField()
    exempted = serializers.BooleanField()
    data_format = serializers.CharField()
    direct_access_from = serializers.DateField(required=False, allow_null=True)
    direct_access_to = serializers.DateField(required=False, allow_null=True)
    no_date_limit = serializers.BooleanField()
    principal_fname = serializers.CharField()
    principal_sname = serializers.CharField()
    principal_phone = serializers.CharField()
    principal_email = serializers.CharField()
    principal_occupation = serializers.CharField()
    principal_institution = serializers.CharField()

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class EthicsPatchSerializer(serializers.Serializer):
    request_id = serializers.IntegerField(read_only=True)
    protocol_ref_num = serializers.CharField()
    ethics_doc_path = serializers.CharField(required=False, allow_null=True)
    file_path = serializers.CharField(required=False, allow_null=True)
    additional_ethics_committee_name = serializers.CharField(required=False, allow_null=True)
    additional_IRB_file_path = serializers.CharField(required=False, allow_null=True)
    ethics_committee = serializers.PrimaryKeyRelatedField(queryset=IRB.objects.all())

    @classmethod
    def upload_data_request_files(cls, file_data, blob_name, request_no):
        client = storage.Client(credentials=settings.GS_CREDENTIALS)
        bucket_name = settings.GS_BUCKET_NAME

        if file_data:
            file_mime = file_data['mime']
            uploaded_file = file_data['data']

            blob_name_with_random = f"idarp_files/{blob_name}_{PadZeros.pad(request_no)}.{file_mime.split('/')[1]}"

            bucket = client.get_bucket(bucket_name)
            blob = bucket.blob(blob_name_with_random, chunk_size=262144)
            decoded_file = base64.b64decode(uploaded_file)
            blob.upload_from_string(decoded_file, content_type=file_mime)
            return blob.public_url

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class RequestedDatasetPatchSerializer(serializers.Serializer):
    rdataset_id = serializers.IntegerField(read_only=True)
    dataset_description = serializers.CharField(required=False, allow_null=True)
    data_source = serializers.PrimaryKeyRelatedField(queryset=DataSource.objects.all(), required=False, allow_null=True)
    release_date = serializers.DateTimeField(required=False, allow_null=True)

    # filters = serializers.DictField(required=False, allow_null=True)

    @classmethod
    def upload_requested_dataset_files(cls, file_data, blob_name, request_no):
        return DataRequestPatchSerializer.upload_data_request_files(file_data, blob_name, request_no)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
