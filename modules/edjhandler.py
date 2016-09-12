#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import pprint
from modules.pobjs import PrimaryObject, CMDR, Ship

DEBUG = True
ERROR = True
VERSION = '2.2 Beta'

def printdebug(mystring):
    if DEBUG is True:
        print("DEBUG edjhandler: %s" % mystring)

def printerror(mystring):
    if ERROR is True:
        print("ERROR edjhandler: %s" % mystring)

class JournalHandler(object):
    '''
    This takes a single line of JSON, decides which handler to use
    and then send the line of JSON to the handler
    It directly updates the primary objects via their methods
    it  may signal the need for further action.
    Uses a dictionary to map events to functions.
    This should make it easy to map new events into the system
    When created, it needs to be given the primary objects (well it will)
    '''

    # Our mapping handler dictionary and a method to update it.
    # Method just used in & by class definition
    handlerdict = {}
    def updatehdict(handlerdict, mykv):
        for key, value in mykv.items():
            if key in (handlerdict.keys()):
                printerror("Trying to add a duplicate handler %s" % key)
            else:
                handlerdict[key] = value
                printdebug("Adding unique handler %s" % key)

    # Special case handlers
    '''
    __________________________________________________________________________
    Fallback entry
    This handler is for events that we don't know about
    Ideally we'd capture them and log them for further investigation
    That's a TODO.
    '''
    def handlerFallback(self, myjson, mypobj):
        printdebug("Handler Called: Fallback")
        printerror("Unknown Event received: %s" % myjson['event'])
        return

    updatehdict(handlerdict, {'Fallback': handlerFallback})

    '''
    __________________________________________________________________________
    Heading entry
    The Heading record has a Json object with the following values:
    timestamp: the time in GMT, ISO 8601
    part: the file part number
    language: the language code
    gameversion: which version of the game produced the log
                                        (will indicate if beta)
    build: game build number

    Example:
    { "timestamp":"2016-07-22T10:20:01Z", "event":"fileheader", "part":1,
    "language”:”French/FR”, "gameversion":"2.2 Beta 1", "build":"r114123 " }
    (If the play session goes on a long time, and the journal gets very large,
    the file will be closed and a new file started with an increased
    part number)
    '''

    def handlerFileHeader(self, myjson, mypobj):
        printdebug("Handler Called: FileHeader")
        # TODO
        return

    updatehdict(handlerdict, {'Fileheader': handlerFileHeader})

    # Startup Handlers
    '''
    __________________________________________________________________________
    ClearSavedGame
    When written: If you should ever reset your game
    Parameters:
    Name: commander name

    Example:
    { "timestamp":"2016-06-10T14:32:03Z", "event":"ClearSavedGame",
     "Name":"HRC1" }
    '''


    def handlerClearSavedGame(self, myjson, mypobj):
        printdebug("Handler Called: ClearSavedGame")
        # TODO
        return

    updatehdict(handlerdict, {'ClearSavedGame': handlerClearSavedGame})
    '''
    __________________________________________________________________________
    NewCommander
    When written: Creating a new commander
    Parameters:
    Name: (new) commander name
    Package: selected starter package

    Example:
    { "timestamp":"2016-06-10T14:32:03Z", "event":"NewCommander",
     "Name":"HRC1", "Package":"ImperialBountyHunter" }
    '''

    def handlerNewCommander(self, myjson, mypobj):
        printdebug("Handler Called: NewCommander")
        # TODO
        return

    updatehdict(handlerdict, {'NewCommander': handlerNewCommander})

    '''
    __________________________________________________________________________
    LoadGame
    When written: at startup, when loading from main menu into game
    Parameters:
    Commander: commander name
    Ship: current ship type
    ShipID: ship id number
    StartLanded: true (only present if landed)
    StartDead:true (only present if starting dead: see “Resurrect”)
    GameMode: Open, Solo or Group
    Group: name of group (if in a group)
    Credits: current credit balance
    Loan: current loan

    Example:
    { "timestamp":"2016-06-10T14:32:03Z", "event":"LoadGame",
    "Commander":"HRC1",
    "Ship":"CobraMkIII", “ShipID”:1, “GameMode”:”Group”, “Group”:”Mobius”,
    “Credits”:600120, “Loan”:0  }
    '''

    def handlerLoadGame(self, myjson, mypobj):
        printdebug("Handler Called: LoadGame")
        cmdr = mypobj.cmdr
        # Essentials
        cmdr.setname(myjson['Commander'])   # TODO convert to loadcommander
        cmdr.setcredits(myjson['Credits'])
        if myjson['GameMode'] is 'Group':
            cmdr.setgamemodegroup(myjson['GameMode'], myjson['Group'])
        else:
            cmdr.setgamemode(myjson['GameMode'])
        # Optionals
        if 'StartLanded' in myjson:
            # TODO
            pass
        if 'StartDead' in myjson:
            # TODO
            pass
        cmdr.setcmdrisknown()
        #
        shipID = myjson['ShipID']
        shiptype = myjson['Ship']
        if shipID in mypobj.cmdr.ships.keys():
            # Great, we know about this ship already
            # TODO Verify ship type is correct
            printdebug('Ship is recognised. Loading from CMDR Records.')
            printdebug('ShipID: %s, Ship: %s' % (shipID, shiptype))
            mypobj.ship = mypobj.cmdr.ships[shipID]
            mypobj.cmdr.currentshipid = shipID  # not sure I really need this
            mypobj.cmdr.shipknown = True # Well sortof... perhaps EDAPI call?
        else:
            # We don't know about the ship, start with a new one
            # load out based on Coriolis defaults
            # We'll update as and when we can
            printdebug('Ship is not recognised. Creating new record.')
            mypobj.cmdr.ships[shipID] = Ship(mypobj, shipID, shiptype)
            printdebug('Linking to new record.')
            mypobj.ship = mypobj.cmdr.ships[shipID]
            printdebug('ShipID: %s, Ship: %s' % (shipID, shiptype))
            mypobj.cmdr.currentshipid = shipID  # not sure I really need this
            mypobj.cmdr.shipknown = True    # Well sortof... perhaps EDAPI call?

        return

    updatehdict(handlerdict, {'LoadGame': handlerLoadGame})

    '''
    __________________________________________________________________________
    Progress
    When written: at startup
    Parameters:
    Combat: percent progress to next rank
    Trade: 		“
    Explore: 	“
    Empire: 	“
    Federation: 	“
    CQC: 		“

    Example:
    { "timestamp":"2016-06-10T14:32:03Z", "event":"Progress", "Combat":77,
    "Trade":9, "Explore":93, "Empire":0, "Federation":0, "CQC":0 }
    '''

    def handlerProgress(self, myjson, mypobj):
        printdebug("Handler Called: Progress")
        cmdr = mypobj.cmdr
        # Order is important here.
        cmdr.setprogress(
            myjson['Combat'],
            myjson['Trade'],
            myjson['Explore'],
            myjson['Empire'],
            myjson['Federation'],
            myjson['CQC']
            )
        return

    updatehdict(handlerdict, {'Progress': handlerProgress})

    '''
    __________________________________________________________________________
    Rank
    When written: at startup
    Parameters:
    Combat: rank on scale 0-8
    Trade: rank on scale 0-8
    Explore: rank on scale 0-8
    Empire: military rank
    Federation: military rank
    CQC: rank on scale 0-8

    Example:
    { "timestamp":"2016-06-10T14:32:03Z", "event":"Rank", "Combat":2,
    "Trade":2, "Explore":5, "Empire":1, "Federation":3, "CQC":0 }
    '''
    def handlerRank(self, myjson, mypobj):
        printdebug("Handler Called: Rank")
        cmdr = mypobj.cmdr
        # Order is important here.
        cmdr.setranks(
            myjson['Combat'],
            myjson['Trade'],
            myjson['Explore'],
            myjson['Empire'],
            myjson['Federation'],
            myjson['CQC']
            )
        return

    updatehdict(handlerdict, {'Rank': handlerRank})

    # Travel Section

    '''
    __________________________________________________________________________
    Docked
    When written: when landing at landing pad in a space station, outpost,
    or surface settlement
    Parameters:
    StationName: name of station
    StationType: type of station
    StarSystem: name of system
    CockpitBreach:true (only if landing with breached cockpit)
    Faction: station’s controlling faction
    FactionState
    Allegiance
    Economy
    Government
    Security

    Example:
    { "timestamp":"2016-06-10T14:32:03Z", "event":"Docked",
    "StationName":"Kotov Refinery", "StationType":"Outpost",
    “StarSystem”:”Wolf 289”, "Faction":"Wolf 289 Gold Federal Industry",
    "FactionState":"CivilWar", “Allegiance”:”Federation”,
    “Economy”:”$economy_Extraction”, “Government”:”$government_Corporate”,
    "Security":”$SYSTEM_SECURITY_high_anarchy;” }
    '''
    def handlerDocked(self, myjson, mypobj):
        printdebug("Handler Called: Docked")
        return

    updatehdict(handlerdict, {'Docked': handlerDocked})

    '''
    __________________________________________________________________________
    DockingCancelled
    When written: when the player cancels a docking request
    Parameters:
    StationName: name of station

    '''
    def handlerDockingCancelled(self, myjson, mypobj):
        printdebug("Handler Called: DockingCancelled")
        return

    updatehdict(handlerdict, {'DockingCancelled': handlerDockingCancelled})

    '''
    __________________________________________________________________________
    DockingDenied
    When written: when the station denies a docking request
    Parameters:
    StationName: name of station
    Reason: reason for denial

    Reasons include: NoSpace, TooLarge, Hostile, Offences,
    Distance, ActiveFighter, NoReason
    '''

    def handlerDockingDenied(self, myjson, mypobj):
        printdebug("Handler Called: DockingDenied")
        return

    updatehdict(handlerdict, {'DockingDenied': handlerDockingDenied})

    '''
    __________________________________________________________________________
    DockingGranted
    When written: when a docking request is granted
    Parameters:
    StationName: name of station
    LandingPad: pad number
    '''

    def handlerDockingGranted(self, myjson, mypobj):
        printdebug("Handler Called: DockingGranted")
        return

    updatehdict(handlerdict, {'DockingGranted': handlerDockingGranted})

    '''
    __________________________________________________________________________
    DockingRequested
    When written: when the player requests docking at a station
    Parameters:
    StationName: name of station
    '''

    def handlerDockingRequested(self, myjson, mypobj):
        printdebug("Handler Called: DockingRequested")
        return

    updatehdict(handlerdict, {'DockingRequested': handlerDockingRequested})

    '''
    __________________________________________________________________________
    DockingTimeout
    When written: when a docking request has timed out
    Parameters:
    StationName: name of station
    '''

    def handlerDockingTimeout(self, myjson, mypobj):
        printdebug("Handler Called: DockingTimeout")
        return

    updatehdict(handlerdict, {'DockingTimeout': handlerDockingTimeout})

    '''
    __________________________________________________________________________
    FSDJump
    When written: when jumping from one star system to another
    Parameters:
    StarSystem: name of destination starsystem
    StarPos: star position, as a Json array [x, y, z], in light years
    Body: star’s body name
    JumpDist: distance jumped
    FuelUsed
    FuelLevel
    BoostUsed: whether FSD boost was used
    Faction: system controlling faction
    FactionState
    Allegiance
    Economy
    Government
    Security

    Example:
    { "timestamp":"2016-07-21T13:16:49Z", "event":"FSDJump",
    "StarSystem":"LP 98-132", "StarPos":[-26.781,37.031,-4.594],
    "Economy":"$economy_Extraction;", “Allegiance”:”Federation”,
    "Government":"$government_Anarchy;",
    "Security":”$SYSTEM_SECURITY_high_anarchy;”,
    "JumpDist":5.230, "FuelUsed":0.355614, "FuelLevel":12.079949,
    "Faction":"Brotherhood of LP 98-132", "FactionState":"Outbreak" }
    '''

    def handlerFSDJump(self, myjson, mypobj):
        printdebug("Handler Called: FSDJump")
        return

    updatehdict(handlerdict, {'FSDJump': handlerFSDJump})

    '''
    __________________________________________________________________________
    Liftoff
    When written: when taking off from planet surface
    Parameters:
    Latitude
    Longitude

    Example:
    { "timestamp":"2016-07-22T10:53:19Z", "event":"Liftoff",
    "Latitude":63.468872, "Longitude":157.599380 }
    '''

    def handlerLiftoff(self, myjson, mypobj):
        printdebug("Handler Called: Liftoff")
        return

    updatehdict(handlerdict, {'Liftoff': handlerLiftoff})

    '''
    __________________________________________________________________________
    Location
    When written: at startup, or when being resurrected at a station
    Parameters:
    StarSystem: name of destination starsystem
    StarPos: star position, as a Json array [x, y, z], in light years
    Body: star’s body name
    Docked: true (if docked)
    StationName: station name, (if docked)
    StationType: (if docked)
    Faction: star system controlling faction
    FactionState
    Allegiance
    Economy
    Government
    Security

    Example:
    { "timestamp":"2016-07-21T13:14:25Z", "event":"Location", "Docked":1,
    "StationName":"Azeban City", "StationType":"Coriolis",
    "StarSystem":"Eranin", "StarPos":[-22.844,36.531,-1.188],
    “Allegiance”:”Alliance”, "Economy":"$economy_Agri;",
    "Government":"$government_Communism;",
    "Security":$SYSTEM_SECURITY_medium;, "Faction":"Eranin Peoples Party" }
    '''

    def handlerLocation(self, myjson, mypobj):
        printdebug("Handler Called: Location")
        return

    updatehdict(handlerdict, {'Location': handlerLocation})

    '''
    __________________________________________________________________________
    SupercruiseEntry
    When written: entering supercruise from normal space
    Parameters:
    Starsystem

    Example:
    {"timestamp":"2016-06-10T14:32:03Z",  "event":"SupercruiseEntry",
    "StarSystem":"Yuetu" }
    '''

    def handlerSupercruiseEntry(self, myjson, mypobj):
        printdebug("Handler Called: SupercruiseEntry")
        return

    updatehdict(handlerdict, {'SupercruiseEntry': handlerSupercruiseEntry})

    '''
    __________________________________________________________________________
    SupercruiseExit
    When written: leaving supercruise for normal space
    Parameters:
    Starsystem
    Body

    Example:
    { "timestamp":"2016-06-10T14:32:03Z", "event":"SupercruiseExit",
    "StarSystem":"Yuetu", "Body":"Yuetu B" }
    '''

    def handlerSupercruiseExit(self, myjson, mypobj):
        printdebug("Handler Called: SupercruiseExit")
        return

    updatehdict(handlerdict, {'SupercruiseExit': handlerSupercruiseExit})

    '''
    __________________________________________________________________________
    Touchdown
    When written: landing on a planet surface
    Parameters:
    Latitude
    Longitude

    Example:
    { "timestamp":"2016-07-22T10:38:46Z", "event":"Touchdown",
    "Latitude":63.468872, "Longitude":157.599380 }
    '''

    def handlerTouchdown(self, myjson, mypobj):
        printdebug("Handler Called: Touchdown")
        return

    updatehdict(handlerdict, {'Touchdown': handlerTouchdown})

    '''
    __________________________________________________________________________
    Undocked
    When written: liftoff from a landing pad in a station,
    outpost or settlement
    Parameters:
    StationName: name of station

    Example:
    { "timestamp":"2016-06-10T14:32:03Z", "event":"Undocked",
    "StationName":"Long Sight Base" }
    '''

    def handlerUndocked(self, myjson, mypobj):
        printdebug("Handler Called: Undocked")
        return

    updatehdict(handlerdict, {'Undocked': handlerUndocked})

    # Combat Section

    '''
    __________________________________________________________________________
    Bounty
    When written: player is awarded a bounty for a kill
    Parameters:
    Faction: the faction awarding the bounty
    Reward: the reward value
    VictimFaction: the victim’s faction
    SharedWithOthers: whether shared with other players

    Example:
    { "timestamp":"2016-06-10T14:32:03Z", "event":"Bounty",
     "Faction":"$faction_Federation;", "Target":"Skimmer",
      "Reward":1000, "VictimFaction":"MMU" }
    '''

    def handlerBounty(self, myjson, mypobj):
        printdebug("Handler Called: Bounty")
        return

    updatehdict(handlerdict, {'Bounty': handlerBounty})

    '''
    __________________________________________________________________________
    CapShipBond
    When written: The player has been rewarded for a capital ship combat
    Parameters:
    Reward: value of award
    AwardingFaction
    VictimFaction

    '''

    def handlerCapShipBond(self, myjson, mypobj):
        printdebug("Handler Called: CapShipBond")
        return

    updatehdict(handlerdict, {'CapShipBond': handlerCapShipBond})

    '''
    __________________________________________________________________________
    Died
    When written: player was killed
    Parameters:
    KillerName
    KillerShip
    KillerRank

    Example:
    { "timestamp":"2016-06-10T14:32:03Z", "event":"Died",
     "KillerName":"$ShipName_Police_Independent;", "KillerShip":"viper",
      "KillerRank":"Deadly" }

    Died
    When written: player was killed by a wing
    Parameters:
    Killers: a JSON array of objects containing player name, ship, and rank

    Example:
    { "timestamp":"2016-06-10T14:32:03Z", "event":"Died",
     “Killers”:[ { “Name”:”Cmdr HRC1”, “Ship”:”Vulture”, ”Rank”:”Competent” },
      { “Name”:”Cmdr HRC2”, “Ship”:”Python”, ”Rank”:”Master” } ] }

    '''

    def handlerDied(self, myjson, mypobj):
        printdebug("Handler Called: Died")
        return

    updatehdict(handlerdict, {'Died': handlerDied})

    '''
    __________________________________________________________________________
    EscapeInterdiction
    When written: Player has escaped interdiction
    Parameters:
    Interdictor: interdicting pilot name
    IsPlayer: whether player or npc

    Example:
    {"timestamp":"2016-06-10T14:32:03Z",  "event":"EscapeInterdiction",
     “Interdictor”:”Hrc1”, “IsPlayer”:”true” }

    '''

    def handlerEscapeInterdiction(self, myjson, mypobj):
        printdebug("Handler Called: EscapeInterdiction")
        return

    updatehdict(handlerdict, {'EscapeInterdiction': handlerEscapeInterdiction})

    '''
    __________________________________________________________________________
    FactionKillBond
    When written: Player rewarded for taking part in a combat zone
    Parameters:
    Reward
    AwardingFaction
    VictimFaction

    Example:
    {"timestamp":"2016-06-10T14:32:03Z",  "event":"FactionKillBond",
    “Reward”: 500,
    "AwardingFaction":"Jarildekald Public Industry",
    “VictimFaction”: “Lencali Freedom Party” }

    '''

    def handlerFactionKillBond(self, myjson, mypobj):
        printdebug("Handler Called: FactionKillBond")
        return

    updatehdict(handlerdict, {'FactionKillBond': handlerFactionKillBond})

    '''
    __________________________________________________________________________
    HeatDamage
    When written: when taking damage due to overheating
    Parameters:none

    '''

    def handlerHeatDamage(self, myjson, mypobj):
        printdebug("Handler Called: HeatDamage")
        return

    updatehdict(handlerdict, {'HeatDamage': handlerHeatDamage})

    '''
    __________________________________________________________________________
    HeatWarning
    When written: when heat exceeds 100%
    Parameters: none

    '''

    def handlerHeatWarning(self, myjson, mypobj):
        printdebug("Handler Called: HeatWarning")
        return

    updatehdict(handlerdict, {'HeatWarning': handlerHeatWarning})

    '''
    __________________________________________________________________________
    HullDamage
    When written: when hull health drops below a threshold (20% steps)
    Parameters:
    Health
    Example:
    { "timestamp":"2016-07-25T14:46:23Z", "event":"HullDamage", "Health":0.798496 }
    { "timestamp":"2016-07-25T14:46:23Z", "event":"HullDamage", "Health":0.595611 }
    { "timestamp":"2016-07-25T14:46:23Z", "event":"HullDamage", "Health":0.392725 }
    { "timestamp":"2016-07-25T14:46:26Z", "event":"HullDamage", "Health":0.188219 }

    '''

    def handlerHullDamage(self, myjson, mypobj):
        printdebug("Handler Called: HullDamage")
        return

    updatehdict(handlerdict, {'HullDamage': handlerHullDamage})

    '''
    __________________________________________________________________________
    Interdicted
    When written: player was interdicted by player or npc
    Parameters:
    Submitted: true or false
    Interdictor: interdicting pilot name
    IsPlayer: whether player or npc
    CombatRank: if player
    Faction: if npc
    Power: if npc working for a power

    Example:
    { "timestamp":"2016-06-10T14:32:03Z", "event":"interdicted",
    “Submitted”:false, “Interdictor”:”Dread Pirate Roberts”,
    “IsPlayer”:false, “Faction”: "Timocani Purple Posse"  }

    '''

    def handlerInterdicted(self, myjson, mypobj):
        printdebug("Handler Called: Interdicted")
        return

    updatehdict(handlerdict, {'Interdicted': handlerInterdicted})

    '''
    __________________________________________________________________________
    Interdiction
    When written: player has (attempted to) interdict another player or npc
    Parameters:
    Success : true or false
    Interdicted: victim pilot name
    IsPlayer: whether player or npc
    CombatRank: if a player
    Faction: if an npc
    Power: if npc working for power

    Example:
    { "timestamp":"2016-06-10T14:32:03Z", "event":"interdiction",
    “Success”:true, “Interdicted”:”Fred Flintstone”, “IsPlayer”:”true”,
    “CombatRank”:5 }

    '''

    def handlerInterdiction(self, myjson, mypobj):
        printdebug("Handler Called: Interdiction")
        return

    updatehdict(handlerdict, {'Interdiction': handlerInterdiction})

    '''
    __________________________________________________________________________
    PVPKill
    When written: when this player has killed another player
    Parameters:
    Victim: name of victim
    CombatRank: victim’s rank in range 0..8

    '''

    def handlerPVPKill(self, myjson, mypobj):
        printdebug("Handler Called: PVPKill")
        return

    updatehdict(handlerdict, {'PVPKill': handlerInterdiction})

    '''
    __________________________________________________________________________
    ShieldState
    When written: when shields are disabled in combat, or recharged
    Parameters:
    ShieldsUp 0 when disabled, 1 when restored
    Examples:
    { "timestamp":"2016-07-25T14:45:48Z", "event":"ShieldState", "ShieldsUp":false }
    { "timestamp":"2016-07-25T14:46:36Z", "event":"ShieldState", "ShieldsUp":true }

    '''

    def handlerShieldState(self, myjson, mypobj):
        printdebug("Handler Called: ShieldState")
        return

    updatehdict(handlerdict, {'ShieldState': handlerShieldState})

    # Exploration handlers

    '''
    __________________________________________________________________________
    Scan
    When Written: detailed discovery scan of a star, planet or moon
    Parameters(star)
    Bodyname: name of body
    DistanceFromArrivalLS
    StarType: Stellar classification (for a star)
    StellarMass: mass as multiple of Sol’s mass
    Radius
    AbsoluteMagnitude
    OrbitalPeriod (seconds)
    RotationPeriod (seconds)
    Rings: [ array ] – if present

    Parameters(Planet/Moon)
    Bodyname: name of body
    DistanceFromArrivalLS
    TidalLock: 1 if tidally locked
    TerraformState: Terraformable, Terraforming, Terraformed, or null
    PlanetClass
    Atmosphere
    Volcanism
    SurfaceGravity
    SurfaceTemperature
    SurfacePressure
    Landable: true (if landable)
    Materials: JSON object with material names and percentage occurrence
    OrbitalPeriod (seconds)
    RotationPeriod (seconds)
    Rings: [ array of info ] – if rings present

    Rings properties
    Name
    RingClass
    MassMT – ie in megatons
    InnerRad
    OuterRad

    Examples:
    { "timestamp":"2016-07-25T10:02:38Z", "event":"Scan", "BodyName":"Alnitak",
    "DistanceFromArrivalLS":0.000000, "StarType":"O", "StellarMass":26.621094,
    "Radius":2305180672.000000, "AbsoluteMagnitude":-5.027969,
    "OrbitalPeriod":5755731.500000, "RotationPeriod":90114.937500 }

    { "timestamp":"2016-07-27T14:40:04Z", "event":"Scan",
    "BodyName":"HIP 4420 1", "DistanceFromArrivalLS":151.984283,
    "StarType":"Y", "StellarMass":0.019531, "Radius":54144908.000000,
    "AbsoluteMagnitude":20.959091, "OrbitalPeriod":4977483.500000,
    "RotationPeriod":67481.585938,
    "Rings":[ {
        "Name":"HIP 4420 1 A Ring",
        "RingClass":"eRingClass_Rocky", "MassMT":3.040e11,
        "InnerRad":8.933e7, "OuterRad":1.361e8 }, {
        "Name":"HIP 4420 1 B Ring", "RingClass":"eRingClass_MetalRich",
        "MassMT":1.355e13, "InnerRad":1.362e9, "OuterRad":6.796e8 } ] }
    '''

    def handlerScan(self, myjson, mypobj):
        printdebug("Handler Called: Scan")
        return

    updatehdict(handlerdict, {'Scan': handlerScan})

    '''
    __________________________________________________________________________
    MaterialCollected
    When Written: whenever materials are collected
    Parameters:
    Category: type of material (Raw/Encoded/Manufactured)
    Name: name of material

    Examples:
    { "timestamp":"2016-06-10T14:32:03Z", "event":"MaterialCollected",
    "Category":"Raw", "Name":"sulphur" }
    { "timestamp":"2016-06-10T14:32:03Z", "event":"MaterialCollected",
    "Category":"Encoded", "Name":"disruptedwakeechoes" }

    '''

    def handlerMaterialCollected(self, myjson, mypobj):
        printdebug("Handler Called: MaterialCollected")
        return

    updatehdict(handlerdict, {'MaterialCollected': handlerMaterialCollected})

    '''
    __________________________________________________________________________
    MaterialDiscarded
    When Written: if materials are discarded
    Parameters:
    Category
    Name
    Count

    Example:
    { "timestamp":"2016-06-10T14:32:03Z", "event":"MaterialDiscarded",
    "Category":"Raw", "Name":"sulphur", “Count”: 5 }

    '''

    def handlerMaterialDiscarded(self, myjson, mypobj):
        printdebug("Handler Called: MaterialDiscarded")
        return

    updatehdict(handlerdict, {'MaterialDiscarded': handlerMaterialDiscarded})

    '''
    __________________________________________________________________________
    MaterialDiscovered
    When Written: when a new material is discovered
    Parameters:
    Category
    Name
    DiscoveryNumber

    Example:
    { "timestamp":"2016-06-10T14:32:03Z", "event":"MaterialDiscovered",
    "Category":"Manufactured", "Name":"focuscrystals", "DiscoveryNumber":3 }

    '''

    def handlerMaterialDiscovered(self, myjson, mypobj):
        printdebug("Handler Called: MaterialDiscovered")
        return

    updatehdict(handlerdict, {'MaterialDiscovered': handlerMaterialDiscovered})

    '''
    __________________________________________________________________________
    BuyExplorationData
    When Written: when buying system data via the galaxy map
    Parameters:
    System
    Cost

    Example:
    { "timestamp":"2016-06-10T14:32:03Z", "event":"BuyExplorationData",
    "System":"Styx", "Cost":352 }

    '''

    def handlerBuyExplorationData(self, myjson, mypobj):
        printdebug("Handler Called: BuyExplorationData")
        return

    updatehdict(handlerdict, {'BuyExplorationData': handlerBuyExplorationData})

    '''
    __________________________________________________________________________
    SellExplorationData
    When Written: when selling exploration data in Cartographics
    Parameters:
    Systems: JSON array of system names
    Discovered: JSON array of discovered bodies
    BaseValue: value of systems
    Bonus: bonus for first discoveries

    Example:
    { "timestamp":"2016-06-10T14:32:03Z", "event":"SellExplorationData",
    "Systems":[ "HIP 78085", "Praea Euq NW-W b1-3" ],
    "Discovered":[ "HIP 78085 A", "Praea Euq NW-W b1-3",
        "Praea Euq NW-W b1-3 3 a", "Praea Euq NW-W b1-3 3" ],
    "BaseValue":10822, "Bonus":3959 }

    '''

    def handlerSellExplorationData(self, myjson, mypobj):
        printdebug("Handler Called: SellExplorationData")
        return

    updatehdict(handlerdict, {'SellExplorationData': handlerSellExplorationData})

    '''
    __________________________________________________________________________
    Screenshot
    When Written: when a screen snapshot is saved
    Parameters:
    Filename: filename of screenshot
    Width: size in pixels
    Height: size in pixels
    System: current star system
    Body: name of nearest body

    Example:
    { "timestamp":"2016-06-10T14:32:03Z", "event":"Screenshot",
    "Filename":"_Screenshots/Screenshot_0151.bmp",
    "Width":1600, "Height":900,
    "System":"Shinrarta Dezhra", "Body":"Founders World" }

    '''

    def handlerScreenshot(self, myjson, mypobj):
        printdebug("Handler Called: Screenshot")
        return

    updatehdict(handlerdict, {'Screenshot': handlerScreenshot})

    # Trade handlers

    '''
    __________________________________________________________________________
    BuyTradeData
    When Written: when buying trade data in the galaxy map
    Parameters:
    System: star system requested
    Cost: cost of data

    Example:
    { "timestamp":"2016-06-10T14:32:03Z", "event":"BuyTradeData",
    "System":"i Bootis", "Cost":100 }

    '''

    def handlerBuyTradeData(self, myjson, mypobj):
        printdebug("Handler Called: BuyTradeData")
        return

    updatehdict(handlerdict, {'BuyTradeData': handlerBuyTradeData})

    '''
    __________________________________________________________________________
    CollectCargo
    When Written: when scooping cargo from space or planet surface
    Parameters:
    Type: cargo type
    Stolen: whether stolen goods

    Example:
    { "timestamp":"2016-06-10T14:32:03Z", "event":"CollectCargo",
    "Type":"agriculturalmedicines", "Stolen":false }

    '''

    def handlerCollectCargo(self, myjson, mypobj):
        printdebug("Handler Called: CollectCargo")
        return

    updatehdict(handlerdict, {'CollectCargo': handlerCollectCargo})

    '''
    __________________________________________________________________________
    EjectCargo
    When Written:
    Parameters:
    Type: cargo type
    Count: number of units
    Abandoned: whether ‘abandoned’

    Example:
    { "timestamp":"2016-06-10T14:32:03Z", "event":"EjectCargo",
    "Type":"tobacco", "Count":1, "Abandoned":true }

    '''

    def handlerEjectCargo(self, myjson, mypobj):
        printdebug("Handler Called: EjectCargo")
        return

    updatehdict(handlerdict, {'EjectCargo': handlerEjectCargo})

    '''
    __________________________________________________________________________
    MarketBuy
    When Written: when purchasing goods in the market
    Parameters:
    Type: cargo type
    Count: number of units
    BuyPrice: cost per unit
    TotalCost: total cost

    Example:
    { "timestamp":"2016-06-10T14:32:03Z", "event":"MarketBuy",
    "Type":"foodcartridges", "Count":10, "BuyPrice":39, "TotalCost":390 }

    '''

    def handlerMarketBuy(self, myjson, mypobj):
        printdebug("Handler Called: MarketBuy")
        return

    updatehdict(handlerdict, {'MarketBuy': handlerMarketBuy})

    '''
    __________________________________________________________________________
    MarketSell
    When Written: when selling goods in the market
    Parameters:
    Type: cargo type
    Count: number of units
    SellPrice: price per unit
    TotalSale: total sale value
    AvgPricePaid: average price paid
    IllegalGoods: (not always present) whether goods are illegal here
    StolenGoods: (not always present) whether goods were stolen
    BlackMarket: (not always present) whether selling in a black market

    Examples:
    { "timestamp":"2016-06-10T14:32:03Z", "event":"MarketSell",
    "Type":"agriculturalmedicines", "Count":3, "SellPrice":1360,
    "TotalSale":4080, "AvgPricePaid":304 }

    { "event":"MarketSell", "Type":"mineraloil", "Count":9, "SellPrice":72,
    "TotalSale":648, "AvgPricePaid":0, "StolenGoods":true, "BlackMarket":true }

    '''

    def handlerMarketSell(self, myjson, mypobj):
        printdebug("Handler Called: MarketSell")
        return

    updatehdict(handlerdict, {'MarketSell': handlerMarketSell})

    '''
    __________________________________________________________________________
    MiningRefined
    When Written: when mining fragments are converted unto a unit of
    cargo by refinery
    Parameters:
    Type: cargo type

    Example:
    { "timestamp":"2016-06-10T14:32:03Z", "event":"MiningRefined",
    “Type:”Gold” }

    '''

    def handlerMiningRefined(self, myjson, mypobj):
        printdebug("Handler Called: MiningRefined")
        return

    updatehdict(handlerdict, {'MiningRefined': handlerMiningRefined})

    '''
    __________________________________________________________________________
    BuyAmmo
    When Written: when purchasing ammunition
    Parameters:
    Cost

    Example:
    { "timestamp":"2016-06-10T14:32:03Z", "event":"BuyAmmo", "Cost":80 }

    '''

    def handlerBuyAmmo(self, myjson, mypobj):
        printdebug("Handler Called: BuyAmmo")
        return

    updatehdict(handlerdict, {'BuyAmmo': handlerBuyAmmo})

    '''
    __________________________________________________________________________
    BuyDrones
    When Written: when purchasing drones
    Parameters:
    Type
    Count
    BuyPrice
    TotalCost

    Example:
     { "timestamp":"2016-06-10T14:32:03Z", "event":"BuyDrones",
     "Type":"Drones", "Count":2, "SellPrice":101, "TotalCost":202 }

    '''

    def handlerBuyDrones(self, myjson, mypobj):
        printdebug("Handler Called: BuyDrones")
        return

    updatehdict(handlerdict, {'BuyDrones': handlerBuyDrones})

    '''
    __________________________________________________________________________
    CommunityGoalJoin
    When Written: when signing up to a community goal
    Parameters:
    Name
    System

    '''

    def handlerCommunityGoalJoin(self, myjson, mypobj):
        printdebug("Handler Called: CommunityGoalJoin")
        return

    updatehdict(handlerdict, {'CommunityGoalJoin': handlerCommunityGoalJoin})

    # Crew

    '''
    __________________________________________________________________________
    CrewAssign
    When written: when changing the task assignment of a member of crew
    Parameters:
    Name
    Role

    Example:
    { "timestamp":"2016-08-09T08:45:31Z", "event":"CrewAssign",
    "Name":"Dannie Koller", "Role":"Active" }

    '''

    def handlerCrewAssign(self, myjson, mypobj):
        printdebug("Handler Called: CrewAssign")
        return

    updatehdict(handlerdict, {'CrewAssign': handlerCrewAssign})

    '''
    __________________________________________________________________________
    CrewFire
    When written: when dismissing a member of crew
    Parameters:
    Name

    Example:
    { "timestamp":"2016-08-09T08:46:11Z", "event":"CrewFire",
    "Name":"Whitney Pruitt-Munoz" }

    '''

    def handlerCrewFire(self, myjson, mypobj):
        printdebug("Handler Called: CrewFire")
        return

    updatehdict(handlerdict, {'CrewFire': handlerCrewFire})

    '''
    __________________________________________________________________________
    CrewHire
    When written: when engaging a new member of crew
    Parameters:
    Name
    Faction
    Cost
    Combat Rank

    Example:
    { "timestamp":"2016-08-09T08:46:29Z", "event":"CrewHire",
    "Name":"Margaret Parrish", "Faction":"The Dark Wheel", "Cost":15000,
    "CombatRank":1 }

    '''

    def handlerCrewHire(self, myjson, mypobj):
        printdebug("Handler Called: CrewHire")
        return

    updatehdict(handlerdict, {'CrewHire': handlerCrewHire})

    # Engineers

    '''
    __________________________________________________________________________
    EngineerApply
    When Written: when applying an engineer’s upgrade to a module
    Parameters:
    Engineer: name of engineer
    Blueprint: blueprint being applied
    Level: crafting level
    Override: whether overriding special effect

    Example:
    { "timestamp":"2016-06-10T14:32:03Z", "event":"EngineerApply",
    "Engineer":"Elvira Martuuk", "Blueprint":"ShieldGenerator_Reinforced",
    “Level”:1 }

    '''

    def handlerEngineerApply(self, myjson, mypobj):
        printdebug("Handler Called: EngineerApply")
        return

    updatehdict(handlerdict, {'EngineerApply': handlerEngineerApply})

    '''
    __________________________________________________________________________
    EngineerCraft
    When Written: when requesting an engineer upgrade
    Parameters:
    Engineer: name of engineer
    Blueprint: name of blueprint
    Level: crafting level
    Ingredients: JSON object with names and quantities of materials required

    Example:
    { "timestamp":"2016-06-10T14:32:03Z", "event":"EngineerCraft",
    "Engineer":"Elvira Martuuk", "Blueprint":"FSD_LongRange", “Level”:2,
    "Ingredients":{"praseodymium":1, "disruptedwakeechoes":3,
    "chemicalprocessors":2, "arsenic":2 } }

    '''

    def handlerEngineerCraft(self, myjson, mypobj):
        printdebug("Handler Called: EngineerCraft")
        return

    updatehdict(handlerdict, {'EngineerCraft': handlerEngineerCraft})

    '''
    __________________________________________________________________________
    EngineerProgress
    When Written: when a player increases their access to an engineer
    Parameters
    Engineer: name of engineer
    Rank: rank reached (when unlocked)
    Progress: progress stage (Invited/Acquainted/Unlocked/Barred)

    Examples:
    { "timestamp":"2016-06-10T14:32:03Z", "event":"EngineerProgress",
    "Progress":"Unlocked", "Engineer":"Elvira Martuuk" }
    { "timestamp":"2016-06-10T14:32:03Z", "event":"EngineerProgress",
    "Engineer":"Elvira Martuuk", "Rank":2 }

    '''

    def handlerEngineerProgress(self, myjson, mypobj):
        printdebug("Handler Called: EngineerProgress")
        return

    updatehdict(handlerdict, {'EngineerProgress': handlerEngineerProgress})

    # Other Station Services

    '''
    __________________________________________________________________________
    MissionAccepted
    When Written: when starting a mission
    Parameters:
    Name: name of mission
    Faction: faction offering mission
    MissionID
    Optional Parameters (depending on mission type)
    Commodity: commodity type
    Count: number required / to deliver
    Target: name of target
    TargetType: type of target
    TargetFaction: target’s faction
    Expiry: mission expiry time, in ISO 8601

    Example:
    { "timestamp":"2016-07-26T11:36:44Z", "event":"MissionAccepted",
    "Faction":"Tsu Network", "Name":"Mission_Collect", "MissionID":65343026,
    "Commodity":"$Fish_Name;", "Commodity_Localised":"Fish", "Count":2,
    "Expiry":"2016-07-27T15:56:23Z" }

    '''

    def handlerMissionAccepted(self, myjson, mypobj):
        printdebug("Handler Called: MissionAccepted")
        return

    updatehdict(handlerdict, {'MissionAccepted': handlerMissionAccepted})

    '''
    __________________________________________________________________________
    MissionCompleted
    When Written: when a mission is completed
    Parameters:
    Name: mission type
    Faction: faction name
    MissionID
    Optional parameters (depending on mission type)
    Commodity
    Count
    Target
    TargetType
    TargetFaction
    Reward: value of reward
    Donation: donation offered (for altruism missions)
    PermitsAwarded:[] (names of any permits awarded, as a JSON array)

    Example:
    { "timestamp":"2016-06-10T14:32:03Z", "event":"MissionCompleted",
    "Name":"Mission_Delivery_name", "MissionID":65343027,
    "Commodity":$Beer_Name;, "Faction":"Lencali Freedom Party",
    "Reward":76258 }

    '''

    def handlerMissionCompleted(self, myjson, mypobj):
        printdebug("Handler Called: MissionCompleted")
        return

    updatehdict(handlerdict, {'MissionCompleted': handlerMissionCompleted})

    '''
    __________________________________________________________________________
    MissionFailed
    When Written: when a mission has failed
    Parameters:
    Name: name of mission
    MissionID

    '''

    def handlerMissionFailed(self, myjson, mypobj):
        printdebug("Handler Called: MissionFailed")
        return

    updatehdict(handlerdict, {'MissionFailed': handlerMissionFailed})

    # Module stuff

    '''
    __________________________________________________________________________
    ModuleBuy
    When Written: when buying a module in outfitting
    Parameters:
    Slot: the outfitting slot
    BuyItem: the module being purchased
    BuyPrice: price paid
    Ship: the players ship
    ShipID
    If replacing an existing module:
    SellItem: item being sold
    SellPrice: sale price

    Example:
    { "timestamp":"2016-06-10T14:32:03Z", "event":"ModuleBuy",
    "Slot":"MediumHardpoint2", "SellItem":"hpt_pulselaser_fixed_medium",
    "SellPrice":0, "BuyItem":"hpt_multicannon_gimbal_medium",
    "BuyPrice":50018, "Ship":"cobramkiii",“ShipID”:1  }

    '''

    def handlerModuleBuy(self, myjson, mypobj):
        printdebug("Handler Called: ModuleBuy")
        # spec is different to example, work with it.
        if 'ShipID' in myjson:
            shipid = myjson['ShipID']
        else:
            shipid = mypobj.ship.shipid
        # end of that little fix
        # modulebuy(self, mypobj, slot, item, price, ship)
        mypobj.ship.modulebuy(
            mypobj,
            myjson['Slot'],
            myjson['BuyItem'],
            myjson['BuyPrice'],
            shipid,
            )
        return

    updatehdict(handlerdict, {'ModuleBuy': handlerModuleBuy})

    '''
    __________________________________________________________________________
    ModuleRetrieve
    When written: when fetching a previously stored module
    Parameters:
    Slot
    Ship
    ShipID
    RetrievedItem
    EngineerModifications: name of modification blueprint, if any
    SwapOutItem (if slot was not empty)
    Cost


    '''

    def handlerModuleRetrieve(self, myjson, mypobj):
        printdebug("Handler Called: ModuleRetrieve")
        return

    updatehdict(handlerdict, {'ModuleRetrieve': handlerModuleRetrieve})

    '''
    __________________________________________________________________________
    ModuleSell
    When Written: when selling a module in outfitting
    Parameters:
    Slot
    SellItem
    SellPrice
    Ship
    ShipID

    Example:
    { "timestamp":"2016-06-10T14:32:03Z", "event":"ModuleSell",
    "Slot":"Slot06_Size2", "SellItem":"int_cargorack_size1_class1",
    "SellPrice":877, "Ship":"asp", “ShipID”:1 }

    '''

    def handlerModuleSell(self, myjson, mypobj):
        printdebug("Handler Called: ModuleSell")
        return

    updatehdict(handlerdict, {'ModuleSell': handlerModuleSell})

    '''
    __________________________________________________________________________
    ModuleStore
    When written: when storing a module in Outfitting
    Parameters:
    Slot
    Ship
    ShipID
    StoredItem
    EngineerModifications: name of modification blueprint, if any
    ReplacementItem (if a core module)
    Cost (if any)

    '''

    def handlerModuleStore(self, myjson, mypobj):
        printdebug("Handler Called: ModuleStore")
        return

    updatehdict(handlerdict, {'ModuleStore': handlerModuleStore})

    '''
    __________________________________________________________________________
    ModuleSwap
    When Written: when moving a module to a different slot on the ship
    Parameters:
    FromSlot
    ToSlot
    FromItem
    ToItem
    Ship
    ShipID

    Examples:
    { "timestamp":"2016-06-10T14:32:03Z", "event":"ModuleSwap",
    "FromSlot":"MediumHardpoint1", "ToSlot":"MediumHardpoint2",
    "FromItem":"hpt_pulselaser_fixed_medium",
    "ToItem":"hpt_multicannon_gimbal_medium",
    "Ship":"cobramkiii", “ShipID”:1  }

    { "timestamp":"2016-06-10T14:32:03Z",
    "event":"ModuleSwap", "FromSlot":"SmallHardpoint2",
    "ToSlot":"SmallHardpoint1",
    "FromItem":"hpt_pulselaserburst_fixed_small_scatter",
    "ToItem":"Null", "Ship":"cobramkiii", “ShipID”:1  }

    '''

    def handlerModuleSwap(self, myjson, mypobj):
        printdebug("Handler Called: ModuleSwap")
        # spec is different to example, work with it.
        if 'ShipID' in myjson:
            shipid = myjson['ShipID']
        else:
            shipid = mypobj.ship.shipid
        # end of that little fix
        mypobj.ship.moduleswap(
            mypobj,
            myjson['FromSlot'],
            myjson['ToSlot'],
            myjson['FromItem'],
            myjson['ToItem'],
            shipid,
            )
        return

    updatehdict(handlerdict, {'ModuleSwap': handlerModuleSwap})

    # Money stuff

    '''
    __________________________________________________________________________
    PayFines
    When Written: when paying fines
    Parameters:
    Amount: (total amount paid , including any broker fee)
    BrokerPercentage (present if paid via a Broker)

    Example:
    { "timestamp":"2016-06-10T14:32:03Z", "event":"PayFines", "Amount":1791 }

    '''

    def handlerPayFines(self, myjson, mypobj):
        printdebug("Handler Called: PayFines")
        return

    updatehdict(handlerdict, {'PayFines': handlerPayFines})

    '''
    __________________________________________________________________________
    PayLegacyFines
    When Written: when paying legacy fines
    Parameters:
    Amount (total amount paid, including any broker fee)
    BrokerPercentage (present if paid through a broker)

    '''

    def handlerPayLegacyFines(self, myjson, mypobj):
        printdebug("Handler Called: PayLegacyFines")
        return

    updatehdict(handlerdict, {'PayLegacyFines': handlerPayLegacyFines})

    '''
    __________________________________________________________________________
    RedeemVoucher
    When Written: when claiming payment for combat bounties and bonds
    Parameters:
    Type
    Amount: (Net amount received, after any broker fee)
    BrokerPercenentage (if redeemed through a broker)

    Example:
    { "timestamp":"2016-06-10T14:32:03Z", "event":"RedeemVoucher",
    "Type":"bounty", "Amount":1000 }
    '''

    def handlerRedeemVoucher(self, myjson, mypobj):
        printdebug("Handler Called: RedeemVoucher")
        return

    updatehdict(handlerdict, {'RedeemVoucher': handlerRedeemVoucher})

    '''
    __________________________________________________________________________
    RefuelAll
    When Written: when refuelling (full tank)
    Parameters:
    Cost: cost of fuel
    Amount: tons of fuel purchased

    Example:
    { "timestamp":"2016-06-10T14:32:03Z", "event":"RefuelAll",
    "Cost":317, "Amount":6.322901 }
    '''

    def handlerRefuelAll(self, myjson, mypobj):
        printdebug("Handler Called: RefuelAll")
        return

    updatehdict(handlerdict, {'RefuelAll': handlerRefuelAll})

    '''
    __________________________________________________________________________
    RefuelPartial
    When Written: when refuelling (10%)
    Parameters:
    Cost: cost of fuel
    Amount: tons of fuel purchased

    Example:
    { "timestamp":"2016-06-10T14:32:03Z", "event":"RefuelPartial",
    "Cost":83, "Amount":1.649000 }

    '''

    def handlerRefuelPartial(self, myjson, mypobj):
        printdebug("Handler Called: RefuelPartial")
        return

    updatehdict(handlerdict, {'RefuelPartial': handlerRefuelPartial})

    '''
    __________________________________________________________________________
    Repair
    When Written: when repairing the ship
    Parameters:
    Item: all, wear, hull, paint, or name of module
    Cost: cost of repair

    Example:
    { "timestamp":"2016-06-10T14:32:03Z", "event":"Repair",
    "Item":"int_powerplant_size3_class5", "Cost":1100 }

    '''

    def handlerRepair(self, myjson, mypobj):
        printdebug("Handler Called: Repair")
        return

    updatehdict(handlerdict, {'Repair': handlerRepair})

    '''
    __________________________________________________________________________
    RestockVehicle
    When Written: when purchasing an SRV or Fighter
    Parameters:
    Type: type of vehicle being purchased (SRV or fighter model)
    Loadout: variant
    Cost: purchase cost
    Count: number of vehicles purchased

    Example:
    { "timestamp":"2016-06-10T14:32:03Z", "event":"RestockVehicle",
    “Type”:”SRV”, "Loadout":"starter", "Cost":1030, “Count”:1 }

    '''

    def handlerRestockVehicle(self, myjson, mypobj):
        printdebug("Handler Called: RestockVehicle")
        return

    updatehdict(handlerdict, {'RestockVehicle': handlerRestockVehicle})

    '''
    __________________________________________________________________________
    SellDrones
    When Written: when selling unwanted drones back to the market
    Parameters:
    Type
    Count
    SellPrice
    TotalSale

    Example:
    { "timestamp":"2016-06-10T14:32:03Z", "event":"SellDrones",
    "Type":"Drones", "Count":1, "SellPrice":91, "TotalSale":91 }

    '''

    def handlerSellDrones(self, myjson, mypobj):
        printdebug("Handler Called: SellDrones")
        return

    updatehdict(handlerdict, {'SellDrones': handlerSellDrones})

    # Shipyard stuff

    '''
    __________________________________________________________________________
    ShipyardBuy
    When Written: when buying a new ship in the shipyard
    Parameters:
    ShipType: ship being purchased
    ShipPrice: purchase cost
    StoreOldShip: (if storing old ship) ship type being stored
    StoreShipID
    SellOldShip: (if selling current ship) ship type being sold
    SellShipID
    SellPrice: (if selling current ship) ship sale price

    Note: the new ship’s ShipID will be logged in a separate event
     after the purchase (see ShipardNew)

    Example:
    { "timestamp":"2016-07-21T14:36:38Z", "event":"ShipyardBuy",
    "ShipType":"hauler", "ShipPrice":46262, "StoreOldShip":"SideWinder",
    "StoreShipID":2 }

    '''

    def handlerShipyardBuy(self, myjson, mypobj):
        printdebug("Handler Called: ShipyardBuy")
        return

    updatehdict(handlerdict, {'ShipyardBuy': handlerShipyardBuy})

    '''
    __________________________________________________________________________
    ShipyardNew
    When written: after a new ship has been purchased
    Parameters:
    ShipType
    ShipID
    Example:
    { "timestamp":"2016-07-21T14:36:38Z", "event":"ShipyardNew",
    "ShipType":"hauler", "ShipID":4 }

    '''

    def handlerShipyardNew(self, myjson, mypobj):
        printdebug("Handler Called: ShipyardNew")
        return

    updatehdict(handlerdict, {'ShipyardNew': handlerShipyardNew})

    '''
    __________________________________________________________________________
    ShipyardSell
    When Written: when selling a ship stored in the shipyard
    Parameters:
    ShipType: type of ship being sold
    SellShipID
    ShipPrice: sale price
    System: (if ship is in another system) name of system

    Example:
    { "timestamp":"2016-07-21T15:12:19Z", "event":"ShipyardSell",
    "ShipType":"Adder", "SellShipID":6, "ShipPrice":79027, "System":"Eranin" }

    '''

    def handlerShipyardSell(self, myjson, mypobj):
        printdebug("Handler Called: ShipyardSell")
        return

    updatehdict(handlerdict, {'ShipyardSell': handlerShipyardSell})

    '''
    __________________________________________________________________________
    ShipyardTransfer
    When Written: when requesting a ship at another station be
    transported to this station
    Parameters:
    ShipType: type of ship
    ShipID
    System: where it is
    Distance: how far away
    TransferPrice: cost of transfer

    Example:
    { "timestamp":"2016-07-21T15:19:49Z", "event":"ShipyardTransfer",
    "ShipType":"SideWinder", "ShipID":7, "System":"Eranin",
    "Distance":85.639145, "TransferPrice":580 }

    '''

    def handlerShipyardTransfer(self, myjson, mypobj):
        printdebug("Handler Called: ShipyardTransfer")
        return

    updatehdict(handlerdict, {'ShipyardTransfer': handlerShipyardTransfer})

    '''
    __________________________________________________________________________
    ShipyardSwap
    When Written: when switching to another ship already stored at this station
    Parameters:
    ShipType: type of ship being switched to
    ShipID
    StoreOldShip: (if storing old ship) type of ship being stored
    StoreShipID
    SellOldShip: (if selling old ship) type of ship being sold
    SellShipID

    Example
    { "timestamp":"2016-07-21T14:36:06Z", "event":"ShipyardSwap",
    "ShipType":"sidewinder", "ShipID":10, "StoreOldShip":"Asp",
    "StoreShipID":2 }

    '''

    def handlerShipyardSwap(self, myjson, mypobj):
        printdebug("Handler Called: ShipyardSwap")
        # Should just be able to load as if new ship.
        shipID = myjson['ShipID']
        shiptype = myjson['ShipType']
        if shipID in mypobj.cmdr.ships.keys():
            # Great, we know about this ship already
            # TODO Verify ship type is correct
            printdebug('Ship is recognised. Loading from CMDR Records.')
            printdebug('ShipID: %s, Ship: %s' % (shipID, shiptype))
            mypobj.ship = mypobj.cmdr.ships[shipID]
            mypobj.cmdr.currentshipid = shipID  # not sure I really need this
            mypobj.cmdr.shipknown = True # Well sortof... perhaps EDAPI call?
        else:
            # We don't know about the ship, start with a new one
            # load out based on Coriolis defaults
            # We'll update as and when we can
            printdebug('Ship is not recognised. Creating new record.')
            mypobj.cmdr.ships[shipID] = Ship(mypobj, shipID, shiptype)
            printdebug('Linking to new record.')
            mypobj.ship = mypobj.cmdr.ships[shipID]
            printdebug('ShipID: %s, Ship: %s' % (shipID, shiptype))
            mypobj.cmdr.currentshipid = shipID  # not sure I really need this
            mypobj.cmdr.shipknown = True    # Well sortof... perhaps EDAPI call?


        return

    updatehdict(handlerdict, {'ShipyardSwap': handlerShipyardSwap})

    # Powerplay

    '''
    __________________________________________________________________________
    PowerplayCollect
    When written: when collecting powerplay commodities for delivery
    Parameters:
    Power: name of power
    Type: type of commodity
    Count: number of units

    Example:
    { "timestamp":"2016-06-10T14:32:03Z", "event":"PowerplayCollect",
    "Power":"Li Yong-Rui", "Type":"siriusfranchisepackage", "Count":10 }

    '''

    def handlerPowerplayCollect(self, myjson, mypobj):
        printdebug("Handler Called: PowerplayCollect")
        return

    updatehdict(handlerdict, {'PowerplayCollect': handlerPowerplayCollect})

    '''
    __________________________________________________________________________
    PowerplayDefect
    When written: when a player defects from one power to another
    Parameters:
    FromPower
    ToPower

    Example:
    { "timestamp":"2016-06-10T14:32:03Z", "event":"PowerplayDefect",
    "FromPower":"Zachary Hudson", "ToPower":"Li Yong-Rui" }

    '''

    def handlerPowerplayDefect(self, myjson, mypobj):
        printdebug("Handler Called: PowerplayDefect")
        return

    updatehdict(handlerdict, {'PowerplayDefect': handlerPowerplayDefect})

    '''
    __________________________________________________________________________
    PowerplayDeliver
    When written: when delivering powerplay commodities
    Parameters:
    Power
    Type
    Count

    Example:
    { "timestamp":"2016-06-10T14:32:03Z", "event":"PowerplayDeliver",
    "Power":"Li Yong-Rui", "Type":"siriusfranchisepackage", "Count":10 }

    '''

    def handlerPowerplayDeliver(self, myjson, mypobj):
        printdebug("Handler Called: PowerplayDeliver")
        return

    updatehdict(handlerdict, {'PowerplayDeliver': handlerPowerplayDeliver})

    '''
    __________________________________________________________________________
    PowerplayFastTrack
    When written: when paying to fast-track allocation of commodities
    Parameters:
    Power
    Cost

    '''

    def handlerPowerplayFastTrack(self, myjson, mypobj):
        printdebug("Handler Called: PowerplayFastTrack")
        return

    updatehdict(handlerdict, {'PowerplayFastTrack': handlerPowerplayFastTrack})

    '''
    __________________________________________________________________________
    PowerplayJoin
    When written: when joining up with a power
    Parameters:
    Power

    Example:
    { "timestamp":"2016-06-10T14:32:03Z", "event":"PowerplayJoin",
    "Power":"Zachary Hudson" }

    '''

    def handlerPowerplayJoin(self, myjson, mypobj):
        printdebug("Handler Called: PowerplayJoin")
        return

    updatehdict(handlerdict, {'PowerplayJoin': handlerPowerplayJoin})

    '''
    __________________________________________________________________________
    PowerplayLeave
    When written: when leaving a power
    Parameters:
    Power

    Example:
    { "timestamp":"2016-06-10T14:32:03Z", "event":"PowerplayLeave",
    "Power":"Li Yong-Rui" }

    '''

    def handlerPowerplayLeave(self, myjson, mypobj):
        printdebug("Handler Called: PowerplayLeave")
        return

    updatehdict(handlerdict, {'PowerplayLeave': handlerPowerplayLeave})

    '''
    __________________________________________________________________________
    PowerplaySalary
    When written: when receiving salary payment from a power
    Parameters:
    Power
    Amount

    '''

    def handlerPowerplaySalary(self, myjson, mypobj):
        printdebug("Handler Called: PowerplaySalary")
        return

    updatehdict(handlerdict, {'PowerplaySalary': handlerPowerplaySalary})

    '''
    __________________________________________________________________________
    PowerplayVote
    When written: when voting for a system expansion
    Parameters:
    Power
    Votes
    System

    '''

    def handlerPowerplayVote(self, myjson, mypobj):
        printdebug("Handler Called: PowerplayVote")
        return

    updatehdict(handlerdict, {'PowerplayVote': handlerPowerplayVote})

    '''
    __________________________________________________________________________
    PowerplayVoucher
    When written: when receiving payment for powerplay combat
    Parameters:
    Power
    Systems:[name,name]

    '''

    def handlerPowerplayVoucher(self, myjson, mypobj):
        printdebug("Handler Called: PowerplayVoucher")
        return

    updatehdict(handlerdict, {'PowerplayVoucher': handlerPowerplayVoucher})

    # Other events

    '''
    __________________________________________________________________________
    CockpitBreached
    When written: when cockpit canopy is breached
    Parameters: none
    Example:
    { "timestamp":"2016-06-10T14:32:03Z", "event":"CockpitBreached" }

    '''

    def handlerCockpitBreached(self, myjson, mypobj):
        printdebug("Handler Called: CockpitBreached")
        return

    updatehdict(handlerdict, {'CockpitBreached': handlerCockpitBreached})

    '''
    __________________________________________________________________________
    CommitCrime
    When written: when a crime is recorded against the player
    Parameters:
    CrimeType
    Faction
    Optional parameters (depending on crime)
    Victim
    Fine
    Bounty

    Examples:
    { "timestamp":"2016-06-10T14:32:03Z", "event":"CommitCrime",
    "CrimeType":"assault", "Faction":"The Pilots Federation",
    "Victim":"Potapinski", "Bounty":210 }
    { "timestamp":"2016-06-10T14:32:03Z", "event":"CommitCrime",
    "CrimeType":"fireInNoFireZone", "Faction":"Jarildekald Public Industry",
    "Fine":100 }

    '''

    def handlerCommitCrime(self, myjson, mypobj):
        printdebug("Handler Called: CommitCrime")
        return

    updatehdict(handlerdict, {'CommitCrime': handlerCommitCrime})

    '''
    __________________________________________________________________________
    Continued
    When written: if the journal file grows to 500k lines, we write this event,
    close the file, and start a new one
    Parameters:
    Part: next part number

    '''

    def handlerContinued(self, myjson, mypobj):
        printdebug("Handler Called: Continued")
        return

    updatehdict(handlerdict, {'Continued': handlerContinued})

    '''
    __________________________________________________________________________
    DatalinkScan
    When written: when scanning a data link
    Parameters:
    Message: message from data link


    '''

    def handlerDatalinkScan(self, myjson, mypobj):
        printdebug("Handler Called: DatalinkScan")
        return

    updatehdict(handlerdict, {'DatalinkScan': handlerDatalinkScan})

    '''
    __________________________________________________________________________
    DatalinkVoucher
    When written: when scanning a datalink generates a reward
    Parameters:
    Reward: value in credits
    VictimFaction
    PayeeFaction

    '''

    def handlerDatalinkVoucher(self, myjson, mypobj):
        printdebug("Handler Called: DatalinkVoucher")
        return

    updatehdict(handlerdict, {'DatalinkVoucher': handlerDatalinkVoucher})

    '''
    __________________________________________________________________________
    DataScanned
    When written: when scanning some types of data links
    Parameters:
    Type

    Type will typically be one of “DataLink”, “DataPoint”, “ListeningPost”,
    “AbandonedDataLog”, “WreckedShip”, etc

    '''

    def handlerDataScanned(self, myjson, mypobj):
        printdebug("Handler Called: DataScanned")
        return

    updatehdict(handlerdict, {'DataScanned': handlerDataScanned})

    '''
    __________________________________________________________________________
    DockFighter
    When written: when docking a fighter back with the mothership
    Parameters: none
    Example:
    { "timestamp":"2016-06-10T14:32:03Z", "event":"DockFighter" }

    '''

    def handlerDockFighter(self, myjson, mypobj):
        printdebug("Handler Called: DockFighter")
        return

    updatehdict(handlerdict, {'DockFighter': handlerDockFighter})

    '''
    __________________________________________________________________________
    DockSRV
    When written: when docking an SRV with the ship
    Parameters: none

    '''

    def handlerDockSRV(self, myjson, mypobj):
        printdebug("Handler Called: DockSRV")
        return

    updatehdict(handlerdict, {'DockSRV': handlerDockSRV})

    '''
    __________________________________________________________________________
    FuelScoop
    When written: when scooping fuel from a star
    Parameters:
    Scooped: tons fuel scooped
    Total: total fuel level after scooping

    Example:
    { "timestamp":"2016-06-10T14:32:03Z", "event":"FuelScoop",
    "Scooped":0.498700, "Total":16.000000 }


    '''

    def handlerFuelScoop(self, myjson, mypobj):
        printdebug("Handler Called: FuelScoop")
        return

    updatehdict(handlerdict, {'FuelScoop': handlerFuelScoop})

    '''
    __________________________________________________________________________
    JetConeBoost
    When written: when enough material has been collected from a
    solar jet code (at a white dwarf or neutron star) for a jump boost
    Parameters:
    BoostValue

    '''

    def handlerJetConeBoost(self, myjson, mypobj):
        printdebug("Handler Called: JetConeBoost")
        return

    updatehdict(handlerdict, {'JetConeBoost': handlerJetConeBoost})

    '''
    __________________________________________________________________________
    JetConeDamage
    When written: when passing through the jet code from a white dwarf or
    neutron star has caused damage to a ship module
    Parameters:
    Module: the name of the module that has taken some damage

    '''

    def handlerJetConeDamage(self, myjson, mypobj):
        printdebug("Handler Called: JetConeDamage")
        return

    updatehdict(handlerdict, {'JetConeDamage': handlerJetConeDamage})

    '''
    __________________________________________________________________________
    LaunchFighter
    When written: when launching a fighter
    Parameters:
    Loadout
    PlayerControlled: whether player is controlling the fighter from launch

    { "timestamp":"2016-06-10T14:32:03Z", "event":"LaunchFighter",
    "Loadout":"starter", "PlayerControlled":true }

    '''

    def handlerLaunchFighter(self, myjson, mypobj):
        printdebug("Handler Called: LaunchFighter")
        return

    updatehdict(handlerdict, {'LaunchFighter': handlerLaunchFighter})

    '''
    __________________________________________________________________________
    LaunchSRV
    When written: deploying the SRV from a ship onto planet surface
    Parameters:
    Loadout

    '''

    def handlerLaunchSRV(self, myjson, mypobj):
        printdebug("Handler Called: LaunchSRV")
        return

    updatehdict(handlerdict, {'LaunchSRV': handlerLaunchSRV})

    '''
    __________________________________________________________________________
    Promotion
    When written: when the player’s rank increases
    Parameters: one of the following
    Combat: new rank
    Trade: new rank
    Explore: new rank
    CQC: new rank

    Example:
    { "timestamp":"2016-06-10T14:32:03Z", "event":"Promotion", "Explore":2 }

    '''

    def handlerPromotion(self, myjson, mypobj):
        printdebug("Handler Called: Promotion")
        return

    updatehdict(handlerdict, {'Promotion': handlerPromotion})

    '''
    __________________________________________________________________________
    RebootRepair
    When written: when the ‘reboot repair’ function is used
    Parameters:
    Modules: JSON array of names of modules repaired
    Example:
    { "timestamp":"2016-06-10T14:32:03Z", "event":"RebootRepair",
    "Modules":[ “MainEngines”, “TinyHardpoint1” ] }

    '''

    def handlerRebootRepair(self, myjson, mypobj):
        printdebug("Handler Called: RebootRepair")
        return

    updatehdict(handlerdict, {'RebootRepair': handlerRebootRepair})

    '''
    __________________________________________________________________________
    ReceiveText
    When written: when a text message is received from another player
    Parameters:
    From
    Message

    '''

    def handlerReceiveText(self, myjson, mypobj):
        printdebug("Handler Called: ReceiveText")
        return

    updatehdict(handlerdict, {'ReceiveText': handlerReceiveText})

    '''
    __________________________________________________________________________
    Resurrect
    When written: when the player restarts after death
    Parameters:
    Option: the option selected on the insurance rebuy screen
    Cost: the price paid
    Bankrupt: whether the commander declared bankruptcy

    '''

    def handlerResurrect(self, myjson, mypobj):
        printdebug("Handler Called: Resurrect")
        return

    updatehdict(handlerdict, {'Resurrect': handlerResurrect})

    '''
    __________________________________________________________________________
    SelfDestruct
    When written: when the ‘self destruct’ function is used
    Parameters: none

    '''

    def handlerSelfDestruct(self, myjson, mypobj):
        printdebug("Handler Called: SelfDestruct")
        return

    updatehdict(handlerdict, {'SelfDestruct': handlerSelfDestruct})

    '''
    __________________________________________________________________________
    SendText
    When written: when a text message is sent to another player
    Parameters:
    To
    Message

    Example:
    { "timestamp":"2016-06-10T14:32:03Z", "event":"SendText", "To":"HRC-2",
    "Message":"zoom" }

    '''

    def handlerSendText(self, myjson, mypobj):
        printdebug("Handler Called: SendText")
        return

    updatehdict(handlerdict, {'SendText': handlerSendText})

    '''
    __________________________________________________________________________
    Synthesis
    When written: when synthesis is used to repair or rearm
    Parameters:
    Name: synthesis blueprint
    Materials: JSON object listing materials used and quantities

    Example:
    { "timestamp":"2016-06-10T14:32:03Z", "event":"Synthesis",
    "Name":"Repair Basic", "Materials":{ "iron":2, "nickel":1 } }

    '''

    def handlerSynthesis(self, myjson, mypobj):
        printdebug("Handler Called: Synthesis")
        return

    updatehdict(handlerdict, {'Synthesis': handlerSynthesis})

    '''
    __________________________________________________________________________
    USSDrop
    When written: when dropping from Supercruise at a USS
    Parameters:
    USSType: description of USS
    USSThreat: threat level

    Example:
    { "timestamp":"2016-06-10T14:32:03Z", “event”:”USSDrop”,
    “USSType”:”Disrupted wake echoes”, “USSThreat”: 0 }

    '''

    def handlerUSSDrop(self, myjson, mypobj):
        printdebug("Handler Called: USSDrop")
        return

    updatehdict(handlerdict, {'USSDrop': handlerUSSDrop})

    '''
    __________________________________________________________________________
    VehicleSwitch
    When written: when switching control between the main ship and a fighter
    Parameters:
    To: ( Mothership/Fighter)

    Examples:
    { "timestamp":"2016-06-10T14:32:03Z",
        "event":"VehicleSwitch", "To":"Fighter" }
    { "timestamp":"2016-06-10T14:32:03Z",
        "event":"VehicleSwitch", "To":"Mothership" }

    '''

    def handlerVehicleSwitch(self, myjson, mypobj):
        printdebug("Handler Called: VehicleSwitch")
        return

    updatehdict(handlerdict, {'VehicleSwitch': handlerVehicleSwitch})

    '''
    __________________________________________________________________________
    WingAdd
    When written: another player has joined the wing
    Parameters:
    Name

    Example:
    { "timestamp":"2016-06-10T14:32:03Z", "event":"WingAdd", "Name":"HRC-2" }

    '''

    def handlerWingAdd(self, myjson, mypobj):
        printdebug("Handler Called: WingAdd")
        return

    updatehdict(handlerdict, {'WingAdd': handlerWingAdd})

    '''
    __________________________________________________________________________
    WingJoin
    When written: this player has joined a wing
    Parameters:
    Others: JSON array of other player names already in wing

    Example:
    { "timestamp":"2016-06-10T14:32:03Z", "event":"WingJoin",
        "Others":[ "HRC1" ] }

    '''

    def handlerWingJoin(self, myjson, mypobj):
        printdebug("Handler Called: WingJoin")
        return

    updatehdict(handlerdict, {'WingJoin': handlerWingJoin})

    '''
    __________________________________________________________________________
    WingLeave
    When written: this player has left a wing
    Parameters: none
    Example:
    { "timestamp":"2016-06-10T14:32:03Z", "event":"WingLeave" }

    '''

    def handlerWingLeave(self, myjson, mypobj):
        printdebug("Handler Called: WingLeave")
        return

    updatehdict(handlerdict, {'WingLeave': handlerWingLeave})



    # Other things
    def routetohandler(self, myjson, pobj):
        # Verify we're getting a good object
        if type(pobj) is not PrimaryObject:
            # Not what we want
            raise TypeError('pobj not a Primary Object')
        if type(pobj.cmdr) is not CMDR:
            raise TypeError("pobj.cmdr not a CMDR")
        # OK - so we should be able to continue now
        if myjson['event'] in self.handlerdict:
            functiontocall = self.handlerdict[myjson['event']]
        else:
            functiontocall = self.handlerdict['Fallback']
            # printdebug('Router falling back.')
        try:
            functiontocall(self, myjson, pobj)
        except:
            print("Message Router: Error calling %s" % functiontocall)
            if DEBUG is True:
                raise

    def __init__(self):
        pass

if __name__ == '__main__':
    myjournalh = JournalHandler()
    print("ED Journal Handler (Version: %s) knows the following events:" % VERSION)
    for k in sorted(myjournalh.handlerdict.keys()):
        print(k)
