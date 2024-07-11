from django.contrib import admin
from .models import *

# Register your models here.

admin.site.register(DataRequest)
admin.site.register(RequestState)
admin.site.register(RequestedDataset)
admin.site.register(Purpose)
admin.site.register(RequestPurpose)
admin.site.register(DatasetPreset)
admin.site.register(DatasetVariable)
admin.site.register(StateLookup)
admin.site.register(EquipmentType)
admin.site.register(DataHandlingDevice)
admin.site.register(IRB)
