from analytics.models import Tag
from data_dictionary.models import *
from data_exploration.models import Preset
from users.models import *
from utils.base_model import BaseModel


# Create your models here.

class ApprovalProcedure(models.Model):
    approval_procedure_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    designed_on = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        db_table = 'approval_procedures'
        managed = True

    def __str__(self):
        return f"approval_procedure_id : {self.pk} name : {self.name}"


class StageType(models.Model):
    stage_type_id = models.AutoField(primary_key=True)
    stage_type = models.CharField(max_length=255)

    class Meta:
        db_table = 'stage_types'
        managed = True

    def __str__(self):
        return f"stage_type_id : {self.pk} stage_type : {self.stage_type}"


class Stage(models.Model):
    stage_id = models.AutoField(primary_key=True)
    approval_procedure = models.ForeignKey(ApprovalProcedure, on_delete=models.CASCADE)
    stage_order = models.IntegerField(null=True, blank=True)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    stage_activity = models.TextField(null=True, blank=True)
    stage_type = models.ForeignKey(StageType, on_delete=models.CASCADE)
    branch_level = models.IntegerField(default=0)
    pos_x = models.DecimalField(null=True, blank=True, decimal_places=2, max_digits=5)
    pos_y = models.DecimalField(null=True, blank=True, decimal_places=2, max_digits=5)
    icon = models.CharField(max_length=30, null=True, blank=True)

    class Meta:
        db_table = 'stages'
        managed = True

    def __str__(self):
        return f"stage_id : {self.pk} stage_order : {self.stage_order}"


class NextStage(models.Model):
    next_stage_id = models.AutoField(primary_key=True)
    current_stage = models.ForeignKey(Stage, on_delete=models.CASCADE, related_name='next_stage_connections')
    next = models.ForeignKey(Stage, on_delete=models.CASCADE, related_name='prev_stage_connections')

    class Meta:
        db_table = 'next_stages'
        managed = True

    def __str__(self):
        return f"next_stage_id : {self.pk} current_stage : {str(self.current_stage)} next : {str(self.next)}"


class Purpose(models.Model):
    purpose_id = models.AutoField(primary_key=True)
    purpose = models.CharField(max_length=35, unique=True)

    class Meta:
        managed = True
        db_table = 'purposes'

    def __str__(self):
        return self.purpose


class IRB(models.Model):
    irb_id = models.AutoField(primary_key=True)
    irb_name = models.CharField(max_length=255)

    class Meta:
        managed = True
        db_table = 'irbs'

    def __str__(self):
        return f'id: {self.pk}, IRB: {self.irb_name}'


class DataRequest(models.Model):
    request_id = models.AutoField(primary_key=True)
    requester = models.ForeignKey(AssignedRole, models.DO_NOTHING)
    date_created = models.DateTimeField(auto_now_add=True)
    title = models.TextField(blank=True, null=True)
    department = models.CharField(blank=True, null=True, max_length=255)
    needed_on = models.DateField()
    protocol_ref_num = models.CharField(blank=True, null=True, max_length=255)
    ethics_doc_path = models.CharField(blank=True, null=True, max_length=255)
    ethics_approval_letter = models.CharField(max_length=10, null=True, choices=(
        ('Yes', 'Yes'),
        ('No', 'No'),
        ('N/A', 'N/A')
    ))
    submitted = models.BooleanField(blank=True, null=True)
    submitted_on = models.DateTimeField(blank=True, null=True)
    file_path = models.CharField(blank=True, null=True, max_length=255)
    exempted = models.BooleanField(default=False)
    data_format = models.CharField(max_length=65, default="Electronic", choices=(
        ('Paper-based', 'Paper-based'),
        ('Electronic', 'Electronic'),
        ('Direct access', 'Direct access')
    ))
    direct_access_from = models.DateField(null=True, blank=True)
    direct_access_to = models.DateField(null=True, blank=True)
    no_date_limit = models.BooleanField(default=False)
    principal_fname = models.CharField(max_length=70, default="N/A")
    principal_sname = models.CharField(max_length=70, default="N/A")
    principal_phone = models.CharField(max_length=20, default="+265000000000")
    principal_email = models.CharField(max_length=255, default="requester@idarp.mw")
    principal_occupation = models.CharField(max_length=255, default="Data Requester")
    principal_institution = models.CharField(max_length=255, default="Data Requester")
    additional_ethics_committee_name = models.CharField(max_length=255, null=True, blank=True)
    additional_IRB_file_path = models.CharField(max_length=255, null=True, blank=True)
    ethics_committee = models.ForeignKey(IRB, on_delete=models.DO_NOTHING)

    class Meta:
        managed = True
        db_table = 'data_requests'

    def __str__(self):
        return f"{self.title} {self.submitted_on}"


class RequestPurpose(models.Model):
    request_purpose_id = models.AutoField(primary_key=True)
    request = models.ForeignKey(DataRequest, on_delete=models.CASCADE)
    purpose = models.ForeignKey(Purpose, on_delete=models.CASCADE)
    purpose_description = models.TextField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'request_purposes'

    def __str__(self):
        return f"id: {self.request_purpose_id} purpose: {str(self.purpose)}"


class StateLookup(models.Model):
    state_lookup_id = models.AutoField(primary_key=True)
    state = models.CharField(max_length=255, choices=(
        ('Incoming', 'Incoming'),
        ('Unattended', 'Unattended'),
        ('Approved', 'Approved'),
        ('Denied', 'Denied')),
                             )

    class Meta:
        managed = True
        db_table = 'state_lookups'

    def __str__(self):
        return f"states_id: {self.pk} state: {self.state}"


class RequestState(models.Model):
    request_state_id = models.AutoField(primary_key=True)
    request = models.ForeignKey(DataRequest, models.DO_NOTHING, related_name='data_request')
    org_role = models.ForeignKey(OrgRole, models.DO_NOTHING)
    attention = models.CharField(max_length=255, null=True, blank=True)
    state_lookup = models.ForeignKey(StateLookup, on_delete=models.CASCADE)
    reason = models.TextField(blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    responded_on = models.DateTimeField(blank=True, null=True)
    attended_by = models.ForeignKey(AssignedRole, models.DO_NOTHING, blank=True, null=True)
    reminders_count = models.IntegerField(default=0)
    stage_order = models.IntegerField(null=True, blank=True)
    stage_type = models.CharField(max_length=255, null=True, blank=True)
    branch_level = models.IntegerField(default=0)
    pos_x = models.DecimalField(null=True, blank=True, decimal_places=2, max_digits=5)
    pos_y = models.DecimalField(null=True, blank=True, decimal_places=2, max_digits=5)
    icon = models.CharField(max_length=30, null=True, blank=True)

    class Meta:
        managed = True
        db_table = 'request_state'

    def __str__(self):
        return f"{self.request} {self.org_role}"


class NextState(models.Model):
    next_state_id = models.AutoField(primary_key=True)
    current_state = models.ForeignKey(RequestState, on_delete=models.CASCADE, related_name='current_state')
    next = models.ForeignKey(RequestState, on_delete=models.CASCADE, related_name='next_state')

    class Meta:
        db_table = 'next_state'
        managed = True

    def __str__(self):
        return f"next_state_id : {self.pk} current_state: {str(self.current_state)} next_state : {str(self.next)}"


class RequestedDataset(models.Model):
    rdataset_id = models.AutoField(primary_key=True)
    request = models.ForeignKey(DataRequest, models.DO_NOTHING)
    dataset_description = models.TextField(blank=True, null=True)
    data_source = models.ForeignKey(DataSource, on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now=True)
    release_date = models.DateTimeField(null=True, blank=True)
    data_specs_path = models.CharField(null=True, blank=True, max_length=255)
    filters = models.TextField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'requested_datasets'

    def __str__(self):
        return f"{self.request} {self.dataset_description}"


class DatasetPreset(models.Model):
    preset = models.OneToOneField(Preset, on_delete=models.CASCADE, primary_key=True)
    rdataset = models.ForeignKey(DataRequest, on_delete=models.CASCADE)

    class Meta:
        managed = True
        db_table = 'dataset_presets'

    def __str__(self):
        return f"ID: {self.preset} Request Dataset: {str(self.rdataset)}"


class DatasetVariable(models.Model):
    dataset_variable_id = models.AutoField(primary_key=True)
    rdataset = models.ForeignKey(RequestedDataset, on_delete=models.CASCADE, related_name='dataset_variables')
    var = models.ForeignKey(Variable, on_delete=models.CASCADE)
    is_distinct = models.BooleanField(null=True, blank=True)
    date_added = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = 'dataset_variables'

    def __str__(self):
        return f'id: {self.pk} RD: {str(self.rdataset)} Var: {str(self.var)}'


class EquipmentType(models.Model):
    equipment_type_id = models.AutoField(primary_key=True)
    equipment_type = models.CharField(max_length=255)

    class Meta:
        managed = True
        db_table = 'equipment_types'

    def __str__(self):
        return f'id: {self.pk}, Equipment Type: {self.equipment_type}'


class DataHandlingDevice(BaseModel):
    device_id = models.AutoField(primary_key=True)
    request = models.ForeignKey(DataRequest, on_delete=models.CASCADE)
    equipment_name = models.CharField(max_length=255,default="No Equipment Name")
    serial_number = models.CharField(max_length=100)
    used_by = models.CharField(max_length=200)
    organisation = models.CharField(max_length=255)
    usage_from = models.DateField(blank=False, null=False)
    usage_to = models.DateField(blank=False, null=False)
    equipment_type = models.ForeignKey(EquipmentType, on_delete=models.DO_NOTHING, default=1)

    class Meta:
        managed = True
        db_table = 'data_handling_devices'

    def __str__(self):
        return f'id: {self.pk} Data_Request: {str(self.request)}'


class StaffShared(BaseModel):
    staff_shared_id = models.AutoField(primary_key=True)
    request = models.ForeignKey(DataRequest, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=50)
    surname = models.CharField(max_length=50)
    phone = models.CharField(max_length=15)
    email = models.CharField(max_length=255)
    identification_type = models.CharField(max_length=50, choices=(
        ('Passport', 'Passport'),
        ('National ID', 'National ID'),
        ('None', 'None')
    ))
    identification_number = models.CharField(max_length=30, blank=True, null=True)
    position_in_organisation = models.CharField(max_length=265)
    confidentiality_protocols = models.BooleanField(blank=False, null=False)
    identification_file_path = models.CharField(max_length=500, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'staff_shared'

    def __str__(self):
        return f'id: {self.pk} Data_Request: {str(self.request)}'


class StateComment(models.Model):
    comment_id = models.AutoField(primary_key=True)
    request_state = models.ForeignKey(RequestState, on_delete=models.CASCADE)
    comment = models.TextField()
    authored_on = models.DateTimeField(auto_now_add=True)
    section = models.CharField(max_length=255)
    resolved = models.BooleanField(default=False)
    author = models.ForeignKey(AssignedRole, on_delete=models.CASCADE)
    action_required = models.BooleanField(default=False)

    class Meta:
        managed = True
        db_table = 'state_comments'


class Reply(models.Model):
    reply_id = models.AutoField(primary_key=True)
    comment = models.ForeignKey(StateComment, on_delete=models.CASCADE)
    reply = models.TextField()
    responded_on = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(AssignedRole, on_delete=models.CASCADE)

    class Meta:
        managed = True
        db_table = 'replies'


class Keyword(models.Model):
    keyword_id = models.AutoField(primary_key=True)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    request = models.ForeignKey(DataRequest, on_delete=models.CASCADE)

    class Meta:
        managed = True
        db_table = 'keywords'
