from .models import CMDR, Ship, System
from rest_framework import serializers


class CMDRSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = CMDR


class ShipSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Ship


class SystemSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = System
