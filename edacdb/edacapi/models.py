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
