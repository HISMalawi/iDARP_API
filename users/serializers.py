from rest_framework import serializers
from users.models import *
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate, get_user_model
from users.backends.authenticate_username_and_otp import UsernameAndOTPModelBackend, RecordExpiredException
from users.backends.authenticate_email_or_phone import EmailOrPhoneModelBackend
import logging
from django.utils import timezone
from datetime import datetime, timedelta
import random

logger = logging.getLogger(__name__)


class UserAuditTrailSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAuditTrail
        fields = [
            'user_id',
            'cookie_id',
            'action',
            'object',
            'old_value',
            'new_value',
            'ip_address',
            'user_agent',
            'referer',
            'script_name',
            'page',
            'done_at'
        ]

    def create(self, validated_data):
        for key, value in self.context.items():
            validated_data[key] = self.context.get(key, '')

        return super().create(validated_data)


class UserGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'user_id',
            'fname',
            'sname',
            'middle_name',
            'org_email',
            'phone',
            'designation',
            'department',
        ]


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    middle_name = serializers.CharField(required=False, allow_null=True)
    department = serializers.CharField(required=False, allow_null=True)
    tentative_organization = serializers.CharField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = [
            'user_id',
            'p_photo_path',
            'fname',
            'sname',
            'middle_name',
            'org_email',
            'phone',
            'designation',
            'department',
            'tentative_organization',
            'password',
            'is_active',
            'is_staff',
            'org',
            'email_is_verified',
        ]

    def create(self, validated_data):
        password = validated_data.pop('password')
        hashed_password = make_password(password)

        for key, value in self.context.items():
            validated_data[key] = self.context.get(key, '')

        user = User.objects.create(password=hashed_password, **validated_data)
        return user


class UserSignInSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        request = self.context.get('request')

        if username and password:

            user = EmailOrPhoneModelBackend.authenticate(self, request, username, password)

            if not user:
                raise serializers.ValidationError('Invalid username or password')

        else:
            raise serializers.ValidationError('Username and password are required')

        attrs['user'] = user
        return attrs


class UserSignUpOTPSerializer(serializers.ModelSerializer):
    class Meta:
        model = TempOtp
        fields = [
            'otp_id',
            'username',
            'otp',
            'created_on'
        ]
        read_only_fields = ['otp', 'created_on']

    def create(self, validated_data):
        for key, value in self.context.items():
            validated_data[key] = self.context.get(key, '')

        return super().create(validated_data)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        return {'otp_id': representation['otp_id']}


class UserOTPResendSerializer(serializers.Serializer):
    username = serializers.CharField()

    def validate(self, attrs):
        username = attrs.get('username')
        request = self.context.get('request')

        if not username:
            raise serializers.ValidationError('Username is required')

        return attrs


class OTPVerificationSerializer(serializers.Serializer):
    otp = serializers.CharField()
    username = serializers.CharField()

    def validate(self, attrs):
        username = attrs.get('username')
        otp = attrs.get('otp')

        if not TempOtp.objects.filter(username=username, otp=otp).exists():
            raise serializers.ValidationError('OTP does not exist')

        try:
            temp_otp = TempOtp.objects.filter(otp=otp, username=username).order_by('-created_on').first()

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


class UserSignUpOTPVerificationSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(required=False, allow_null=True)
    username = serializers.CharField()
    otp = serializers.CharField()
    org = serializers.IntegerField()
    fname = serializers.CharField()
    middle_name = serializers.CharField(required=False, allow_null=True)
    department = serializers.CharField(required=False, allow_null=True)
    tentative_organization = serializers.CharField(required=False, allow_null=True)
    phone = serializers.CharField()
    org_email = serializers.EmailField()
    sname = serializers.CharField()
    designation = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        user_id = attrs.get('user_id')
        username = attrs.get('username')
        otp = attrs.get('otp')

        if not TempOtp.objects.filter(username=username, otp=otp).exists():
            raise serializers.ValidationError('OTP does not exist')

        if '@' in username:
            # Authenticate using org_email
            try:
                temp_otp = TempOtp.objects.filter(otp=otp, username=username).order_by('-created_on').first()

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

        else:
            # Authenticate using phone number
            try:
                temp_otp = TempOtp.objects.filter(otp=otp, username=username).order_by('-created_on').first()

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


class UserProfileUpdateSerializer(serializers.Serializer):
    fname = serializers.CharField()
    middle_name = serializers.CharField(required=False, allow_null=True)
    sname = serializers.CharField()
    department = serializers.CharField()
    designation = serializers.CharField()

    def update(self, instance, validated_data):
        instance.fname = validated_data.get('fname', instance.fname)
        instance.middle_name = validated_data.get('middle_name', instance.middle_name)
        instance.sname = validated_data.get('sname', instance.sname)
        instance.department = validated_data.get('department', instance.department)
        instance.designation = validated_data.get('designation', instance.designation)
        instance.save()
        return instance


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = [
            'org_id',
            'name',
            'domain',
            'description',
            'active',
            'country',
        ]


class OrgRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrgRole
        fields = [
            'role',
            'org_role_id',
        ]
        depth = 1


class RoleStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoleStatus
        fields = [
            'role_status_id',
            'status',
            'created_on',
            'modified_on',
        ]


class AssignedRoleStatusSerializer(serializers.ModelSerializer):
    role_status = RoleStatusSerializer()

    class Meta:
        model = AssignedRoleStatus
        fields = [
            'assigned_role_status_id',
            'assigned_role',
            'role_status',
            'state_changed_on',
        ]


class AssignedRoleStatusPatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssignedRoleStatus
        fields = [
            'assigned_role_status_id',
            'role_status',
        ]


class AssignRoleGetSerializer(serializers.Serializer):
    org_role = OrgRoleSerializer()
    user = UserGetSerializer()

    class Meta:
        model = AssignedRole
        fields = [
            'assigned_role_id',
            'org_role',
            'org_role_id',
            'assigned_role_status',
            'user',
        ]
        read_only_fields = ['created_on', 'assigned_role_id', ]


class AssignedRoleStatusAdminSerializer(serializers.ModelSerializer):
    role_status = RoleStatusSerializer()
    assigned_role = AssignRoleGetSerializer()

    class Meta:
        model = AssignedRoleStatus
        fields = [
            'assigned_role_status_id',
            'assigned_role',
            'role_status',
            'state_changed_on',
        ]


class AssignRoleSerializer(serializers.ModelSerializer):
    org_role = OrgRoleSerializer()
    assigned_role_status = serializers.SerializerMethodField()

    class Meta:
        model = AssignedRole
        fields = [
            'assigned_role_id',
            'org_role',
            'org_role_id',
            'assigned_role_status',
            'user',
            'created_on',
            'assigned_by'
        ]
        read_only_fields = ['created_on', 'assigned_role_id', ]

    def get_assigned_role_status(self, obj):
        assigned_role_status_array = []
        try:
            assigned_role_statuses = AssignedRoleStatus.objects.filter(
                assigned_role_id=obj.assigned_role_id
            ).order_by('-state_changed_on')

            for assigned_role_status in assigned_role_statuses:
                assigned_role_status_array.append(str(assigned_role_status))
        except AssignedRoleStatus.DoesNotExist:
            pass

        return assigned_role_status_array

    def create(self, validated_data):
        org_role_data = validated_data.pop('org_role')
        org_role_serializer = OrgRoleSerializer(data=org_role_data)
        org_role_serializer.is_valid(raise_exception=True)
        org_role = org_role_serializer.save()

        validated_data['org_role'] = org_role
        assigned_role = AssignedRole.objects.create(**validated_data)

        return assigned_role


class AssignRoleCustomSerializer(serializers.Serializer):
    assigned_role_status_id = serializers.IntegerField()
    assigned_role_id = serializers.IntegerField()
    role_status_id = serializers.IntegerField()
    password = serializers.CharField()

    def validate(self, attrs):
        assigned_role_status_id = attrs.get('assigned_role_status_id')
        assigned_role_id = attrs.get('assigned_role_id')
        role_status_id = attrs.get('role_status_id')

        if not AssignedRole.objects.filter(pk=assigned_role_id).exists():
            raise serializers.ValidationError('Assigned Role does not exist.')

        if not AssignedRoleStatus.objects.filter(pk=assigned_role_status_id).exists():
            raise serializers.ValidationError('Assigned Role Status does not exist.')

        if not RoleStatus.objects.filter(pk=role_status_id).exists():
            raise serializers.ValidationError('Role Status does not exist.')

        return attrs


class OrgRoleStatusSerializer(serializers.Serializer):
    class Meta:
        model = OrgRoleStatus
        fields = '__all__'


class UserActivationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('is_active',)

    def update(self, instance, validated_data):
        instance.is_active = validated_data.get('is_active', instance.is_active)
        instance.save()
        return instance


class CheckPhoneNumberSerializer(serializers.Serializer):
    phone = serializers.CharField(required=False, allow_null=False)


class EmailVerificationSerializer(serializers.Serializer):
    org_email = serializers.EmailField(required=False, allow_null=False)


User = get_user_model()


class EmailSerializer(serializers.Serializer):
    org_email = serializers.EmailField(required=False, allow_null=False)
    email_is_verified = serializers.BooleanField(required=True)

    def validate_org_email(self, value):
        """
        Validate that the org_email is unique across users.
        """
        if User.objects.filter(org_email=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError("This email is already registered by another user.")
        return value


class PhoneNumberSerializer(serializers.Serializer):
    phone = serializers.CharField(required=False, allow_null=False)

    def validate_phone(self, value):
        """
        Validate that the phone number is unique across users.
        """
        if User.objects.filter(phone=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError("This phone is already registered by another user.")
        return value
