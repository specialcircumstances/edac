from .models import CMDR, Ship, System
from .models import ModuleSlot, HardpointMount
from .models import SecurityLevel, Allegiance, State, Faction, Power
from .models import Government, PowerState, Economy
from rest_framework import serializers
from rest_framework_bulk import BulkSerializerMixin, BulkListSerializer

import serpy


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

class MyBulkSystemSerializer(serializers.ModelSerializer):
    class Meta:
        model = System

    def is_valid(self, raise_exception=False):
        print('Called my is_valid')
        assert not hasattr(self, 'restore_object'), (
            'Serializer `%s.%s` has old-style version 2 `.restore_object()` '
            'that is no longer compatible with REST framework 3. '
            'Use the new-style `.create()` and `.update()` methods instead.' %
            (self.__class__.__module__, self.__class__.__name__)
        )

        assert hasattr(self, 'initial_data'), (
            'Cannot call `.is_valid()` as no `data=` keyword argument was '
            'passed when instantiating the serializer instance.'
        )

        if not hasattr(self, '_validated_data'):
            print('I dont hasattr _validated_data')
            try:
                self._validated_data = self.run_validation(self.initial_data)
            except ValidationError as exc:
                self._validated_data = {}
                self._errors = exc.detail
            else:
                self._errors = {}

        if self._errors and raise_exception:
            raise ValidationError(self.errors)

        return not bool(self._errors)

    def run_validation(self, data=None):
        """
        We override the default `run_validation`, because the validation
        performed by validators and the `.validate()` method should
        be coerced into an error dictionary with a 'non_fields_error' key.
        """
        #(is_empty_value, data) = self.validate_empty_values(data)
        #if is_empty_value:
        #    return data

        value = self.to_internal_value(data)
        print('Value is: ')
        print('value')
        try:
            self.run_validators(value)
            value = self.validate(value)
            assert value is not None, '.validate() should return the validated data'
        except (ValidationError, DjangoValidationError) as exc:
            raise ValidationError(detail=get_validation_error_detail(exc))

        return value


class SystemSerpySerializer(serpy.Serializer):
    edsmid = serpy.Field()
    edsmdate = serpy.Field()
    name = serpy.Field()
    coord_x = serpy.Field()
    coord_y = serpy.Field()
    coord_z = serpy.Field()
    eddbid = serpy.Field()
    is_populated = serpy.Field()
    population = serpy.Field()
    simbad_ref = serpy.Field()
    needs_permit = serpy.Field()
    eddbdate = serpy.Field()
    reserve_type = serpy.Field()
    security = serpy.Field()
    state = serpy.Field()
    allegiance = serpy.Field()
    faction = serpy.Field()
    power = serpy.Field()
    government = serpy.Field()
    power_state = serpy.Field()
    primary_economy = serpy.Field()
    duphash = serpy.Field()

    def create(self, validated_data):
            return Comment(**validated_data)


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
