import time

from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.db import transaction, connection
from django.db import IntegrityError, OperationalError
from django.db.models import Q
from django.http import HttpResponse
from django.forms.models import model_to_dict
import json
import cbor2 as cbor
import sys
import gc
import ast

from .models import CMDR, Ship, System
from .models import ModuleSlot, HardpointMount
from .models import SecurityLevel, Allegiance, State, Faction, Power
from .models import Government, PowerState, Economy
from .models import AtmosType, AtmosComponent
from .models import BodyGroup, BodyType, VolcanismType, RingType, SolidType
from .models import MaterialType, Body, SolidComposition, AtmosComposition
from .models import MaterialComposition, Ring, CommodityCategory, Commodity
from .models import StationType, Station, StationEconomy
from .models import StationShip, StationModule, ShipType, Module
from .models import ModuleMountType, ModuleGuidanceType, ModuleCategory
from .models import ModuleGroup, StationShip, StationModule, StationImport
from .models import StationExport, StationProhibited, MarketListing
from rest_framework import viewsets, views
from rest_framework import status
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
from .serializers import AtmosTypeSerializer, AtmosComponentSerializer
from .serializers import AtmosCompositionSerializer
from .serializers import BodyGroupSerializer, BodyTypeSerializer
from .serializers import VolcanismTypeSerializer, RingTypeSerializer
from .serializers import SolidTypeSerializer, MaterialTypeSerializer
from .serializers import BodySerializer, SolidCompositionSerializer
from .serializers import MaterialCompositionSerializer, RingSerializer
from .serializers import CommodityCategorySerializer, CommoditySerializer
from .serializers import StationTypeSerializer, StationSerializer
from .serializers import StationEconomySerializer
from .serializers import StationShipSerializer, StationModuleSerializer
from .serializers import AtmosCompositionBulkSerializer
from .serializers import SolidCompositionBulkSerializer
from .serializers import MaterialCompositionBulkSerializer
from .serializers import RingBulkSerializer, BodyBulkSerializer
from .serializers import StationBulkSerializer
from .serializers import StationEconomyBulkSerializer, ShipTypeSerializer
from .serializers import ModuleSerializer, ModuleMountTypeSerializer
from .serializers import ModuleGuidanceTypeSerializer, ModuleCategorySerializer
from .serializers import ModuleGroupSerializer, StationShipBulkSerializer
from .serializers import StationImportSerializer, StationExportSerializer
from .serializers import StationProhibitedSerializer, StationModuleBulkSerializer
from .serializers import StationImportBulkSerializer, StationExportBulkSerializer
from .serializers import StationProhibitedBulkSerializer, MarketListingSerializer
from .serializers import MarketListingBulkSerializer




class UpdatingBulkViewSet(BulkModelViewSet):
    """
    API endpoint that allows things to be bulk created or updated.
    """
    renderer_classes = (CBORRenderer, )
    parser_classes = (CBORParser, )
    # TODO control Bulk Deletes

    def create(self, request, *args, **kwargs):
        bulk = isinstance(request.data, list)
        if not bulk:
            return super(BulkCreateModelMixin, self).create(request, *args, **kwargs)
        elif len(request.data) == 0:
            return Response(status=status.HTTP_204_NO_CONTENT)
        elif 'station_id' in request.data[0]:   # Speed up
            table = self.queryset.model
            tablename = table._meta.db_table
            fields = list(request.data[0])      # Python 3 list of keys
            try:
                # Try raw TODO insert correct table and fields
                #print('Attempting direct inserts.')
                cursor = connection.cursor()
                queryp1 = ('INSERT INTO %s (%s, %s) VALUES'
                            % (tablename, fields[0], fields[1]))
                queryp2 = ''' (%s,%s) '''
                query = queryp1 + queryp2
                querylist = [(thisdict[fields[0]], thisdict[fields[1]]) for
                            thisdict in request.data
                            ]
                with transaction.atomic():
                    cursor.executemany(query, querylist)
                connection.commit()             # Not sure if this is required.
            except OperationalError:
                # Try again
                print('Operational Error: DB Locked?, retrying')
                time.sleep(2)
                with transaction.atomic():
                    cursor.executemany(query, querylist)
                connection.commit()
            except Exception as exc:
                print(exc)
                return Response(str(exc), status=status.HTTP_400_BAD_REQUEST)
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            serializer = self.get_serializer(data=request.data, many=True)
            serializer.is_valid(raise_exception=True)
            retrycount = 20
            while retrycount > 0:
                try:
                    self.perform_bulk_create(serializer)
                    break
                except OperationalError:
                    # Try again
                    print('Operational Error: DB Locked? Retrying...')
                    time.sleep(0.5)
                    retrycount -= 1
                except Exception as exc:
                    raise
                    print("Unexpected error: %s : %s" % (sys.exc_info()[0], sys.exc_info()[1]))
                    return HttpResponse(exc, status=400)
            return Response(len(serializer.data), status=status.HTTP_201_CREATED)

    def bulk_update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        if len(request.data) == 0:
            return Response(status=status.HTTP_204_NO_CONTENT)
        elif 'station_id' in request.data[0]:
            try:
                for thisdict in request.data:
                    thisdict['id'] = thisdict.pop('pk')     # Why why why ?????
                    #thisdict['module'] = Module.objects.get(pk=thisdict['module'])
                    #thisdict['station'] = Station.objects.get(pk=thisdict['station'])
            except Exception as exc:
                print(exc)
                return Response(exc, status=status.HTTP_400_BAD_REQUEST)
            retrycount = 20
            for thisitem in request.data:
                while retrycount > 0:
                    try:
                        StationModule.objects.filter(id=thisitem['id']).update(**thisitem)
                        break
                    except OperationalError:
                        # Try again
                        print('Operational Error: DB Locked?, retrying')
                        time.sleep(0.5)
                        retrycount -= 1
                    except Exception as exc:
                        print("Unexpected error: %s : %s" % (sys.exc_info()[0], sys.exc_info()[1]))
                        return HttpResponse(str(exc), status=400)
        else:
            # restrict the update to the filtered queryset
            serializer = self.get_serializer(
                self.filter_queryset(self.get_queryset()),
                data=request.data,
                many=True,
                partial=partial,
            )
            validated_data = []
            validation_errors = []
            results = []
            for item in request.data:
                item_serializer = self.get_serializer(
                    get_object_or_404(self.filter_queryset(self.get_queryset()),
                                      pk=item['id']),
                    data=item,
                    partial=partial,
                )
                if not item_serializer.is_valid():
                    validation_errors.append(item_serializer.errors)
                retrycount = 20
                result = None
                while retrycount > 0:
                    try:
                        result = self.get_queryset().filter(id=item['id']).update(
                                        **item_serializer.validated_data)
                        break
                    except OperationalError:
                        # Try again
                        print('Operational Error: DB Locked? Retrying...')
                        time.sleep(0.5)
                        retrycount -= 1
                    except Exception as exc:
                        print("Unexpected error: %s : %s" % (sys.exc_info()[0], sys.exc_info()[1]))
                        return HttpResponse(exc, status=400)
                # results.append(result)
            if validation_errors:
                raise ValidationError(validation_errors)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def allow_bulk_destroy(self, qs, filtered):
        # custom logic here
        print('HELLO allow_bulk_destroy')
        # Blog.objects.filter(pk__in=[1,4,7])
        # default checks if the qs was filtered
        # qs comes from self.get_queryset()
        # filtered comes from self.filter_queryset(qs)
        return True

    def bulk_destroy(self, request, *args, **kwargs):
        #qs = self.get_queryset()

        #filtered = self.filter_queryset(qs)
        #if not self.allow_bulk_destroy(qs, filtered):
        #    return Response(status=status.HTTP_400_BAD_REQUEST)
        pklist = request.data
        pklistlen = len(pklist)
        print('bulk_destroy got %d items to destroy' % len(pklist))
        #if pklistlen == 0:
        #    return Response(status=status.HTTP_400_BAD_REQUEST)
        # Need to limit the number of objects we try and destroy
        # at once.
        for pk in pklist:
            self.get_queryset().filter(id=pk).delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class CBORPackedItemView(views.APIView):
    """
    Optimised data dump of a Station join table.
    For use as a subclass.
    I've also added the capability to request of items by an arbitrary field
    ?field=fieldname&v=123(etc)
    """
    renderer_classes = (CBORRenderer, )
    parser_classes = (CBORParser, )

    def getpackedlist(self, request, table=None, fields=None):
        if table is None:
            table = self.queryset.model
            # print('Model is set to: %s' % table.__name__)
        if fields is None:
            fields = [f.name for f in table._meta.get_fields()
                      if f.concrete and (
                        not f.is_relation
                        or f.one_to_one
                        or (f.many_to_one and f.related_model)
                        )]
        # Check for filtering
        filterfield = request.GET.get('field')
        filtervalues = request.GET.getlist('v')
        myobjects = table.objects
        if (filterfield and filtervalues) is not None:
            # print('Making a filter...')
            myfilterqs = Q()
            for value in filtervalues:
                 myfilterqs = myfilterqs | Q(**{filterfield:value})
            myobjects = myobjects.filter(myfilterqs)
        count = myobjects.count()
        # print('I\'m counting %d objects' % count)
        offset = int(request.GET.get('offset', 0))
        limit = int(request.GET.get('limit', 9999)) + offset
        # items = myobjects.values(*fields)[offset:limit]
        items = myobjects.values_list(*fields)[offset:limit]
        # optimise by changing to a long list with headers and tuples
        list_items = []
        noofitems = len(items)
        if noofitems > 0:
                #list_headers = [header for header in sorted(items[0].keys())]
                list_headers = list(fields)
                #list_items = [
                #                [entry[header] for header in list_headers]
                #                 for entry in items]
                #listoflists = [ list(mytuple) for mytuple in items ]
                #flat_list = [item for sublist in listoflists for item in sublist]
                list_items = [len(list_headers)] + list_headers + list(items)
                # print(list_items[0:30])
        response = {
            'count': count,
            'results': list_items
        }
        # print(response)
        #print('CBOR Packer returning %d/%d items, tot. length %d'
        #      % (noofitems, count, len(list_items)))
        return response

    def get(self, request, format=None):
        response = self.getpackedlist(request)
        return Response(response, content_type='application/cbor')


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


class ShipTypeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Ship Types to be viewed or edited.
    """
    queryset = ShipType.objects.all()
    serializer_class = ShipTypeSerializer


class CBORShipTypeView(CBORPackedItemView):
    """
    Optimised data dump of the StationEconomy join table.
    """
    queryset = ShipType.objects.all()
    renderer_classes = (CBORRenderer, )
    parser_classes = (CBORParser, )


class ModuleMountTypeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Module Mount Types to be viewed or edited.
    """
    queryset = ModuleMountType.objects.all()
    serializer_class = ModuleMountTypeSerializer


class ModuleGuidanceTypeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Module Mount Types to be viewed or edited.
    """
    queryset = ModuleGuidanceType.objects.all()
    serializer_class = ModuleGuidanceTypeSerializer


class ModuleGroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows ModuleGroup to be viewed or edited.
    """
    queryset = ModuleGroup.objects.all()
    serializer_class = ModuleGroupSerializer


class CBORModuleGroupView(CBORPackedItemView):
    """
    Optimised data dump of the ModuleCategory join table.
    """
    queryset = ModuleGroup.objects.all()
    renderer_classes = (CBORRenderer, )
    parser_classes = (CBORParser, )


class ModuleCategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows ModuleCategory to be viewed or edited.
    """
    queryset = ModuleCategory.objects.all()
    serializer_class = ModuleCategorySerializer


class CBORModuleCategoryView(CBORPackedItemView):
    """
    Optimised data dump of the ModuleCategory join table.
    """
    queryset = ModuleCategory.objects.all()
    renderer_classes = (CBORRenderer, )
    parser_classes = (CBORParser, )


class ModuleViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Ships to be viewed or edited.
    """
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer


class CBORModuleView(CBORPackedItemView):
    """
    Optimised data dump of the StationEconomy join table.
    """
    queryset = Module.objects.all()
    renderer_classes = (CBORRenderer, )
    parser_classes = (CBORParser, )


class SuperStationModuleBulkViewSet(views.APIView):

    """
    A hidden API endpoint that allows Modules Stations joins
    to be bulk updated or created
    """
    queryset = StationModule.objects.all()
    renderer_classes = (CBORRenderer, )
    parser_classes = (CBORParser, )
    # serializer_class = StationModuleSerializer  # I don't think I actually use one.
    # TODO control Bulk Deletes

    # Stripped down for initial load events

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        print('StationModuleBulkViewSet update called.')
        return self.create(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        # print('StationModuleBulkViewSet create called.')
        # If we assume the data is good...
        # because we already checked it in EDACAPI Wrapper
        # It's a list of dict object - should be directly insertable in the DB
        # We just need to find the related objects and put them in the dict
        # print('Looking up related objects')
        # Load the related tables in full as there are lots+ objects in dict

        #
        # All wrapped in a try because there could be issues outside of our
        # control doing this...
        updating = False
        print('StationModuleBulkViewSet checking for update or create.')
        # Sample first item
        gc.collect()
        if 'pk' in request.data[0]:
            updating = True
        if updating is True:
            print('StationModuleBulkViewSet preloading modules.')
            #b1 = bool(Module.objects.all())
            #b2 = bool(Station.objects.all())
            try:
                for thisdict in request.data:
                    thisdict['id'] = thisdict.pop('pk')     # Why why why ?????
                    #thisdict['module'] = Module.objects.get(pk=thisdict['module'])
                    #thisdict['station'] = Station.objects.get(pk=thisdict['station'])
            except Exception as exc:
                print("Unexpected error: %s : %s" % (sys.exc_info()[0], sys.exc_info()[1]))
                print(str(exc))
                return Response(exc, status=status.HTTP_400_BAD_REQUEST)
            retrycount = 20
            for thisitem in request.data:
                while retrycount > 0:
                    try:
                        StationModule.objects.filter(id=thisitem['id']).update(**thisitem)
                        break
                    except OperationalError:
                        # Try again
                        print('Operational Error: DB Locked?, retrying')
                        time.sleep(0.5)
                        retrycount -= 1
                    except Exception as exc:
                        print("Unexpected error: %s : %s" % (sys.exc_info()[0], sys.exc_info()[1]))
                        return HttpResponse(str(exc), status=status.HTTP_400_BAD_REQUEST)
        else:
            try:
                # StationModule.objects.bulk_create([StationModule(**thisdict) for thisdict in request.data])
                # Try raw
                # print('Attempting direct inserts.')
                cursor = connection.cursor()
                query = ''' INSERT INTO edacapi_stationmodule
                            (station_id, module_id)
                            VALUES (%s,%s) '''
                querylist = [(thisdict['station_id'], thisdict['module_id']) for
                            thisdict in request.data
                            ]
                with transaction.atomic():
                    cursor.executemany(query, querylist)
                connection.commit()             # Not sure if this is required.
            except OperationalError:
                # Try again
                print('Operational Error: DB Locked?, retrying')
                time.sleep(2)
                with transaction.atomic():
                    cursor.executemany(query, querylist)
                connection.commit()
            except Exception as exc:
                print(exc)
                return Response(str(exc), status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SystemViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Systems to be viewed or edited.
    """
    queryset = System.objects.all()
    serializer_class = SystemSerializer

    def create(self, request, *args, **kwargs):
        return super(SystemViewSet, self).create(self, request, *args, **kwargs)


class SystemBulkCreateViewSet(views.APIView):

    """
    A hidden API endpoint that allows Systems to be bulk created reasonably
    quickly....
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
        '''
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
        '''
        idstrings = ['security', 'state', 'allegiance', 'faction', 'power',
                     'government', 'power_state', 'primary_economy']
        for thisdict in request.data:
            for idstring in idstrings:
                newid = idstring + '_id'
                thisdict[newid] = thisdict.pop(idstring)
        try:
            System.objects.bulk_create([System(**thisdict) for thisdict in request.data])
        except Exception as exc:
            print(exc)
            return Response(exc, status=status.HTTP_400_BAD_REQUEST)
        # print('Returning Response')
        # Should really put some stuff in here.
        return Response(status=status.HTTP_204_NO_CONTENT)


class SystemBulkUpdateViewSet(views.APIView):

    """
    A hidden API endpoint that allows Systems to be bulk updated.
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
        idstrings = ['security', 'state', 'allegiance', 'faction', 'power',
                     'government', 'power_state', 'primary_economy']
        for thisdict in request.data:
            thisdict['id'] = thisdict.pop('pk')
            for idstring in idstrings:
                newid = idstring + '_id'
                thisdict[newid] = thisdict.pop(idstring)
        # print('Doing Bulk Save')
        #System.objects.bulk_create([System(**thisdict) for thisdict in request.data])
        retrycount = 120
        for thisitem in request.data:
            while retrycount > 0:
                try:
                    System.objects.filter(id=thisitem['id']).update(**thisitem)
                    break
                except OperationalError:
                    # Try again
                    print('Operational Error: DB Locked?, retrying')
                    time.sleep(0.5)
                    retrycount -= 1
                except Exception as exc:
                    print("Unexpected error: %s : %s" % (sys.exc_info()[0], sys.exc_info()[1]))
                    return HttpResponse(exc, status=400)
        # print('Returning Response')
        # Should really put some stuff in here.
        return Response(status=status.HTTP_204_NO_CONTENT)


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
    A view that returns the count of active users in CBOR.
    """
    queryset = System.objects.all()
    renderer_classes = (CBORRenderer, )
    parser_classes = (CBORParser, )
    # content_negotiation_class = IgnoreClientContentNegotiation

    def get(self, request, format=None):
        systems = System.objects.values('pk', 'edsmid', 'eddbid', 'duphash')
        # optimise by changing to a long list.
        list_systems = []
        if len(systems) > 0:
            list_headers = [header for header in sorted(systems[0].keys())]
            list_systems = [
                            [entry[header] for header in list_headers]
                             for entry in systems]
            list_systems = [len(list_headers)] + list_headers + list_systems
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
        gc.collect()
        mycbor = cbor.dumps(list_systems)
        endtime = time.clock()
        timetaken = endtime - starttime
        print('%d systems in %d seconds' % (items, timetaken))
        print(sys.getsizeof(mycbor))
        # serializer = SystemIDSerializer(systems)
        return HttpResponse(mycbor, content_type='application/cbor; charset=utf-8')


class CBORSysIDView(CBORPackedItemView):
    """
    Optimised data dump of the ModuleCategory join table.
    """
    queryset = System.objects.all()
    renderer_classes = (CBORRenderer, )
    parser_classes = (CBORParser, )

    def get(self, request, format=None):
        fields = ('pk', 'edsmid', 'eddbid', 'duphash')
        response = self.getpackedlist(request, fields=fields)
        return Response(response, content_type='application/cbor')

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


class FactionBulkViewSet(UpdatingBulkViewSet):
    """
    API endpoint that allows Factions to be bulk viewed or edited.
    """
    queryset = Faction.objects.all()
    serializer_class = FactionBulkSerializer
    renderer_classes = (CBORRenderer, )
    parser_classes = (CBORParser, )
    # TODO control Bulk Deletes


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


class AtmosTypeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Ships to be viewed or edited.
    """
    queryset = AtmosType.objects.all()
    serializer_class = AtmosTypeSerializer


class AtmosComponentViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Ships to be viewed or edited.
    """
    queryset = AtmosComponent.objects.all()
    serializer_class = AtmosComponentSerializer


class AtmosCompositionViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Ships to be viewed or edited.
    """
    queryset = AtmosComposition.objects.all()
    serializer_class = AtmosCompositionSerializer


class AtmosCompositionBulkViewSet(UpdatingBulkViewSet):
    """
    API endpoint that allows Factions to be bulk viewed or edited.
    """
    queryset = AtmosComposition.objects.all()
    serializer_class = AtmosCompositionBulkSerializer
    renderer_classes = (CBORRenderer, )
    parser_classes = (CBORParser, )
    # TODO control Bulk Deletes


class CBORAtmosCompositionView(CBORPackedItemView):
    """
    Optimised data dump of the ModuleCategory join table.
    """
    queryset = AtmosComposition.objects.all()
    renderer_classes = (CBORRenderer, )
    parser_classes = (CBORParser, )


class BodyGroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Ships to be viewed or edited.
    """
    queryset = BodyGroup.objects.all()
    serializer_class = BodyGroupSerializer


class BodyTypeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Ships to be viewed or edited.
    """
    queryset = BodyType.objects.all()
    serializer_class = BodyTypeSerializer


class VolcanismTypeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Ships to be viewed or edited.
    """
    queryset = VolcanismType.objects.all()
    serializer_class = VolcanismTypeSerializer


class RingTypeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Ships to be viewed or edited.
    """
    queryset = RingType.objects.all()
    serializer_class = RingTypeSerializer


class SolidTypeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Ships to be viewed or edited.
    """
    queryset = SolidType.objects.all()
    serializer_class = SolidTypeSerializer


class MaterialTypeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Ships to be viewed or edited.
    """
    queryset = MaterialType.objects.all()
    serializer_class = MaterialTypeSerializer


class BodyViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Ships to be viewed or edited.
    """
    queryset = Body.objects.all()
    serializer_class = BodySerializer


class BodyBulkViewSet(UpdatingBulkViewSet):
    """
    API endpoint that allows Factions to be bulk viewed or edited.
    """
    queryset = Body.objects.all()
    serializer_class = BodyBulkSerializer
    renderer_classes = (CBORRenderer, )
    parser_classes = (CBORParser, )
    # TODO control Bulk Deletes


class CBORBodyView(CBORPackedItemView):
    """
    Optimised data dump of the Body join table.
    """
    queryset = Body.objects.all()
    renderer_classes = (CBORRenderer, )
    parser_classes = (CBORParser, )


class SolidCompositionViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Ships to be viewed or edited.
    """
    queryset = SolidComposition.objects.all()
    serializer_class = SolidCompositionSerializer


class SolidCompositionBulkViewSet(UpdatingBulkViewSet):
    """
    API endpoint that allows Factions to be bulk viewed or edited.
    """
    queryset = SolidComposition.objects.all()
    serializer_class = SolidCompositionBulkSerializer
    renderer_classes = (CBORRenderer, )
    parser_classes = (CBORParser, )
    # TODO control Bulk Deletes


class CBORSolidCompositionView(CBORPackedItemView):
    """
    Optimised data dump of the ModuleCategory join table.
    """
    queryset = SolidComposition.objects.all()
    renderer_classes = (CBORRenderer, )
    parser_classes = (CBORParser, )


class MaterialCompositionViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Ships to be viewed or edited.
    """
    queryset = MaterialComposition.objects.all()
    serializer_class = MaterialCompositionSerializer


class MaterialCompositionBulkViewSet(UpdatingBulkViewSet):
    """
    API endpoint that allows Factions to be bulk viewed or edited.
    """
    queryset = MaterialComposition.objects.all()
    serializer_class = MaterialCompositionBulkSerializer
    renderer_classes = (CBORRenderer, )
    parser_classes = (CBORParser, )
    # TODO control Bulk Deletes


class CBORMaterialCompositionView(CBORPackedItemView):
    """
    Optimised data dump of the ModuleCategory join table.
    """
    queryset = MaterialComposition.objects.all()
    renderer_classes = (CBORRenderer, )
    parser_classes = (CBORParser, )


class RingViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Ships to be viewed or edited.
    """
    queryset = Ring.objects.all()
    serializer_class = RingSerializer


class RingBulkViewSet(UpdatingBulkViewSet):
    """
    API endpoint that allows Factions to be bulk viewed or edited.
    """
    queryset = Ring.objects.all()
    serializer_class = RingBulkSerializer
    renderer_classes = (CBORRenderer, )
    parser_classes = (CBORParser, )
    # TODO control Bulk Deletes


class CBORRingView(CBORPackedItemView):
    """
    Optimised data dump of the StationEconomy join table.
    """
    queryset = Ring.objects.all()
    renderer_classes = (CBORRenderer, )
    parser_classes = (CBORParser, )


class CommodityCategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Ships to be viewed or edited.
    """
    queryset = CommodityCategory.objects.all()
    serializer_class = CommodityCategorySerializer


class CommodityViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Ships to be viewed or edited.
    """
    queryset = Commodity.objects.all()
    serializer_class = CommoditySerializer


class CBORCommodityView(CBORPackedItemView):
    """
    Optimised data dump of the Commodity table.
    """
    queryset = Commodity.objects.all()
    renderer_classes = (CBORRenderer, )
    parser_classes = (CBORParser, )


class StationTypeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Ships to be viewed or edited.
    """
    queryset = StationType.objects.all()
    serializer_class = StationTypeSerializer


class StationViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Ships to be viewed or edited.
    """
    queryset = Station.objects.all()
    serializer_class = StationSerializer


class StationBulkViewSet(UpdatingBulkViewSet):
    """
    API endpoint that allows Factions to be bulk viewed or edited.
    """
    queryset = Station.objects.all()
    serializer_class = StationBulkSerializer
    renderer_classes = (CBORRenderer, )
    parser_classes = (CBORParser, )
    # TODO control Bulk Deletes


class CBORStationView(CBORPackedItemView):
    """
    Optimised data dump of the Station table.
    """
    queryset = Station.objects.all()
    renderer_classes = (CBORRenderer, )
    parser_classes = (CBORParser, )


class StationImportViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Ships to be viewed or edited.
    """
    queryset = StationImport.objects.all()
    serializer_class = StationImportSerializer


class StationImportBulkViewSet(UpdatingBulkViewSet):
    """
    API endpoint that allows Factions to be bulk viewed or edited.
    """
    queryset = StationImport.objects.all()
    serializer_class = StationImportBulkSerializer
    renderer_classes = (CBORRenderer, )
    parser_classes = (CBORParser, )
    # TODO control Bulk Deletes


class CBORStationImportView(CBORPackedItemView):
    """
    Optimised data dump of the StationEconomy join table.
    """
    queryset = StationImport.objects.all()
    renderer_classes = (CBORRenderer, )
    parser_classes = (CBORParser, )


class StationExportViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Ships to be viewed or edited.
    """
    queryset = StationExport.objects.all()
    serializer_class = StationExportSerializer


class StationExportBulkViewSet(UpdatingBulkViewSet):
    """
    API endpoint that allows Factions to be bulk viewed or edited.
    """
    queryset = StationExport.objects.all()
    serializer_class = StationExportBulkSerializer
    renderer_classes = (CBORRenderer, )
    parser_classes = (CBORParser, )
    # TODO control Bulk Deletes


class CBORStationExportView(CBORPackedItemView):
    """
    Optimised data dump of the StationEconomy join table.
    """
    queryset = StationExport.objects.all()
    renderer_classes = (CBORRenderer, )
    parser_classes = (CBORParser, )


class StationProhibitedViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Ships to be viewed or edited.
    """
    queryset = StationProhibited.objects.all()
    serializer_class = StationProhibitedSerializer


class StationProhibitedBulkViewSet(UpdatingBulkViewSet):
    """
    API endpoint that allows Factions to be bulk viewed or edited.
    """
    queryset = StationProhibited.objects.all()
    serializer_class = StationProhibitedBulkSerializer
    renderer_classes = (CBORRenderer, )
    parser_classes = (CBORParser, )
    # TODO control Bulk Deletes


class CBORStationProhibitedView(CBORPackedItemView):
    """
    Optimised data dump of the StationEconomy join table.
    """
    queryset = StationProhibited.objects.all()
    renderer_classes = (CBORRenderer, )
    parser_classes = (CBORParser, )


class StationEconomyViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Ships to be viewed or edited.
    """
    queryset = StationEconomy.objects.all()
    serializer_class = StationEconomySerializer


class StationEconomyBulkViewSet(UpdatingBulkViewSet):
    """
    API endpoint that allows Factions to be bulk viewed or edited.
    """
    queryset = StationEconomy.objects.all()
    serializer_class = StationEconomyBulkSerializer
    renderer_classes = (CBORRenderer, )
    parser_classes = (CBORParser, )
    # TODO control Bulk Deletes


class CBORStationEconomyView(CBORPackedItemView):
    """
    Optimised data dump of the StationEconomy join table.
    """
    queryset = StationEconomy.objects.all()
    renderer_classes = (CBORRenderer, )
    parser_classes = (CBORParser, )


class StationShipViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Ships to be viewed or edited.
    """
    queryset = StationShip.objects.all()
    serializer_class = StationShipSerializer


class StationShipBulkViewSet(UpdatingBulkViewSet):
    """
    API endpoint that allows Factions to be bulk viewed or edited.
    """
    queryset = StationShip.objects.all()
    serializer_class = StationShipBulkSerializer
    renderer_classes = (CBORRenderer, )
    parser_classes = (CBORParser, )
    # TODO control Bulk Deletes


class CBORStationShipView(CBORPackedItemView):
    """
    Optimised data dump of the StationShip join table.
    """
    queryset = StationShip.objects.all()
    renderer_classes = (CBORRenderer, )
    parser_classes = (CBORParser, )


class StationModuleViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Ships to be viewed or edited.
    """
    queryset = StationModule.objects.all()
    serializer_class = StationModuleSerializer


class StationModuleBulkViewSet(UpdatingBulkViewSet):
    """
    API endpoint that allows Station Modules joins to be bulk viewed or edited.
    """
    queryset = StationModule.objects.all()
    serializer_class = StationModuleBulkSerializer
    renderer_classes = (CBORRenderer, )
    parser_classes = (CBORParser, )
    # TODO control Bulk Deletes


class CBORStationModuleView(CBORPackedItemView):
    """
    Optimised data dump of the StationModule join table.
    """
    queryset = StationModule.objects.all()
    renderer_classes = (CBORRenderer, )
    parser_classes = (CBORParser, )


class MarketListingViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows MarketListing to be viewed or edited.
    """
    queryset = MarketListing.objects.all()
    serializer_class = MarketListingSerializer


class MarketListingBulkViewSet(UpdatingBulkViewSet):
    """
    API endpoint that allows MarketListing joins to be bulk viewed or edited.
    """
    queryset = MarketListing.objects.all()
    serializer_class = MarketListingBulkSerializer
    renderer_classes = (CBORRenderer, )
    parser_classes = (CBORParser, )
    # TODO control Bulk Deletes


class CBORMarketListingView(CBORPackedItemView):
    """
    Optimised data dump of the MarketListing join table.
    """
    queryset = MarketListing.objects.all()
    renderer_classes = (CBORRenderer, )
    parser_classes = (CBORParser, )
