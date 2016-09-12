#!/usr/bin/env python
# -*- coding: utf-8 -*-

DEBUG = True
ERROR = True
VERSION = '2.2 Beta'

from pprint import pprint

def printdebug(mystring):
    if DEBUG is True:
        print("DEBUG edjhandler: %s" % mystring)

def printerror(mystring):
    if ERROR is True:
        print("ERROR edjhandler: %s" % mystring)

'''
This module contains the primary objects
The following are the key objects I'll require.
pobj_state - this is for general system status (e.g. INACTIVE, CMDR_LOADED)
pobj_cmdr - this is the current commander, including any materials and prefs
pobj_ship - this is the current ship, including loadout and cargo
pobj_universe - this is the universe
pobj_starsystem - this is the current star system
pobj_localbody - this is the current local body
'''

from modules.coriolis import Coriolis, Mapper
from modules.fdevid import Mapper as FDMapper

# Define constants

# From journal documentation
'''
Ranks
Combat ranks: 0='Harmless', 1='Mostly Harmless', 2='Novice', 3='Competent',
4='Expert', 5='Master', 6='Dangerous', 7='Deadly', 8='Elite’

Trade ranks: 0='Penniless', 1='Mostly Pennliess', 2='Peddler', 3='Dealer',
4='Merchant', 5='Broker', 6='Entrepreneur', 7='Tycoon', 8='Elite'

Exploration ranks: 0='Aimless', 1='Mostly Aimless', 2='Scout', 3='Surveyor',
4='Explorer', 5='Pathfinder', 6='Ranger', 7='Pioneer', 8='Elite'

Federation ranks: 0='None', 1='Recruit', 2='Cadet', 3='Midshipman',
4='Petty Officer', 5='Chief Petty Officer', 6='Warrant Officer', 7='Ensign',
8='Lieutenant', 9='Lt. Commander', 10='Post Commander', 11= 'Post Captain',
12= 'Rear Admiral', 13='Vice Admiral', 14=’Admiral’

Empire ranks: 0='None', 1='Outsider', 2='Serf', 3='Master', 4='Squire',
5='Knight', 6='Lord', 7='Baron',  8='Viscount ', 9=’Count', 10= 'Earl',
11='Marquis' 12='Duke', 13='Prince', 14=’King’

CQC ranks: 0=’Helpless’, 1=’Mostly Helpless’, 2=’Amateur’,
3=’Semi Professional’, 4=’Professional’, 5=’Champion’, 6=’Hero’,
7=’Legend’, 8=’Elite’
'''

# From coriolis-data
# https://github.com/cmmcleod/coriolis/blob/master/src/app/shipyard/Constants.js
ArmourMultiplier = (
    1,      # Lightweight
    1.4,    # Reinforced
    1.945,  # Military
    1.945,  # Mirrored
    1.945   # Reactive
    )

SizeMap = ('', 'small', 'medium', 'large', 'capital')

StandardArray = (
    'pp',   # Power Plant
    't',    # Thrusters
    'fsd',  # Frame Shift Drive
    'ls',   # Life Support
    'pd',   # Power Distributor
    's',    # Sensors
    'ft',   # Fuel Tank
    )


BulkheadNames = (
    'Lightweight Alloy',
    'Reinforced Alloy',
    'Military Grade Composite',
    'Mirrored Surface Composite',
    'Reactive Surface Composite'
    )


class PrimaryObject(object):

    def __init__(self):
        self.cmdr = CMDR()
        self.ship = None
        self.state = State()
        self.universe = Universe()
        self.starsystem = None
        self.localbody = None

class State(object):

    def __init__(self):
        self.loadstate = 'NOTLOADED'
        pass


# The following are component classes for the ship configurations

class Component(object):

    def __init__(self, *args, **kwargs):
        # Expects (cclass= , rating= , enabled=, priority= )
        self.known = False
        self.cclass = kwargs.pop('cclass', None)
        self.rating = kwargs.pop('rating', None)
        self.enabled = kwargs.pop('enabled', None)
        self.priority = kwargs.pop('priority', None)


class GroupedComponent(object):

    def __init__(self, *args, **kwargs):
        # Expects (cclass= , rating= , enabled=, priority= , group= )
        self.group = kwargs.pop('group', None)
        super().__init__()


class Hardpoint(GroupedComponent):

    def __init__(self, *args, **kwargs):
        # Expects (cclass= , rating= , enabled=, priority= , group= , mount= )
        self.mount = kwargs.pop('mount', None)
        super().__init__()


class Utilty(GroupedComponent):

    def __init__(self, *args, **kwargs):
        # Expects (cclass= , rating= , enabled=, priority= , group= , name= )
        # name is optional
        self.name = kwargs.pop('name', None)
        super().__init__()


class Internal(GroupedComponent):

    def __init__(self, cclass, rating, enabled, priority, group, name=None):
        # Expects (cclass= , rating= , enabled=, priority= , group= , name= )
        # Name is optional
        self.name = kwargs.pop('name', None)
        super().__init__()


class StandardSlot(object):

    def getsize():
        return self.size

    def getcontent():
        return self.attached

    def attach(self, unit):
        # TODO Add some sanity checks
        self.attached = unit

    def __init__(self, size):
        if type(size) is int:
            if (size >= 0 and size <= 8):
                self.size = size
            else:
                self.size = 0
        else:
            self.size = 0
        self.attached = None

class InternalSlot(StandardSlot):
    pass


class HardpointMount(object):

    def getsize(self):
        return self.size

    def getsizename(self):
        return self.sizename

    def gethardpoint(self):
        return self.attached

    def attach(self, unit):
        # TODO Add some sanity checks
        printdebug('Attaching \n%s \nto \n%s' % (unit, self))
        self.attached = unit

    def detach(self):
        # TODO Add some sanity checks
        # Detach the unit and return it for reference
        unit = self.attached
        self.attached = None
        return unit

    def __init__(self, size):
        mappings = {
            0: 'U',
            1: 'S',
            2: 'M',
            3: 'L',
            4: 'H'
        }
        if type(size) is int:
            if (size >= 0 and size <= 4):
                self.size = size
            else:
                self.size = 0
        else:
            self.size = 0
        self.sizename = mappings[self.size]
        self.attached = None

class StandardSlots(object):

    def load_defaults(self, mypobj, defaults):
        # Loads modules into the slots based on Coriolis defaults
        # Modules are defined as SizeClass e.g. "4E" so use getmodbytcr

        # TODO add check that we've been initialised properly
        # shortcut
        coriolis = mypobj.universe.coriolis.modules
        self.powerplant.attach(coriolis.getmodbytcr('pp', defaults[0][0], defaults[0][1]))
        printdebug("Loaded Default Powerplant: Class %s, Rating %s" % (defaults[0][0], defaults[0][1]))
        self.thrusters.attach(coriolis.getmodbytcr('t', defaults[1][0], defaults[1][1]))
        printdebug("Loaded Default Thrusters: Class %s, Rating %s" % (defaults[1][0], defaults[1][1]))
        self.fsd.attach(coriolis.getmodbytcr('fsd', defaults[2][0], defaults[2][1]))
        printdebug("Loaded Default FSD: Class %s, Rating %s" % (defaults[2][0], defaults[2][1]))
        self.lifesupport.attach(coriolis.getmodbytcr('ls', defaults[3][0], defaults[3][1]))
        printdebug("Loaded Default Life Support: Class %s, Rating %s" % (defaults[3][0], defaults[3][1]))
        self.powerdist.attach(coriolis.getmodbytcr('pd', defaults[4][0], defaults[4][1]))
        printdebug("Loaded Default Power Distributor: Class %s, Rating %s" % (defaults[4][0], defaults[4][1]))
        self.sensors.attach(coriolis.getmodbytcr('s', defaults[5][0], defaults[5][1]))
        printdebug("Loaded Default Sensors: Class %s, Rating %s" % (defaults[5][0], defaults[5][1]))
        self.fueltank.attach(coriolis.getmodbytcr('ft', defaults[6][0], defaults[6][1]))
        printdebug("Loaded Default Fuel Tank: Class %s, Rating %s" % (defaults[6][0], defaults[6][1]))
        # TODO - do we need to verify it's all loaded OK?
        # Probably should, getmodbytcr returns None if not found
        # Could look for that... or just accept that as appropriate

    def __init__(self, slots):
        self.powerplant = StandardSlot(slots[0])
        self.thrusters = StandardSlot(slots[1])
        self.fsd = StandardSlot(slots[2])
        self.lifesupport = StandardSlot(slots[3])
        self.powerdist = StandardSlot(slots[4])
        self.sensors = StandardSlot(slots[5])
        self.fueltank = StandardSlot(slots[6])

class HardpointMounts(object):
    # Note Utilities are just harpoint size 0

    def load_defaults(self, mypobj, defaults):
        # Loads hardpoints into the slots based on Coriolis defaults
        # Hardpoints are defined by IDs
        # TODO add a friendly name
        # TODO add check that we've been initialised
        # quickref coriolis modules
        coriolis = mypobj.universe.coriolis.modules
        # Check that we have the expected number of items
        if len(defaults) != self.count:
            printerror('Wrong number of default hardpoints defined.')
            return
        slot = 0
        for hardpoint in defaults:
            if str(hardpoint) != '0':    # Empty slot optimisation
                mymod = coriolis.gethpbyid(hardpoint)
                if mymod is not None:
                    self.mount[slot].attach(mymod)
                    printdebug('Attached hardpoint Type: %s, Class: %s, Rating: %s to Slot: %d' %
                                (mymod['grp'], mymod['class'], mymod['rating'], slot)
                                )
                else:
                    printdebug('Could not locate hardpoint ID: %s' % hardpoint)
            slot += 1


    def __init__(self, slots):
        x = 0
        self.mount = {}
        for slot in slots:  # slots are sizes
            self.mount[x] = HardpointMount(slot)
            x += 1
        self.count = x

class InternalSlots(object):

    def load_defaults(self, mypobj, defaults):
        # Loads internal modules into the slots based on Coriolis defaults
        # InternalSlots are defined by IDs
        # TODO add a friendly name
        # TODO add check that we've been initialised
        # quickref coriolis modules
        coriolis = mypobj.universe.coriolis.modules
        # Check that we have the expected number of items
        if len(defaults) != self.count:
            printerror('Wrong number of default internals defined.')
            return
        slot = 0
        for internal in defaults:
            if str(internal) != '0':    # Empty slot optimisation
                mymod = coriolis.getintbyid(internal)
                if mymod is not None:
                    self.mount[slot].attach(mymod)
                    printdebug('Attached Internal Type: %s, Class: %s, Rating: %s to Slot: %d' %
                                (mymod['grp'], mymod['class'], mymod['rating'], slot)
                                )
                else:
                    printdebug('Could not locate internal module ID: %s' % internal)
            slot += 1

    def __init__(self, slots):
        # Slots contain a list of sizes
        x = 0
        self.mount = {}
        for slot in slots:  # slots are sizes
            self.mount[x] = InternalSlot(slot)
            x += 1
        self.count = x


class Ship(object):

    def getslotfromjref(self, jref):
        # Takes a module reference in the journals format
        # and returns the actual slot object in this ship or None
        # Step 1
        # Hardpoint or Internal
        #printdebug('Decoding %s' % jref)
        if 'Hardpoint' in jref:
            # "FromSlot":"MediumHardpoint1", "ToSlot":"SmallHardpoint1"
            hp = self.hardpoints
            # Which one?
            # Number bit is easy, it's the only digit we can use it to count
            num = [int(c) for c in jref if c.isdigit()][0]  # WordWordInt (<10)
            # We can locate by sizename, mapped through this dict.
            lookupmap = {
                'Utility': 'U',
                'Small': 'S',
                'Medium': 'M',
                'Large': 'L',
                'Huge': 'H'
            }
            sizename = [value for key, value in lookupmap.items() if key in jref][0]
            # Now we step through to find the nth hardpoint mount of that size.
            checked = 0
            for k, mount in hp.mount.items():
                if mount.getsizename() == sizename:
                    checked += 1
                    if checked == num:
                        printdebug('%s decoded to Hardpoint slot %d' % (jref, k))
                        return mount    # This is a HardpointMount
            # If we don't find anthing we return nothing.
            printdebug('Failed to decode journal reference %s' % jref)
            return None

        elif 'Slot' in jref:    # TODO
            # "Slot":"Slot06_Size2", "SellItem":"int_cargorack_size1_class1"
            printdebug('Its an internal module swap')
            printerror('Cannot do this yet.')

        else:
            printerror('Unknown sort of module swap')
            return None

    def jnameidcleaner(self, jname):
        fdid = (jname.strip('$;'))
        # Get of any _name
        words = fdid.split('_')
        cleanwords = [word for word in words if word != 'name']
        fdid = '_'.join(cleanwords)
        return fdid

    def moduleswap(self, mypobj, fromslot, toslot, fromitem, toitem, shipid):
        # I don't know why the to item would be different
        # first sanity check the shipID
        if self.shipid != shipid:
            printerror('ModuleSwap: ShipID %s is not what we expected (%s)' % (
                self.shipid, shipid))
            return False
        else:
            printdebug('ModuleSwap called OK')
            # got to decode the source and destination locations
            # all I've got at the moment is the hardpoints format so
            # start with that
            # TODO internals
            # Check if toitem is defined
            if toitem == 'Null':
                toitem = fromitem
            # We assume ED always does legal swaps!
            # We play catchup if we need to.
            printdebug('Uninstalling %s from %s' % (fromitem, fromslot))
            unit = self.getslotfromjref(fromslot).detach()
            printdebug('Detached %s' % unit)
            # Need to understand what the module we're attaching is
            printdebug('Installing %s in %s' % (toitem, toslot))
            # Use my FDevIS module to get the EDID for the module
            fdevidmap = FDMapper()
            # Example journal needs tidying up
            fdid = self.jnameidcleaner(toitem)
            printdebug('FDID is %s' % fdid)
            modedid = fdevidmap.getmoduleidbysymbol(fdid)
            printdebug('EDID is %s' % modedid)
            self.getslotfromjref(toslot).attach(
                mypobj.universe.coriolis.modules.getmodbyedid(modedid)
            )
            return True

    def modulebuy(self, mypobj, slot, item, price, shipid):
        if self.shipid != shipid:
            printerror('ModuleBuy: ShipID %s is not what we expected (%s)' % (
                self.shipid, shipid))
            return False
        else:
            printdebug('ModuleBuy called OK')
            mypobj.cmdr.spend(price)
            printdebug('Installing %s in %s' % (item, slot))
            fdevidmap = FDMapper()      # TODO Move this to Universe
            fdid = self.jnameidcleaner(item)
            printdebug('FDID is %s' % fdid)
            modedid = fdevidmap.getmoduleidbysymbol(fdid)
            printdebug('EDID is %s' % modedid)
            self.getslotfromjref(slot).attach(
                mypobj.universe.coriolis.modules.getmodbyedid(modedid)
            )
            return True

    def newshipmaker(self, mypobj, shipID, shiptype):
        # Based on Coriolis.io JSON format
        #
        if mypobj.universe.coriolis_loaded is False:
            printdebug('Coriolis Data Not Loaded')
            mypobj.universe.coriolis = Coriolis()
            if mypobj.universe.coriolis.loaded is True:
                mypobj.universe.coriolis_loaded = True
        # TODO Load the FDevID Mapper into Universe also

        # Need to check the coriolis load works or the following will fail TODO
        # Build the new ship based on default loadout from coriolis
        # We can always refer to this baseref if we need to
        self.baseref = mypobj.universe.coriolis.ships.get_by_name(shiptype)
        #
        self.shipid = shipID    # UID within CMDR
        self.shiptype = self.baseref.properties['name'] # Pretty name
        self.shipname = 'UNKNOWN'     # What the CMDR wants to call it TODO
        self.manufacturer = self.baseref.properties['manufacturer']
        self.cclass = self.baseref.properties['class']
        self.hullcost = self.baseref.properties['hullCost']
        self.speed = self.baseref.properties['speed']
        self.boost = self.baseref.properties['boost']
        self.boostenergy = self.baseref.properties['boostEnergy']
        self.agility = self.baseref.properties['agility']
        self.baseshieldstrength = self.baseref.properties['baseShieldStrength']
        self.basearmour = self.baseref.properties['baseArmour']
        self.masslock = self.baseref.properties['masslock']
        self.pipspeed = self.baseref.properties['pipSpeed']
        self.retailcost = self.baseref.retailcost
        #
        # self.components['standard']['bulkheads'] = "UNKNOWN" # TODO
        #
        # Create structure
        self.standard = StandardSlots(self.baseref.slots_standard)
        self.hardpoints = HardpointMounts(self.baseref.slots_hardpoints)
        self.internals = InternalSlots(self.baseref.slots_internal)
        # Load Defaults into structure - needs Coriolis object so pass ref
        self.standard.load_defaults(mypobj, self.baseref.defaults_standard)
        self.hardpoints.load_defaults(mypobj, self.baseref.defaults_hardpoints)
        self.internals.load_defaults(mypobj, self.baseref.defaults_internal)
        #
        self.stats = {}
        self.stats['hullMass'] = 0
        self.stats['fuelCapacity'] = 0
        self.stats['cargoCapacity'] = 0
        self.stats['ladenMass'] = 0
        self.stats['unladenMass'] = 0
        self.stats['unladenRange'] = 0
        self.stats['fullTankRange'] = 0
        self.stats['ladenRange'] = 0
        return

    def __init__(self, mypobj, shipID, shiptype):
        # Check if we can load the ship from the DB
        # Note Ship object is loaded into mypobj
        loadok = False
        if loadok is False:
            self.newshipmaker(mypobj, shipID, shiptype)
        return


class Universe(object):

    def __init__(self):
        self.coriolis_loaded = False
        self.coriolis = None



class System(object):

    def __init__(self):
        pass


class Body(object):

    def __init__(self):
        pass



class CMDR(object):

    def setname(self, name):    # TODO deprecate to loadcommander
        self.name = name

    def loadcommander(self, name):
        # Check if DB backend is connected

        # Query if commander exists

        # if exists load

        # if does not exist create new and save to DB
        self.savecommander()
        pass

    def savecommander(self):
        # Save commander to DB
        pass

    def setcredits(self, credits):
        self.credits = credits

    def addcredits(self, credits):
        self.credits += credits

    def losecredits(self, credits):
        self.credits -= credits

    def setgamemode(self, gamemode):
        self.gamemode = gamemode
        self.group = None

    def setgamemodegrp(self, gamemode, groupname):
        # Should I check that it's really 'Group'
        if gamemode is not 'Group':
            return
        self.gamemode = gamemode
        self.group = groupname

    def setcmdrisknown(self):
        self.known = True

    def setranks(self, combat, trade, explore, empire, federation, cqc):
        self.rank['combat'] = combat
        self.rank['trade'] = trade
        self.rank['explore'] = explore
        self.rank['empire'] = empire
        self.rank['federation'] = federation
        self.rank['cqc'] = cqc
        self.rank['known'] = True

    def setprogress(self, combat, trade, explore, empire, federation, cqc):
        self.rank['combat_progress'] = combat
        self.rank['trade_progress'] = trade
        self.rank['explore_progress'] = explore
        self.rank['empire_progress'] = empire
        self.rank['federation_progress'] = federation
        self.rank['cqc_progress'] = cqc
        self.rank['progress_known'] = True

    def spend(self, amount):
        self.credits -= amount
        if self.credits < 0:
            self.credits = 0
            printerror('Credits overspent! Correcting. You are broke!')
            return False
        return True

    def __init__(self):

        # Define properties
        self.known = False
        self.name = 'UNKNOWN'
        self.credits = 0
        self.loan = 0
        self.insuranceknown = False
        self.insurance = 0
        self.gamemode = None
        self.group = None
        # Rank
        self.rank = {}
        self.rank['known'] = False
        self.rank['progress_known'] = False
        self.rank['combat'] = 0
        self.rank['combat_progress'] = 0
        self.rank['trade'] = 0
        self.rank['trade_progress'] = 0
        self.rank['explore'] = 0
        self.rank['explore_progress'] = 0
        self.rank['cqc'] = 0
        self.rank['cqc_progress'] = 0
        self.rank['federation'] = 0
        self.rank['federation_progress'] = 0
        self.rank['empire'] = 0
        self.rank['empire_progress'] = 0
        # Reputation
        self.repknown = False
        self.federation_rep = 0
        self.empire_rep = 0
        self.alliance_rep = 0
        self.thargoid_rep = 0       # Well... you never know...
        # Ships
        self.shipknown = False
        self.currentshipid = 0
        self.ships = {}
        self.missions = {}
        # Engineers
        self.engineers = {}
        # self.missions.active
        # self.missions.history
