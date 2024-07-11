from django.contrib import admin
from .models import Topic, Table, TopicTable, Edge, Variable, Dependency, Synonym, InputValue, TimelineOfChange, \
    TableMetadata, TableType, PalettePosition, Color, ColorPalette, DataSource, DataCustodian

# Register your models here.


admin.site.register(Topic)
admin.site.register(Table)
admin.site.register(TableMetadata)
admin.site.register(TopicTable)
admin.site.register(Edge)
admin.site.register(Variable)
admin.site.register(Dependency)
admin.site.register(Synonym)
admin.site.register(InputValue)
admin.site.register(TimelineOfChange)
admin.site.register(TableType)
admin.site.register(PalettePosition)
admin.site.register(Color)
admin.site.register(ColorPalette)
admin.site.register(DataSource)
admin.site.register(DataCustodian)