from .models import CMDR, Ship, System
from .models import ModuleSlot, HardpointMount
from .models import SecurityLevel, Allegiance, State, Faction, Power
from .models import Government, PowerState, Economy
from rest_framework import serializers
from rest_framework_bulk import BulkSerializerMixin, BulkListSerializer


class CMDRSerializer(serializers.ModelSerializer):
    class Meta:
        model = CMDR


class ShipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ship


class SystemSerializer(serializers.ModelSerializer):
    class Meta:
        model = System


class SystemBulkSerializer(BulkSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = System
        list_serializer_class = BulkListSerializer


class SystemIDSerializer(serializers.ModelSerializer):
    class Meta:
        model = System
        fields = ('pk', 'edsmid', 'eddbid', 'duphash')


class ModuleSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModuleSlot


class HardpointMountSerializer(serializers.ModelSerializer):
    class Meta:
        model = HardpointMount


class SecurityLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = SecurityLevel


class AllegianceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Allegiance


class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = State


class FactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Faction


class FactionBulkSerializer(BulkSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Faction
        list_serializer_class = BulkListSerializer


class PowerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Power


class GovernmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Government


class PowerStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PowerState


class EconomySerializer(serializers.ModelSerializer):
    class Meta:
        model = Economy
