import time

from django.shortcuts import render
from django.db import transaction
from django.http import HttpResponse
from django.forms.models import model_to_dict
import json
import cbor2 as cbor
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
from rest_framework_cbor.renderers import CBORRenderer
from rest_framework_cbor.parsers import CBORParser
from .serializers import CMDRSerializer, ShipSerializer, SystemSerializer
from .serializers import ModuleSlotSerializer, HardpointMountSerializer
from .serializers import SecurityLevelSerializer, AllegianceSerializer
from .serializers import StateSerializer, FactionSerializer, PowerSerializer
from .serializers import GovernmentSerializer, PowerStateSerializer
from .serializers import EconomySerializer, SystemIDSerializer
from .serializers import SystemBulkSerializer, FactionBulkSerializer
from .serializers import SystemSerpySerializer, MyBulkSystemSerializer






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

    def create(self, request, *args, **kwargs):
        return super(SystemViewSet, self).create(self, request, *args, **kwargs)


class SystemBulkViewSet(BulkModelViewSet):
    """
    API endpoint that allows Systems to be bulk viewed or edited.
    """
    queryset = System.objects.all()
    renderer_classes = (CBORRenderer, )
    parser_classes = (CBORParser, )
    serializer_class = SystemSerpySerializer
    # TODO control Bulk Deletes

    # Make the whole create atomic
    # @transaction.atomic
    def create(self, request, *args, **kwargs):
        # print(request.content_type)
        # return self.create(request, *args, **kwargs)
        return super(SystemBulkViewSet, self).create(request, *args, **kwargs)


class SerpySystemBulkViewSet(views.APIView):

    """
    API endpoint that allows Systems to be bulk viewed or edited.
    """
    queryset = System.objects.all()
    renderer_classes = (CBORRenderer, )
    parser_classes = (CBORParser, )
    serializer_class = MyBulkSystemSerializer
    # TODO control Bulk Deletes

    # Stripped down for initial load events

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        # If we assume the data is good...
        # because we already checked it in EDACAPI Wrapper
        # It's a list of dict object - should be directly insertable in the DB
        # We just need to find the related objects and put them in the dict
        # print('Looking up related objects')
        # Load the related tables in full as there are 8000+ objects in dict
        bool(SecurityLevel.objects.all())
        bool(State.objects.all())
        bool(Allegiance.objects.all())
        bool(Faction.objects.all())
        bool(Power.objects.all())
        bool(Government.objects.all())
        bool(PowerState.objects.all())
        bool(Economy.objects.all())
        #
        # All wrapped in a try because there could be issues outside of our
        # control doing this...
        try:
            for thisdict in request.data:
                if thisdict['security'] is not None:
                    thisdict['security'] = SecurityLevel.objects.get(pk=thisdict['security'])
                if thisdict['state'] is not None:
                    thisdict['state'] = State.objects.get(pk=thisdict['state'])
                if thisdict['allegiance'] is not None:
                    thisdict['allegiance'] = Allegiance.objects.get(pk=thisdict['allegiance'])
                if thisdict['faction'] is not None:
                    thisdict['faction'] = Faction.objects.get(pk=thisdict['faction'])
                if thisdict['power'] is not None:
                    thisdict['power'] = Power.objects.get(pk=thisdict['power'])
                if thisdict['government'] is not None:
                    thisdict['government'] = Government.objects.get(pk=thisdict['government'])
                if thisdict['power_state'] is not None:
                    thisdict['power_state'] = PowerState.objects.get(pk=thisdict['power_state'])
                if thisdict['primary_economy'] is not None:
                    thisdict['primary_economy'] = Economy.objects.get(pk=thisdict['primary_economy'])
        except Exception as exc:
            print(exc)
            return Response(exc, status=status.HTTP_400_BAD_REQUEST)
        # print('Doing Bulk Save')
        try:
            System.objects.bulk_create([System(**thisdict) for thisdict in request.data])
        except:
            print(exc)
            return Response(exc, status=status.HTTP_400_BAD_REQUEST)
        # print('Returning Response')
        # Should really put some stuff in here.
        return Response()


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


class CBORSysIDListView(views.APIView):
    """
    A view that returns the count of active users in JSON.
    """
    queryset = System.objects.all()
    renderer_classes = (CBORRenderer, )
    parser_classes = (CBORParser, )
    # content_negotiation_class = IgnoreClientContentNegotiation

    def get(self, request, format=None):
        starttime = time.time()
        systems = System.objects.values('pk', 'edsmid', 'eddbid', 'duphash')
        print(sys.getsizeof(systems))
        #print(len(systems))
        endtime = time.time()
        timetaken = endtime - starttime
        print('Got systems in %d seconds' % (timetaken))
        # optimise by changing to a long list.
        list_systems = []
        if len(systems) > 0:
            list_headers = [header for header in sorted(systems[0].keys())]
            list_systems = [
                            [entry[header] for header in list_headers]
                             for entry in systems]
            list_systems = [len(list_headers)] + list_headers + list_systems
            print(list_systems[0])
        endtime = time.time()
        timetaken = endtime - starttime
        print('Change to list of dicts in %d seconds' % (timetaken))
        print(sys.getsizeof(list_systems))
        return Response(list_systems, content_type='application/cbor')


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


class FactionBulkViewSet(BulkModelViewSet):
    """
    API endpoint that allows Factions to be bulk viewed or edited.
    """
    queryset = Faction.objects.all()
    serializer_class = FactionBulkSerializer
    renderer_classes = (CBORRenderer, )
    parser_classes = (CBORParser, )
    # TODO control Bulk Deletes

    # Make the whole create atomic
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        # return self.create(request, *args, **kwargs)
        return super(FactionBulkViewSet, self).post(self, request, *args, **kwargs)


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
