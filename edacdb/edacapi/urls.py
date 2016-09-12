from django.conf.urls import url, include
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r'cmdrs', views.CMDRViewSet)
router.register(r'cmdrbyname', views.CMDRByNameViewSet, {'name'})
router.register(r'ships', views.ShipViewSet)
router.register(r'systems', views.SystemViewSet)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]
