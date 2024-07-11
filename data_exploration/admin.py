from django.contrib import admin
from .models import Preset, PresetVariable, PresetFilter
# Register your models here.

admin.site.register(Preset)
admin.site.register(PresetVariable)
admin.site.register(PresetFilter)