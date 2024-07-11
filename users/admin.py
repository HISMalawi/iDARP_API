from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Organization, Role, OrgRole, User, UserAuditTrail, AssignedRole, TempOtp, OrgRoleStatus, \
     AssignedRoleStatus


# Register your models here.

class MyUserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('fname', 'sname', 'middle_name','org_email','phone', 'designation', 'org', 'password')}),
        ('Permissions', {'fields': ('is_active','is_staff','is_admin', 'is_superuser',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('fname', 'sname', 'middle_name','org_email','phone', 'designation', 'org', 'password1', 'password2','is_active','is_staff', 'is_admin'),
        }),
    )
    list_display = ('phone', 'org_email','is_active','is_staff', 'is_admin','is_superuser',)
    list_filter = ('is_admin',)
    search_fields = ('org_email',)
    ordering = ('org_email',)
    filter_horizontal = ()


admin.site.register(Organization)
admin.site.register(Role)
admin.site.register(OrgRole)
admin.site.register(AssignedRole)
admin.site.register(User, MyUserAdmin)
admin.site.register(UserAuditTrail)
admin.site.register(TempOtp)
admin.site.register(OrgRoleStatus)
admin.site.register(AssignedRoleStatus)
