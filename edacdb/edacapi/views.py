from django.shortcuts import render
from django.db import transaction

from .models import CMDR, Ship, System
from .models import ModuleSlot, HardpointMount
from .models import SecurityLevel, Allegiance, State, Faction, Power
from .models import Government, PowerState, Economy
from rest_framework import viewsets
from rest_framework_bulk import BulkModelViewSet
from .serializers import CMDRSerializer, ShipSerializer, SystemSerializer
from .serializers import ModuleSlotSerializer, HardpointMountSerializer
from .serializers import SecurityLevelSerializer, AllegianceSerializer
from .serializers import StateSerializer, FactionSerializer, PowerSerializer
from .serializers import GovernmentSerializer, PowerStateSerializer
from .serializers import EconomySerializer, SystemIDSerializer
from .serializers import SystemBulkSerializer





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
    queryset = CMDR.objects.all()
    serializer_class = CMDRSerializer

    def get_queryset(self):
        print(self.request.query_params)
        name = self.request.query_params['name']
        return self.queryset.filter(name__iexact=name)


class ShipViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Ships to be viewed or edited.
    """
    queryset = Ship.objects.all()
    serializer_class = ShipSerializer


class ModuleSlotViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows ModuleSlotS to be viewed or edited.
    """
    queryset = ModuleSlot.objects.all()
    serializer_class = ModuleSlotSerializer


class HardpointMountViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Ships to be viewed or edited.
    """
    queryset = HardpointMount.objects.all()
    serializer_class = HardpointMountSerializer



class SystemViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Systems to be viewed or edited.
    """
    queryset = System.objects.all()
    serializer_class = SystemSerializer


class SystemBulkViewSet(BulkModelViewSet):
    """
    API endpoint that allows Systems to be bulk viewed or edited.
    """
    queryset = System.objects.all()
    serializer_class = SystemBulkSerializer
    # TODO control Bulk Deletes


class SystemIDViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Systems to be viewed or edited.
    """
    queryset = System.objects.all()
    serializer_class = SystemIDSerializer


class SecurityLevelViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Security Levels to be viewed or edited.
    """
    queryset = SecurityLevel.objects.all()
    serializer_class = SecurityLevelSerializer


class AllegianceViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Allegiances to be viewed or edited.
    """
    queryset = Allegiance.objects.all()
    serializer_class = AllegianceSerializer


class SysStateViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Security Levels to be viewed or edited.
    """
    queryset = State.objects.all()
    serializer_class = StateSerializer


class FactionViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Security Levels to be viewed or edited.
    """
    queryset = Faction.objects.all()
    serializer_class = FactionSerializer


class PowerViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Security Levels to be viewed or edited.
    """
    queryset = Power.objects.all()
    serializer_class = PowerSerializer


class GovernmentViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Security Levels to be viewed or edited.
    """
    queryset = Government.objects.all()
    serializer_class = GovernmentSerializer


class PowerStatesViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Security Levels to be viewed or edited.
    """
    queryset = PowerState.objects.all()
    serializer_class = PowerStateSerializer


class EconomyViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Security Levels to be viewed or edited.
    """
    queryset = Economy.objects.all()
    serializer_class = EconomySerializer
