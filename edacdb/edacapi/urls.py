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
router.register(r'stationcommodities', views.StationCommodityViewSet)
router.register(r'stationeconomies', views.StationEconomyViewSet)
router.register(r'stationships', views.StationShipViewSet)
router.register(r'stationsmodules', views.StationModuleViewSet)


bulkrouter = BulkRouter(schema_title='EDACD API Bulk Schema', schema_url='./bulk/')
bulkrouter.register(r'systems', views.SystemBulkViewSet, 'bulksys')
bulkrouter.register(r'factions', views.FactionBulkViewSet, 'bulkfact')
bulkrouter.register(r'atmoscomposition',
                    views.AtmosCompositionBulkViewSet, 'bulkatmoscomposition')
bulkrouter.register(r'solidcomposition',
                    views.SolidCompositionBulkViewSet, 'bulksolidcomposition')
bulkrouter.register(r'materialcomposition',
                    views.MaterialCompositionBulkViewSet,
                    'bulkmaterialcomposition')

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^bulk/', include(bulkrouter.urls)),
    url(r'^bulk/cbor/systemids/', views.FastSysIDListView.as_view()),
    url(r'^bulk/cbor/cborsystemids/', views.CBORSysIDListView.as_view()),
    url(r'^bulk/bcreatesystems/', views.SystemBulkCreateViewSet.as_view()),
    url(r'^bulk/bupdatesystems/', views.SystemBulkUpdateViewSet.as_view()),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]
