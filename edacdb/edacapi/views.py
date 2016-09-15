import time

from django.shortcuts import render
from django.db import transaction
from django.http import HttpResponse
import json
import cbor
import sys

from .models import CMDR, Ship, System
from .models import ModuleSlot, HardpointMount
from .models import SecurityLevel, Allegiance, State, Faction, Power
from .models import Government, PowerState, Economy
from rest_framework import viewsets, views
from rest_framework_bulk import BulkModelViewSet
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.negotiation import BaseContentNegotiation
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

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        return super(SystemViewSet, self).create(self, request, *args, **kwargs)


class SystemBulkViewSet(BulkModelViewSet):
    """
    API endpoint that allows Systems to be bulk viewed or edited.
    """
    queryset = System.objects.all()
    serializer_class = SystemBulkSerializer
    # TODO control Bulk Deletes

    # Make the whole create atomic
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        # return self.create(request, *args, **kwargs)
        return super(SystemBulkViewSet, self).post(self, request, *args, **kwargs)


class SystemIDViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows Systems to be viewed or edited.
    """
    queryset = System.objects.only('pk', 'edsmid', 'eddbid', 'duphash')
    serializer_class = SystemIDSerializer


class IgnoreClientContentNegotiation(BaseContentNegotiation):
    def select_parser(self, request, parsers):
        """
        Select the first parser in the `.parser_classes` list.
        """
        return parsers[0]

    def select_renderer(self, request, renderers, format_suffix):
        """
        Select the first renderer in the `.renderer_classes` list.
        """
        return (renderers[0], renderers[0].media_type)


class FastSysIDListView(views.APIView):
    queryset = System.objects.all()
    permission_classes = []
    authentication_classes = []
    renderer_classes = [JSONRenderer]
    content_negotiation_class = IgnoreClientContentNegotiation

    def get(self, request):
        #systems = System.objects.only('pk', 'edsmid', 'eddbid', 'duphash')
        items = System.objects.count()
        print('There are %d items' % items)
        step = 8000
        offset = 0
        systems = []
        starttime = time.clock()
        #while offset < items:
        #    print(System.objects.values('pk', 'edsmid', 'eddbid', 'duphash')[offset:step])
        #    offset += step
        systems = System.objects.values('pk', 'edsmid', 'eddbid', 'duphash')
        list_systems = [entry for entry in systems]
        '''
        squeezed = []
        for mydict in list_systems:
            newdict = {}
            newdict['a'] = mydict['pk']
            newdict['b'] = mydict['edsmid']
            newdict['c'] = mydict['eddbid']
            newdict['d'] = mydict['duphash']
            squeezed.append(mydict)
        '''
        endtime = time.clock()
        timetaken = endtime - starttime
        print('%d systems in %d seconds' % (items, timetaken))
        print(sys.getsizeof(list_systems))
        #print(sys.getsizeof(squeezed))
        #myjson = json.dumps(squeezed)
        #print(sys.getsizeof(myjson))
        starttime = time.clock()
        mycbor = cbor.dumps(list_systems)
        endtime = time.clock()
        timetaken = endtime - starttime
        print('%d systems in %d seconds' % (items, timetaken))
        print(sys.getsizeof(mycbor))
        # serializer = SystemIDSerializer(systems)
        return HttpResponse(mycbor, content_type='application/cbor; charset=utf-8')


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
