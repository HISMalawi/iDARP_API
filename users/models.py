from django.db import models
from djtriggers.models import Trigger
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
import logging

logger = logging.getLogger(__name__)


# Create your models here.

class MyUserManager(BaseUserManager):
    def create_user(self, fname, sname, username, password, **extra_fields):
        if not fname:
            raise ValueError('Users must have a firstname')

        if not sname:
            raise ValueError('Users must have a surname')

        if not username:
            raise ValueError('Users must have an email address or phone number')

        user = self.model(**extra_fields)

        if '@' in username:  # If '@' is present, consider it as an email
            user.org_email = self.normalize_email(username)
        else:  # Otherwise, consider it as a phone number
            user.phone = username

        user.is_active = True
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, fname, org_email, password, org, **extra_fields):
        org = Organization.objects.get(org_id=org)
        user = self.create_user(
            org_email=org_email,
            fname=fname,
            password=password,
            org_id=org.org_id,
            **extra_fields
        )
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.save(using=self._db)
        return user


class Organization(models.Model):
    org_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    domain = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    active = models.IntegerField()
    country = models.CharField(max_length=45)

    class Meta:
        managed = True
        db_table = 'organizations'

    def __str__(self):
        return self.name


class Role(models.Model):
    role_id = models.AutoField(primary_key=True)
    role = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    rank = models.IntegerField(null=True, blank=True)

    class Meta:
        managed = True
        db_table = 'roles'

    def __str__(self):
        return f"role_id: {self.pk} {self.role}"


class OrgRole(models.Model):
    org = models.ForeignKey(Organization, models.DO_NOTHING)
    role = models.ForeignKey(Role, models.DO_NOTHING)
    org_role_id = models.AutoField(primary_key=True)

    class Meta:
        managed = True
        db_table = 'org_roles'
        unique_together = (('org', 'role'),)

    def __str__(self):
        return f"org_role_id: {self.pk} {self.role} -> {self.org}"


class OrgRoleStatus(models.Model):
    org_role_status_id = models.AutoField(primary_key=True)
    org_role = models.ForeignKey(OrgRole, models.DO_NOTHING)
    status = models.BooleanField()
    changed_on = models.DateTimeField(null=True, blank=True)
    Reason = models.TextField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'org_role_statuses'

    def __str__(self):
        return f"id: {self.org_role_status_id} status: {self.status}"


class User(AbstractBaseUser, PermissionsMixin):
    user_id = models.AutoField(primary_key=True)
    p_photo_path = models.TextField(null=True, blank=True)
    fname = models.CharField(max_length=30)
    sname = models.CharField(max_length=30)
    middle_name = models.CharField(max_length=30, blank=True, null=True)
    org_email = models.CharField(unique=True, max_length=255, blank=True, null=True)
    phone = models.CharField(unique=True, max_length=20)
    designation = models.CharField(max_length=255)
    department = models.CharField(null=True, blank=True, max_length=255)
    is_active = models.BooleanField(default=True)
    org = models.ForeignKey(Organization, models.DO_NOTHING)
    tentative_organization = models.CharField(max_length=255, null=True, blank=True)
    attempts = models.IntegerField(null=True)
    last_attempt = models.DateTimeField(null=True)
    hits = models.IntegerField(null=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    email_is_verified = models.BooleanField(default=False)

    USERNAME_FIELD = 'phone'

    REQUIRED_FIELDS = ['fname', 'sname', 'designation', 'org']

    def update_password(self, password):
        self.set_password(password)
        self.save()

    def has_module_perms(self, app_label):
        """
        Returns True if the user has any permissions in the given app label.
        """
        return self.is_staff

    objects = MyUserManager()

    class Meta:
        managed = True
        db_table = 'users'

    def __str__(self):
        return f"user_id: {self.pk} {self.fname} {self.sname}"


class TempOtp(models.Model):
    otp_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=255)
    otp = models.CharField(max_length=6)
    created_on = models.DateTimeField()

    class Meta:
        managed = True
        db_table = 'temp_otp'

    def __str__(self):
        return f"username: {self.username} otp: {self.otp}"


class RoleStatus(models.Model):
    role_status_id = models.AutoField(primary_key=True)
    status = models.CharField(max_length=255)
    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = True
        db_table = 'role_statuses'

    def __str__(self):
        return f"id: {self.role_status_id} status: {self.status}"


class AssignedRole(Trigger):
    assigned_role_id = models.AutoField(primary_key=True)
    org_role = models.ForeignKey(OrgRole, on_delete=models.DO_NOTHING)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    created_on = models.DateTimeField(auto_now_add=True)
    assigned_by = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'assigned_roles'
        unique_together = (('org_role', 'user'),)

    typed = 'assigned_role'

    def __str__(self):
        return f"assigned_role_id: {self.assigned_role_id} {str(self.org_role)} {str(self.user)}"

    def _process(self, dictionary={}):
        # Getting Pending Role Status
        pending = RoleStatus.objects.get(role_status_id=1)
        # Creating Assigned Role Status
        AssignedRoleStatus.objects.create(assigned_role=self, role_status=pending)


class AssignedRoleStatus(models.Model):
    assigned_role_status_id = models.AutoField(primary_key=True)
    assigned_role = models.ForeignKey(AssignedRole, models.DO_NOTHING)
    role_status = models.ForeignKey(RoleStatus, models.DO_NOTHING)
    state_changed_on = models.DateTimeField(auto_now_add=True)
    Reason = models.TextField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'assigned_role_statuses'

    def __str__(self):
        return f"id : {self.assigned_role_status_id} status: {self.role_status}"


class UserAuditTrail(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.IntegerField(blank=True, null=True)
    cookie_id = models.CharField(max_length=255, blank=True, null=True)
    action = models.CharField(max_length=255, blank=True, null=True)
    object = models.CharField(max_length=255, blank=True, null=True)
    old_value = models.TextField(blank=True, null=True)
    new_value = models.TextField(blank=True, null=True)
    ip_address = models.CharField(max_length=255, blank=True, null=True)
    user_agent = models.CharField(max_length=255, blank=True, null=True)
    referer = models.CharField(max_length=255, blank=True, null=True)
    script_name = models.CharField(max_length=255, blank=True, null=True)
    page = models.CharField(max_length=255, blank=True, null=True)
    done_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'user_audit_trail'

    def __str__(self):
        return f"id: {self.id} ip: {self.ip_address}"


class OrgRoleStatusChange(models.Model):
    org_role = models.ForeignKey(OrgRole, models.DO_NOTHING)
    status = models.BooleanField()
    changed_on = models.DateTimeField()

    class Meta:
        managed = True
        db_table = 'org_role_status_change'

    def __str__(self):
        return f"id: {self.org_role} status: {self.status}"

