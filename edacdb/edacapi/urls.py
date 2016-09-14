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
#
router.register(r'systems', views.SystemViewSet)
router.register(r'systemids', views.SystemIDViewSet)
router.register(r'securitylevels', views.SecurityLevelViewSet)
router.register(r'allegiances', views.AllegianceViewSet)
router.register(r'sysstates', views.SysStateViewSet)
router.register(r'factions', views.FactionViewSet)
router.register(r'governments', views.GovernmentViewSet)
router.register(r'powers', views.PowerViewSet)
router.register(r'powerstates', views.PowerStatesViewSet)
router.register(r'economies', views.EconomyViewSet)
bulkrouter = BulkRouter(schema_title='EDACD API Bulk Schema',
        schema_url='.')
bulkrouter.register(r'systems', views.SystemBulkViewSet)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^bulk/', include(bulkrouter.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]
