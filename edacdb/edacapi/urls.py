from django.conf.urls import url, include
from rest_framework import routers
from rest_framework_bulk.routes import BulkRouter
from . import views

router = routers.DefaultRouter(schema_title='EDACD API Schema',
        schema_url='.')
router.register(r'cmdrs', views.CMDRViewSet)
#router.register(r'cmdrbyname', views.CMDRByNameViewSet, {'name'})
router.register(r'ships', views.ShipViewSet)
router.register(r'moduleslots', views.ModuleSlotViewSet)
router.register(r'hardpointmounts', views.HardpointMountViewSet)
router.register(r'systems', views.SystemViewSet, 'systems')
router.register(r'systemids', views.SystemIDViewSet, 'systemids')
# router.register(r'fastsysids', views.FastSysIDListView, 'fastsysids')
router.register(r'securitylevels', views.SecurityLevelViewSet)
router.register(r'allegiances', views.AllegianceViewSet)
router.register(r'sysstates', views.SysStateViewSet)
router.register(r'factions', views.FactionViewSet)
router.register(r'governments', views.GovernmentViewSet)
router.register(r'powers', views.PowerViewSet)
router.register(r'powerstates', views.PowerStatesViewSet)
router.register(r'economies', views.EconomyViewSet)
router.register(r'atmostypes', views.AtmosTypeViewSet)
router.register(r'atmoscomponents', views.AtmosComponentViewSet)
router.register(r'atmoscomposition', views.AtmosCompositionViewSet)
router.register(r'bodygroups', views.BodyGroupViewSet)
router.register(r'bodytypes', views.BodyTypeViewSet)
router.register(r'volcanismtypes', views.VolcanismTypeViewSet)
router.register(r'ringtypes', views.RingTypeViewSet)
router.register(r'solidtypes', views.SolidTypeViewSet)
router.register(r'materials', views.MaterialTypeViewSet)
router.register(r'bodies', views.BodyViewSet)
router.register(r'solidcomposition', views.SolidCompositionViewSet)
router.register(r'materialcomposition', views.MaterialCompositionViewSet)
router.register(r'rings', views.RingViewSet)
router.register(r'commoditycats', views.CommodityCategoryViewSet)
router.register(r'commodities', views.CommodityViewSet)
router.register(r'stationtypes', views.StationTypeViewSet)
router.register(r'stations', views.StationViewSet)
router.register(r'stationimports', views.StationImportViewSet)
router.register(r'stationexports', views.StationExportViewSet)
router.register(r'stationprohibited', views.StationProhibitedViewSet)
router.register(r'stationeconomies', views.StationEconomyViewSet)
router.register(r'stationships', views.StationShipViewSet)
router.register(r'stationmodules', views.StationModuleViewSet)
router.register(r'shiptypes', views.ShipTypeViewSet)
router.register(r'modules', views.ModuleViewSet)
router.register(r'modulecats', views.ModuleCategoryViewSet)
router.register(r'modulegroups', views.ModuleGroupViewSet)
router.register(r'modguidances', views.ModuleGuidanceTypeViewSet)
router.register(r'modmounts', views.ModuleMountTypeViewSet)
router.register(r'marketlistings', views.MarketListingViewSet)


bulkrouter = BulkRouter(schema_title='EDACD API Bulk Schema',
                        schema_url='./bulk/')
# bulkrouter.register(r'systems', views.SystemBulkViewSet, 'bulksys')
bulkrouter.register(r'factions', views.FactionBulkViewSet, 'bulkfact')
bulkrouter.register(r'atmoscomposition',
                    views.AtmosCompositionBulkViewSet, 'bulkatmoscomposition')
bulkrouter.register(r'solidcomposition',
                    views.SolidCompositionBulkViewSet, 'bulksolidcomposition')
bulkrouter.register(r'materialcomposition',
                    views.MaterialCompositionBulkViewSet,
                    'bulkmaterialcomposition')
bulkrouter.register(r'rings', views.RingBulkViewSet, 'bulkrings')
bulkrouter.register(r'bodies', views.BodyBulkViewSet, 'bulkbodies')
bulkrouter.register(r'stations', views.StationBulkViewSet, 'bulkstations')
bulkrouter.register(r'stationimports', views.StationImportBulkViewSet,
                    'bulkstationimports')
bulkrouter.register(r'stationexports', views.StationExportBulkViewSet,
                    'bulkstationexports')
bulkrouter.register(r'stationprohibited', views.StationProhibitedBulkViewSet,
                    'bulkstationprohibited')
bulkrouter.register(r'stationeconomies', views.StationEconomyBulkViewSet,
                    'stationeconomies')
bulkrouter.register(r'stationships', views.StationShipBulkViewSet,
                    'stationships')
bulkrouter.register(r'stationmodules', views.StationModuleBulkViewSet,
                    'stationmodules')
bulkrouter.register(r'marketlistings', views.MarketListingBulkViewSet,
                    'marketlistings')

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^bulk/', include(bulkrouter.urls)),
    # url(r'^bulk/cbor/systemids/', views.FastSysIDListView.as_view()),
    url(r'^bulk/cbor/cborsystemids/', views.CBORSysIDListView.as_view()),
    url(r'^bulk/cbor/systemids/', views.CBORSysIDView.as_view()),
    url(r'^bulk/cbor/stationeconomies/', views.CBORStationEconomyView.as_view()),
    url(r'^bulk/cbor/atmoscomposition/', views.CBORAtmosCompositionView.as_view()),
    url(r'^bulk/cbor/solidcomposition/', views.CBORSolidCompositionView.as_view()),
    url(r'^bulk/cbor/materialcomposition/', views.CBORMaterialCompositionView.as_view()),
    url(r'^bulk/cbor/stationships/', views.CBORStationShipView.as_view()),
    url(r'^bulk/cbor/stationmodules/', views.CBORStationModuleView.as_view()),
    url(r'^bulk/cbor/stationimports/', views.CBORStationImportView.as_view()),
    url(r'^bulk/cbor/stationexports/', views.CBORStationExportView.as_view()),
    url(r'^bulk/cbor/stationprohibited/', views.CBORStationProhibitedView.as_view()),
    url(r'^bulk/cbor/bodies/', views.CBORBodyView.as_view()),
    url(r'^bulk/cbor/rings/', views.CBORRingView.as_view()),
    url(r'^bulk/cbor/commodities/', views.CBORCommodityView.as_view()),
    url(r'^bulk/cbor/modules/', views.CBORModuleView.as_view()),
    url(r'^bulk/cbor/modulecats/', views.CBORModuleCategoryView.as_view()),
    url(r'^bulk/cbor/modulegroups/', views.CBORModuleGroupView.as_view()),
    url(r'^bulk/cbor/shiptypes/', views.CBORShipTypeView.as_view()),
    url(r'^bulk/cbor/stations/', views.CBORStationView.as_view()),
    url(r'^bulk/cbor/marketlistings/', views.CBORMarketListingView.as_view()),
    url(r'^bulk/bcreatesystems/', views.SystemBulkCreateViewSet.as_view()),
    url(r'^bulk/bupdatesystems/', views.SystemBulkUpdateViewSet.as_view()),
    url(r'^bulk/bstationmodules/', views.SuperStationModuleBulkViewSet.as_view()),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]
