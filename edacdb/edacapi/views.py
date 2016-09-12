from django.shortcuts import render

from .models import CMDR, Ship, System
from rest_framework import viewsets
from .serializers import CMDRSerializer, ShipSerializer, SystemSerializer


class CMDRViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows CMDRs to be viewed or edited.
    """
    queryset = CMDR.objects.all()
    serializer_class = CMDRSerializer


class CMDRByNameViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows CMDRs to be viewed or edited.
    """
    queryset = CMDR.objects.all()[:100]
    serializer_class = CMDRSerializer

    def get_queryset(self):
        name = self.kwargs.get('name', None)
        return queryset.get(name__iexact=name)


class ShipViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Ships to be viewed or edited.
    """
    queryset = Ship.objects.all()[:100]
    serializer_class = ShipSerializer


class SystemViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Systems to be viewed or edited.
    """
    queryset = System.objects.all()[:100]
    serializer_class = SystemSerializer
