from django.views import View
from .dbconnect import connectGcpDB
from data_dictionary.models import *
from data_dictionary.serializers import *
from rest_framework import generics
from django.contrib.auth.models import User
from rest_framework import permissions
from rest_framework.permissions import IsAdminUser
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404, JsonResponse
from rest_framework.exceptions import ValidationError


class TimelineOfChangeDetail(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = TimelineOfChange.objects.all()
    serializer_class = TimelineOfChangeSerializer


class TimelineOfChangeList(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = TimelineOfChange.objects.all()
    serializer_class = TimelineOfChangeSerializer


class DependencyDetail(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Dependency.objects.all()
    serializer_class = DependencySerializer


class DependencyList(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Dependency.objects.all()
    serializer_class = DependencySerializer


class InputValueDetail(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = InputValue.objects.all()
    serializer_class = InputValueSerializer


class InputValueList(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = InputValue.objects.all()
    serializer_class = InputValueSerializer


class SynonymDetail(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Synonym.objects.all()
    serializer_class = SynonymSerializer


class SynonymList(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Synonym.objects.all()
    serializer_class = SynonymSerializer


class VariableDetail(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Variable.objects.all()
    serializer_class = VariableSerializer


class VariableList(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Variable.objects.all().order_by('-is_primary', '-is_foreign')
    serializer_class = VariableSerializer


class EdgeDetail(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Edge.objects.all()
    serializer_class = EdgeSerializer


class EdgeList(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Edge.objects.all()
    serializer_class = EdgeSerializer


class TableDetail(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Table.objects.all()
    serializer_class = TableSerializer


class TableList(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Table.objects.filter(publish=True)
    serializer_class = TableSerializer


class TableNoFilterList(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Table.objects.all()
    serializer_class = TableSerializer


class TopicTableDetail(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = TopicTable.objects.all()
    serializer_class = TopicTableSerializer


class TopicTableList(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = TopicTable.objects.filter(tbl__publish=True)
    serializer_class = TopicTableSerializer


class TopicDetail(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Topic.objects.all()
    serializer_class = TopicSerializer


class TopicList(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Topic.objects.all()
    serializer_class = TopicSerializer


class TableTypeDetail(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = TableType.objects.all()
    serializer_class = TableTypeSerializer


class TableTypeList(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = TableType.objects.all()
    serializer_class = TableTypeSerializer


class PalettePositionDetail(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = PalettePosition.objects.all()
    serializer_class = PalettePositionSerializer


class PalettePositionList(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = PalettePosition.objects.all()
    serializer_class = PalettePositionSerializer


class ColorDetail(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Color.objects.all()
    serializer_class = ColorSerializer


class ColorList(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Color.objects.all()
    serializer_class = ColorSerializer


class ColorPaletteDetail(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = ColorPalette.objects.all()
    serializer_class = ColorPaletteSerializer


class ColorPaletteList(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = ColorPalette.objects.all()
    serializer_class = ColorPaletteSerializer


class DataSourceDetail(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = DataSource.objects.all()
    serializer_class = DataSourceSerializer


class DataSourceList(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = DataSource.objects.all()
    serializer_class = DataSourceSerializer


class DataSourceTreeList(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = DataSourceTreeSerializer
    queryset = DataSource.objects.all()


class DataSourceTreeDetail(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = DataSourceTreeSerializer
    queryset = DataSource.objects.all()


# Get Results from DQA
class DqaResults(View):
    def get(self, request, *args, **kwargs):
        data_source_id = kwargs['data_source_id']
        # Connect to DQA
        gcpCnx = connectGcpDB()
        gcp_cursor = gcpCnx.cursor()

        query = "SELECT * FROM dqa_snapshots"
        gcp_cursor.execute(query)
        res = gcp_cursor.fetchall()

        data_source = DataSource.objects.all().filter(data_source_id=data_source_id).values(
            ''
        )

        return JsonResponse(data=list(data_source), safe=False)
