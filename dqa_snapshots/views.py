from django.shortcuts import render
from rest_framework import generics, permissions, status
from dqa_snapshots.models import *
from dqa_snapshots.serializers import *
from rest_framework.response import Response

# Create your views here.


# VariableLevelCheck Views
class VariableLevelCheckCreateView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = VariableLevelCheck.objects.all()
    serializer_class = VariableLevelCheckSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class VariableLevelCheckListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = VariableLevelCheck.objects.all()
    serializer_class = VariableLevelCheckSerializer


class VariableLevelCheckDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = VariableLevelCheck.objects.all()
    serializer_class = VariableLevelCheckSerializer


class VariableLevelCheckUpdateView(generics.UpdateAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = VariableLevelCheck.objects.all()
    serializer_class = VariableLevelCheckSerializer


class VariableLevelCheckDestroyView(generics.DestroyAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = VariableLevelCheck.objects.all()
    serializer_class = VariableLevelCheckSerializer


# Proportion Views
class ProportionCreateView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Proportion.objects.all()
    serializer_class = ProportionSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class ProportionListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Proportion.objects.all()
    serializer_class = ProportionSerializer


class ProportionDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Proportion.objects.all()
    serializer_class = ProportionSerializer


class ProportionUpdateView(generics.UpdateAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Proportion.objects.all()
    serializer_class = ProportionSerializer


class ProportionDestroyView(generics.DestroyAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Proportion.objects.all()
    serializer_class = ProportionSerializer


# Snapshot Views
class SnapshotCreateView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Snapshot.objects.all()
    serializer_class = SnapshotSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class SnapshotListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Snapshot.objects.all()
    serializer_class = SnapshotSerializer


class SnapshotDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Snapshot.objects.all()
    serializer_class = SnapshotSerializer


class SnapshotUpdateView(generics.UpdateAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Snapshot.objects.all()
    serializer_class = SnapshotSerializer


class SnapshotDestroyView(generics.DestroyAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Snapshot.objects.all()
    serializer_class = SnapshotSerializer


# Result Views
class ResultCreateView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Result.objects.all()
    serializer_class = ResultSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class ResultListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Result.objects.all()
    serializer_class = ResultSerializer


class ResultDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Result.objects.all()
    serializer_class = ResultSerializer


class ResultUpdateView(generics.UpdateAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Result.objects.all()
    serializer_class = ResultSerializer


class ResultDestroyView(generics.DestroyAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Result.objects.all()
    serializer_class = ResultSerializer
