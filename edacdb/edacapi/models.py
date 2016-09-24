from django.db import models


# CMDR model


class CMDR(models.Model):
    # UID is combination (hash?) of cmdr name and if beta the game version
    # version is major (e.g. 2.2) beta is word
    # Should allow db to function properly (ish) in beta
    UID = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=32)
    version = models.CharField(max_length=32)
    credits = models.IntegerField(blank=True, default=0)
    loan = models.IntegerField(blank=True, default=0)
    insuranceknown = models.BooleanField(blank=True, default=False)
    insurance = models.IntegerField(blank=True, default=0)
    gamemode = models.CharField(max_length=32, blank=True, default='')
    group = models.CharField(max_length=32, blank=True, default='')
    # TODO Location
    # Rank
    rank_known = models.BooleanField(blank=True, default=False)
    rank_progress_known = models.BooleanField(blank=True, default=False)
    rank_combat = models.IntegerField(blank=True, default=0)
    rank_combat_progress = models.IntegerField(blank=True, default=0)
    rank_trade = models.IntegerField(blank=True, default=0)
    rank_trade_progress = models.IntegerField(blank=True, default=0)
    rank_explore = models.IntegerField(blank=True, default=0)
    rank_explore_progress = models.IntegerField(blank=True, default=0)
    rank_cqc = models.IntegerField(blank=True, default=0)
    rank_cqc_progress = models.IntegerField(blank=True, default=0)
    rank_federation = models.IntegerField(blank=True, default=0)
    rank_federation_progress = models.IntegerField(blank=True, default=0)
    rank_empire = models.IntegerField(blank=True, default=0)
    rank_empire_progress = models.IntegerField(blank=True, default=0)
    # Reputation
    rep_federation = models.IntegerField(blank=True, default=0)
    rep_empire = models.IntegerField(blank=True, default=0)
    rep_alliance = models.IntegerField(blank=True, default=0)
    rep_thargoid = models.IntegerField(blank=True, default=0)
    # Ships
    currentshipid = models.IntegerField(blank=True, null=True)
    # Ships in ships model lookup to CMDR
    # Missions in missions model lookup to CMDR
    # Engineers - not decided yet.

class Ship(models.Model):
    cmdr = models.ForeignKey(CMDR, on_delete=models.CASCADE)
    # UID is combination (hash? ) of CMDR UID and shipid, must be unique
    # This is to avoid duplicates within a commander
    UID = models.CharField(max_length=64, unique=True)
    shipid = models.IntegerField()
    shiptype = models.CharField(max_length=32)  # FDEV Symbol
    shipname = models.CharField(max_length=64,  blank=True, default=0)  # Pretty name
    # Save all the info to make DB API more useful in future
    manufacturer = models.CharField(max_length=64, blank=True, default='')
    cclass = models.IntegerField(blank=True, default=0)
    hullcost = models.IntegerField(blank=True, default=0)
    speed = models.IntegerField(blank=True, default=0)
    boost = models.IntegerField(blank=True, default=0)
    boostenergy = models.IntegerField(blank=True, default=0)
    agility = models.IntegerField(blank=True, default=0)
    baseshieldstrength = models.IntegerField(blank=True, default=0)
    basearmour = models.IntegerField(blank=True, default=0)
    masslock = models.IntegerField(blank=True, default=0)
    pipspeed = models.FloatField(blank=True, default=0)
    retailcost = models.IntegerField(blank=True, default=0)
    powerplant = models.CharField(max_length=64)  # FDEV Symbol
    thrusters = models.CharField(max_length=64)  # FDEV Symbol
    fsd = models.CharField(max_length=64)  # FDEV Symbol
    lifesupport = models.CharField(max_length=64)  # FDEV Symbol
    powerdist = models.CharField(max_length=64)  # FDEV Symbol
    sensors = models.CharField(max_length=64)  # FDEV Symbol
    fueltank = models.CharField(max_length=64)  # FDEV Symbol
    # Internal Slots will lookup to this object
    # Hardpoints will lookup to this object
    # Stats
    hullmass = models.IntegerField(blank=True, default=0)
    fuelcapacity = models.IntegerField(blank=True, default=0)
    cargocapacity = models.IntegerField(blank=True, default=0)
    ladenmass = models.IntegerField(blank=True, default=0)
    unladenmass = models.IntegerField(blank=True, default=0)
    unladenrange = models.IntegerField(blank=True, default=0)
    fulltankrange = models.IntegerField(blank=True, default=0)
    ladenrange = models.IntegerField(blank=True, default=0)


class ModuleSlot(models.Model):
    ship = models.ForeignKey(Ship, on_delete=models.CASCADE)
    slotsize = models.IntegerField()
    populated = models.BooleanField()
    attached = models.CharField(max_length=64, blank=True, default='')  # FDEV Symbol


class HardpointMount(models.Model):
    ship = models.ForeignKey(Ship, on_delete=models.CASCADE)
    slotsize = models.IntegerField()
    populated = models.BooleanField()
    attached = models.CharField(max_length=64, blank=True, default='')  # FDEV Symbol


class SecurityLevel(models.Model):
    # What we know about a security rating
    # {'Low': 1591, 'High': 1108, 'Medium': 2327}
    name = models.CharField(max_length=16, unique=True)
    # notes


class Allegiance(models.Model):
    # What we know about an Allegiance
    #{'Federation': 6374, 'None': 5, 'Alliance': 417, 'Empire': 5336,
    #'Independent': 7056}
    name = models.CharField(max_length=16, unique=True)
    # notes


class State(models.Model):
    # What we know about a system state type
    # {'War': 38, 'Bust': 6, 'Boom': 1075, 'Civil War': 86, 'Election': 13,
    # 'Civil Unrest': 26, 'Expansion': 117, 'Famine': 1, 'Retreat': 9,
    # 'None': 3258, 'Lockdown': 56, 'Outbreak': 2}
    name = models.CharField(max_length=32, unique=True)
    # notes


class Faction(models.Model):
    # What we know about a faction
    name = models.CharField(max_length=64, unique=True)
    reputaion = models.CharField(max_length=16, blank=True, default='NEUTRAL')
    # notes


class Power(models.Model):
    # What we know about a power
    # {'Edmund Mahon': 1422, 'None': 11204, 'Archon Delaine': 584,
    # 'Zemina Torval': 839, 'Zachary Hudson': 899, 'Li Yong-Rui': 772,
    # 'Pranav Antal': 610, 'Aisling Duval': 782, 'Denton Patreus': 710,
    # 'Felicia Winters': 635, 'Arissa Lavigny-Duval': 968}
    name = models.CharField(max_length=64, unique=True)
    reputaion = models.CharField(max_length=16, blank=True, default='NEUTRAL')
    # notes


class Government(models.Model):
    # What we know about a government type
    # {'Anarchy': 1442, 'Cooperative': 514, 'Prison Colony': 145,
    # 'Democracy': 3522, 'Communism': 391, 'Corporate': 6770, 'None': 2,
    # 'Dictatorship': 1686, 'Patronage': 2426, 'Feudal': 784,
    # 'Theocracy': 88, 'Confederacy': 1410}
    name = models.CharField(max_length=64, unique=True)
    # notes


class PowerState(models.Model):
    # What we know about a power_state
    # {'Control': 698, 'Exploited': 7531, 'Contested': 385}
    name = models.CharField(max_length=32, unique=True)
    # notes

class Economy(models.Model):
    # What we know about an economy
    #
    name = models.CharField(max_length=32, unique=True)
    # notes


class System(models.Model):
    # Have to allow for variations in data sources
    # And new discoveries
    # Base expected from EDSM
    edsmid = models.IntegerField(unique=True, blank=True, null=True)
    edsmdate = models.DateTimeField(null=True)  # Does not contain TZ
    name = models.CharField(max_length=64, blank=True, db_index=True)
    coord_x = models.FloatField(blank=True, default=0.0)
    coord_y = models.FloatField(blank=True, default=0.0)
    coord_z = models.FloatField(blank=True, default=0.0)
    # Augment with EDDB
    eddbid = models.IntegerField(unique=True, blank=True, null=True)
    is_populated = models.NullBooleanField(blank=True, null=True) # Y N ?
    population = models.IntegerField(blank=True, null=True)
    simbad_ref = models.CharField(max_length=96, blank=True, db_index=True, default='')
    needs_permit = models.NullBooleanField(blank=True, null=True) # Y N ?
    eddbdate = models.IntegerField(blank=True, null=True) # Why Integer???
    reserve_type = models.CharField(max_length=32, blank=True, default='')
    # e.g. either Pristine, Depleted or None = ''
    security = models.ForeignKey(SecurityLevel, models.SET_NULL, blank=True, null=True)
    # {'Low': 1591, 'High': 1108, 'Medium': 2327}
    state = models.ForeignKey(State, models.SET_NULL, blank=True, null=True)
    # {'War': 38, 'Bust': 6, 'Boom': 1075, 'Civil War': 86, 'Election': 13,
    # 'Civil Unrest': 26, 'Expansion': 117, 'Famine': 1, 'Retreat': 9,
    # 'None': 3258, 'Lockdown': 56, 'Outbreak': 2}
    allegiance = models.ForeignKey(Allegiance, models.SET_NULL, blank=True, null=True)
    #{'Federation': 6374, 'None': 5, 'Alliance': 417, 'Empire': 5336,
    #'Independent': 7056}
    faction = models.ForeignKey(Faction, models.SET_NULL, blank=True, null=True)
    # Too many to list here!
    power = models.ForeignKey(Power, models.SET_NULL, blank=True, null=True)
    # {'Edmund Mahon': 1422, 'None': 11204, 'Archon Delaine': 584,
    # 'Zemina Torval': 839, 'Zachary Hudson': 899, 'Li Yong-Rui': 772,
    # 'Pranav Antal': 610, 'Aisling Duval': 782, 'Denton Patreus': 710,
    # 'Felicia Winters': 635, 'Arissa Lavigny-Duval': 968}
    government = models.ForeignKey(Government, models.SET_NULL, blank=True, null=True)
    # {'Anarchy': 1442, 'Cooperative': 514, 'Prison Colony': 145,
    # 'Democracy': 3522, 'Communism': 391, 'Corporate': 6770, 'None': 2,
    # 'Dictatorship': 1686, 'Patronage': 2426, 'Feudal': 784,
    # 'Theocracy': 88, 'Confederacy': 1410}
    power_state = models.ForeignKey(PowerState, models.SET_NULL, blank=True, null=True)
    # {'Control': 698, 'Exploited': 7531, 'Contested': 385}
    primary_economy = models.ForeignKey(Economy, models.SET_NULL, blank=True, null=True)
    #
    duphash = models.CharField(max_length=8, blank=True, default='')


class AtmosType(models.Model):      # Overall Type
    eddbid = models.IntegerField(unique=True, blank=True, null=True)
    name = models.CharField(max_length=32, blank=True, default='')
''' 'atmosphere_type_name': [None,
                          'No atmosphere',
                          'Carbon dioxide',
                          'Suitable for water based life',
                          'Sulphur dioxide',
                          'Methane-rich',
                          'Methane',
                          'Argon-rich',
                          'Nitrogen',
                          'Water',
                          'Silicate vapour',
                          'Mateallic vapour',
                          'Ammonia and oxygen',
                          'Ammonia',
                          'Helium',
                          'Water-rich',
                          'Ammonia-rich',
                          'Neon-rich',
                          'Argon',
                          'Neon',
                          'Oxygen',
                          'Carbon dioxide-rich',
                          'Nitrogen-rich'],'''


class AtmosComponent(models.Model):
    eddbid = models.IntegerField(unique=True, blank=True, null=True)
    name = models.CharField(max_length=32, blank=True, default='')
'''{'atmosphere_component_name': ['Carbon dioxide',
                               'Nitrogen',
                               'Oxygen',
                               'Argon',
                               'Water',
                               'Hydrogen',
                               'Helium',
                               'Sulphur dioxide',
                               'Silicates',
                               'Methane',
                               'Ammonia',
                               'Iron',
                               'Neon'],'''



class BodyGroup(models.Model):
    eddbid = models.IntegerField(unique=True, blank=True, null=True)
    name = models.CharField(max_length=16, blank=True, default='')
    '''   'group_name': ['Star', 'Planet', 'Belt', 'Compact star'], '''


class BodyType(models.Model):
    eddbid = models.IntegerField(unique=True, blank=True, null=True)
    name = models.CharField(max_length=64, blank=True, default='')
    ''' 'type_name': [None,
               'Metal-rich body',
               'High metal content world',
               'Earth-like world',
               'Rocky body',
               'Class I gas giant',
               'Icy body',
               'Rocky ice world',
               'Supermassive black hole',
               'Class IV gas giant',
               'Black hole',
               'Water giant',
               'Class III gas giant',
               'Gas giant with ammonia-based life',
               'Gas giant with water-based life',
               'Water world',
               'Class V gas giant',
               'Ammonia world',
               'Class II gas giant',
               'Neutron star',
               'Helium-rich gas giant'],'''


class VolcanismType(models.Model):
    eddbid = models.IntegerField(unique=True, blank=True, null=True)
    name = models.CharField(max_length=64, blank=True, default='')
    ''' 'volcanism_type_name': [None,
                         'No volcanism',
                         'Silicate magma',
                         'Water magma',
                         'Water geysers',
                         'Methane magma',
                         'Iron magma',
                         'Silicate vapour geysers',
                         'Carbon dioxide geysers',
                         'Ammonia magma',
                         'Nitrogen magma']}'''


class RingType(models.Model):
    eddbid = models.IntegerField(unique=True, blank=True, null=True)
    name = models.CharField(max_length=64, blank=True, default='')
    ''' 'ring_type_name': ['Rocky', 'Icy', 'Metal Rich', 'Metallic', None],'''


class SolidType(models.Model):
    eddbid = models.IntegerField(unique=True, blank=True, null=True)
    name = models.CharField(max_length=64, blank=True, default='')
    ''' 'solid_component_name': ['Rock', 'Metal', 'Ice'],'''


class MaterialType(models.Model):
    eddbid = models.IntegerField(unique=True, blank=True, null=True)
    name = models.CharField(max_length=64, blank=True, default='')
    ''' 'material_name': ['Carbon',
                   'Iron',
                   'Nickel',
                   'Phosphorus',
                   'Sulphur',
                   'Chromium',
                   'Germanium',
                   'Manganese',
                   'Mercury',
                   'Tin',
                   'Ruthenium',
                   'Arsenic',
                   'Vanadium',
                   'Cadmium',
                   'Molybdenum',
                   'Antimony',
                   'Zirconium',
                   'Tungsten',
                   'Niobium',
                   'Selenium',
                   'Tellurium',
                   'Zinc',
                   'Yttrium',
                   'Polonium',
                   'Technetium'],'''


class Body(models.Model):
    eddbid = models.IntegerField(unique=True, blank=True, null=True)
    edsmid = models.IntegerField(unique=True, blank=True, null=True)
    #
    age = models.IntegerField(blank=True, null=True)
    arg_of_periapsis = models.FloatField(blank=True, null=True)
    # atmosphere_composition = lookup to here
    atmosphere_type_id = models.ForeignKey(AtmosType, models.SET_NULL, blank=True, null=True)
    axis_tilt = models.FloatField(blank=True, null=True)
    belt_moon_masses = models.FloatField(blank=True, null=True)
    catalogue_gliese_id = models.CharField(max_length=8, blank=True, default='')
    catalogue_hd_id = models.IntegerField(blank=True, null=True)
    catalogue_hipp_id = models.IntegerField(blank=True, null=True)
    distance_to_arrival = models.FloatField(blank=True, null=True)
    earth_masses = models.FloatField(blank=True, null=True)
    eg_id = models.IntegerField(blank=True, null=True)
    full_spectral_class = models.CharField(max_length=32, blank=True, default='') # TODO make property
    spectral_class = models.CharField(max_length=4, blank=True, default='')
    spectral_sub_class = models.IntegerField(blank=True, null=True)
    luminosity_class = models.CharField(max_length=3, blank=True, default='')
    luminosity_sub_class = models.CharField(max_length=6, blank=True, default='')
    # TODO make scoopable property based on spectral class
    gravity = models.FloatField(blank=True, null=True)
    group_id = models.ForeignKey(BodyGroup, models.SET_NULL, blank=True, null=True)
    is_main_star = models.NullBooleanField(blank=True, null=True) # Y N ?
    is_rotational_period_tidally_locked = models.NullBooleanField(blank=True, null=True) # Y N ?
    # materials - lookup to here
    name = models.CharField(db_index=True, max_length=64, blank=True, default='')
    orbital_eccentricity = models.FloatField(blank=True, null=True)
    orbital_inclination = models.FloatField(blank=True, null=True)
    orbital_period = models.FloatField(blank=True, null=True)
    radius = models.FloatField(blank=True, null=True)
    # rings Lookup to here
    rotational_period = models.FloatField(blank=True, null=True)
    semi_major_axis = models.FloatField(blank=True, null=True)
    solar_masses = models.FloatField(blank=True, null=True)
    solar_radius = models.FloatField(blank=True, null=True)
    # solid_composition lookup to here
    surface_pressure = models.FloatField(blank=True, null=True)
    surface_temperature = models.IntegerField(blank=True, null=True)
    system = models.ForeignKey(System, models.SET_NULL, blank=True, null=True)
    terraforming_state_id = models.IntegerField(blank=True, null=True)
    type_id = models.ForeignKey(BodyType, models.SET_NULL, blank=True, null=True)
    volcanism_type_id = models.ForeignKey(VolcanismType, models.SET_NULL, blank=True, null=True)
    eddb_created_at = models.IntegerField(blank=True, null=True)
    eddb_updated_at = models.IntegerField(blank=True, null=True)
    duphash = models.CharField(max_length=8, blank=True, default='')


class SolidComposition(models.Model):
    component = models.ForeignKey(SolidType, models.CASCADE)
    related_body = models.ForeignKey(Body, models.CASCADE)
    share = models.FloatField(blank=True, null=True)


class AtmosComposition(models.Model):
    component = models.ForeignKey(AtmosComponent, models.CASCADE)
    related_body = models.ForeignKey(Body, models.CASCADE)
    share = models.FloatField(blank=True, null=True)


class MaterialComposition(models.Model):
    component = models.ForeignKey(MaterialType, models.CASCADE)
    related_body = models.ForeignKey(Body, models.CASCADE)
    share = models.FloatField(blank=True, null=True)


class Ring(models.Model):
    eddbid = models.IntegerField(unique=True, blank=True, null=True)
    name = models.CharField(max_length=96, blank=True, default='')
    ring_inner_radius = models.IntegerField(blank=True, null=True)
    ring_mass = models.FloatField(blank=True, null=True)
    ring_outer_radius = models.IntegerField(blank=True, null=True)
    ring_type = models.ForeignKey(RingType, models.SET_NULL, blank=True, null=True)
    related_body = models.ForeignKey(Body, models.CASCADE, blank=True, null=True)
    semi_major_axis = models.FloatField(blank=True, null=True)
    eddb_created_at = models.IntegerField(blank=True, null=True)
    eddb_updated_at = models.IntegerField(blank=True, null=True)
    duphash = models.CharField(max_length=8, blank=True, default='')


#  Commodity Section
'''
{"id":1,"name":"Explosives","category_id":1,"average_price":261,"is_rare":0,
  "category":{"id":1,"name":"Chemicals"}},#
 '''


class CommodityCategory(models.Model):
    eddbid = models.IntegerField(unique=True, blank=True, null=True)
    name = models.CharField(max_length=64, blank=True, default='')


class Commodity(models.Model):
    eddbid = models.IntegerField(unique=True, blank=True, null=True)
    name = models.CharField(max_length=64, blank=True, default='')
    eddbname = models.CharField(max_length=64, blank=True, default='')
    category = models.ForeignKey(CommodityCategory, models.SET_NULL, blank=True, null=True)
    average_price = models.IntegerField(blank=True, null=True)
    is_rare = models.NullBooleanField(blank=True, null=True)   # Y N ?
    duphash = models.CharField(max_length=8, blank=True, default='')


#  Stations Section


class StationType(models.Model):
    eddbid = models.IntegerField(unique=True, blank=True, null=True)
    name = models.CharField(max_length=64, blank=True, default='')


class Station(models.Model):
    eddbid = models.IntegerField(unique=True, blank=True, null=True)
    name = models.CharField(max_length=64, blank=True, default='')
    system = models.ForeignKey(System, models.SET_NULL, blank=True, null=True)
    max_landing_pad_size = models.CharField(max_length=1, blank=True, default='')
    distance_to_star = models.IntegerField(blank=True, null=True)
    faction = models.ForeignKey(Faction, models.SET_NULL, blank=True, null=True)
    government = models.ForeignKey(Government, models.SET_NULL, blank=True, null=True)
    allegiance = models.ForeignKey(Allegiance, models.SET_NULL, blank=True, null=True)
    state = models.ForeignKey(State, models.SET_NULL, blank=True, null=True)
    stationtype = models.ForeignKey(StationType, models.SET_NULL, blank=True, null=True)
    has_blackmarket = models.NullBooleanField(blank=True, null=True)   # Y N ?
    has_market = models.NullBooleanField(blank=True, null=True)   # Y N ?
    has_refuel = models.NullBooleanField(blank=True, null=True)   # Y N ?
    has_repair = models.NullBooleanField(blank=True, null=True)   # Y N ?
    has_rearm = models.NullBooleanField(blank=True, null=True)   # Y N ?
    has_outfitting = models.NullBooleanField(blank=True, null=True)   # Y N ?
    has_shipyard = models.NullBooleanField(blank=True, null=True)   # Y N ?
    has_docking = models.NullBooleanField(blank=True, null=True)   # Y N ?
    has_commodities = models.NullBooleanField(blank=True, null=True)   # Y N ?
    is_planetary = models.NullBooleanField(blank=True, null=True)   # Y N ?
    eddb_updated_at = models.IntegerField(blank=True, null=True)
    eddb_shipyard_updated_at = models.IntegerField(blank=True, null=True)
    eddb_outfitting_updated_at = models.IntegerField(blank=True, null=True)
    eddb_market_updated_at = models.IntegerField(blank=True, null=True)
'''
{"id":14,"name":"Bounds Hub","system_id":773,"max_landing_pad_size":"L",
"distance_to_star":910,"faction":"Blood Brothers from Alrai",
"government":"Democracy","allegiance":"Federation","state":"None","type_id":3,
"type":"Coriolis Starport","has_blackmarket":0,"has_market":1,"has_refuel":1,
"has_repair":1,"has_rearm":1,"has_outfitting":1,"has_shipyard":1,
"has_docking":1,"has_commodities":1,
"import_commodities":["Cobalt","Bauxite","Rutile"],
"export_commodities":["Aluminium","Advanced Catalysers","Robotics"],
"prohibited_commodities":["Narcotics","Tobacco","Combat Stabilisers",
    "Imperial Slaves","Slaves","Battle Weapons","Toxic Waste"],
"economies":["High Tech","Refinery"],"updated_at":1461414377,
"shipyard_updated_at":1473600498,"outfitting_updated_at":1473610940,
"market_updated_at":1473610939,"is_planetary":0,
"selling_ships":["Adder","Cobra Mk. III","Diamondback Scout",
    "Federal Dropship","Hauler","Python","Sidewinder Mk. I",
    "Type-6 Transporter","Type-9 Heavy","Viper Mk III",
    "Asp Scout","Federal Corvette","Keelback",
    "Viper MK IV","Cobra MK IV"],
"selling_modules":[738,739,740,741,742,748,749,750,751,752,753,754,755,756,757,
758,759,760,761,762,763,764,765,766,etc,1549,1550]}
'''

class StationCommodity(models.Model):
    # Buy Sell Don't bring?
    commodity = models.ForeignKey(Commodity, models.CASCADE)
    station = models.ForeignKey(Station, models.CASCADE)
    imported = models.NullBooleanField(blank=True, null=True)   # Y N ?
    exported = models.NullBooleanField(blank=True, null=True)   # Y N ?
    prohibited = models.NullBooleanField(blank=True, null=True)   # Y N ?


class StationEconomy(models.Model):
    # Buy Sell Don't bring?
    economy = models.ForeignKey(Economy, models.CASCADE)
    station = models.ForeignKey(Station, models.CASCADE)


class StationShip(models.Model):
    # ship = models.ForeignKey(ShipType, models.CASCADE) TODO
    station = models.ForeignKey(Station, models.CASCADE)


class StationModule(models.Model):
    # module = models.ForeignKey(ModuleType, models.CASCADE) TODO
    station = models.ForeignKey(Station, models.CASCADE)
