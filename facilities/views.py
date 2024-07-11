from collections import defaultdict

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.http import JsonResponse
from django.views import View

from facilities.models import Facility
from facilities.serializers import FacilitySerializer


# Create your views here.


class FacilityCreateView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Facility.objects.all()
    serializer_class = FacilitySerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class FacilityListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Facility.objects.all()
    serializer_class = FacilitySerializer

    def get(self, request, *args, **kwargs):
        data = Facility.objects.all().values()
        # Organizing facilities by region and district
        facilities_by_region = defaultdict(lambda: defaultdict(list))

        for facility in data:
            region = facility["region"]
            district = facility["district"]
            facilities_by_region[region][district].append(facility)

        # Create the hierarchical structure
        tree = []

        for idx, (region, districts) in enumerate(facilities_by_region.items()):
            region_node = {
                "label": region,
                "icon": "fa-solid fa-earth-africa",
                "key": f"{idx}",
                "level": "region",
                "children": []
            }

            for j, (district, district_facilities) in enumerate(districts.items()):
                district_node = {
                    "label": district,
                    "icon": "fa-solid fa-landmark",
                    "key": f"{idx}-{j}",
                    "level": "district",
                    "children": []
                }

                for k, facility in enumerate(district_facilities):
                    facility_node = {
                        "label": facility["facility"],
                        "icon": "fa-solid fa-house-medical",
                        "key": f"{idx}-{j}-{k}",
                        "level": "facility",
                        "facility_id": facility["facility_id"],
                        "facility": facility["facility"],
                        "site_id": facility["site_id"],
                        "region": facility["region"],
                        "partner_name": facility["partner_name"],
                        "site_name": facility["site_name"],
                        "emr_type": facility["emr_type"],
                        "funding_agency": facility["funding_agency"],
                        "cdc_region": facility["cdc_region"],
                        "zone": facility["zone"],
                        "status": facility["status"],
                        "orgunit": facility["orgunit"],
                        "date_synced": facility["date_synced"],
                        "district": facility["district"],
                    }
                    district_node["children"].append(facility_node)

                region_node["children"].append(district_node)

            tree.append(region_node)

        return JsonResponse(tree, safe=False)


class FacilityDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Facility.objects.all()
    serializer_class = FacilitySerializer


class FacilityUpdateView(generics.UpdateAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Facility.objects.all()
    serializer_class = FacilitySerializer


class FacilityDestroyView(generics.DestroyAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Facility.objects.all()
    serializer_class = FacilitySerializer
