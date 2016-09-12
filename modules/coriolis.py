#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Object(s) to read coriolis data into python objects

Handle all transformations and actions against coriolis data

Handle mappings against journal identifiers also (wish we had a list!)

Refresh json from website (future)

Needs ./coriolis-data/dist/index.json

'''

import json
from collections import namedtuple
from os.path import isfile
from pprint import pprint

DEBUG = True
ERROR = True
VERSION = '2.2 Beta'


def printdebug(mystring):
    if DEBUG is True:
        print("DEBUG coriolis: %s" % mystring)


def printerror(mystring):
    if ERROR is True:
        print("ERROR coriolis: %s" % mystring)



'''
Common Mapping Functions
'''

class Mapper(object):
    # These mappings are class variables
    # Journal Names to Coriolis Names
    shipnamemap_journal_to_coriolis = {
        'cobramkiii': 'cobra_mk_iii',
        'CobraMkIV': 'cobra_mk_iv',
        'viper_mkiv': 'viper_mk_iv'
    }

    shipnamemap_corolis_to_journal = {
        v: k for k, v in shipnamemap_journal_to_coriolis.items()
    }

    ModuleGroupToName = {
        # Standard
        'pp': 'Power Plant',
        't': 'Thrusters',
        'fsd': 'Frame Shift Drive',
        'ls': 'Life Support',
        'pd': 'Power Distributor',
        's': 'Sensors',
        'ft': 'Fuel Tank',
        'pas': 'Planetary Approach Suite',
        # Internal
        'fs': 'Fuel Scoop',
        'sc': 'Scanner',
        'am': 'Auto Field-Maintenance Unit',
        'bsg': 'Bi-Weave Shield Generator',
        'cr': 'Cargo Rack',
        'fi': 'Frame Shift Drive Interdictor',
        'hb': 'Hatch Breaker Limpet Controller',
        'hr': 'Hull Reinforcement Package',
        'rf': 'Refinery',
        'scb': 'Shield Cell Bank',
        'sg': 'Shield Generator',
        'pv': 'Planetary Vehicle Hangar',
        'psg': 'Prismatic Shield Generator',
        'dc': 'Docking Computer',
        'fx': 'Fuel Transfer Limpet Controller',
        'pc': 'Prospector Limpet Controller',
        'cc': 'Collector Limpet Controller',
        # Hard Points
        'bl': 'Beam Laser',
        'ul': 'Burst Laser',
        'c': 'Cannon',
        'cs': 'Cargo Scanner',
        'cm': 'Countermeasure',
        'fc': 'Fragment Cannon',
        'ws': 'Frame Shift Wake Scanner',
        'kw': 'Kill Warrant Scanner',
        'nl': 'Mine Launcher',
        'ml': 'Mining Laser',
        'mr': 'Missile Rack',
        'pa': 'Plasma Accelerator',
        'mc': 'Multi-cannon',
        'pl': 'Pulse Laser',
        'rg': 'Rail Gun',
        'sb': 'Shield Booster',
        'tp': 'Torpedo Pylon'
    }

    def shipname_jtoc(self, name):
        # Convert a journal name to a coriolis name
        if name in self.shipnamemap_journal_to_coriolis.keys():
            return self.shipnamemap_journal_to_coriolis[name]
        else:
            printdebug('Journal Ship Type %s not found in Coriolis mappings' % name)
            return 'NoCName'

    def shipname_ctoj(self, name):
        # Convert a coriolis name to a journal name
        if name in self.shipnamemap_corolis_to_journal.keys():
            return self.shipnamemap_corolis_to_journal[name]
        else:
            printdebug('Coriolis Ship Type %s not found in Journal mappings' % name)
            return 'NoJName'

    '''
    TODO examine this section
    let GrpNameToCodeMap = {};

    for (let grp in ModuleGroupToName) {
      GrpNameToCodeMap[ModuleGroupToName[grp].toLowerCase()] = grp;
    }

    export const ModuleNameToGroup = GrpNameToCodeMap;
    '''

    # The following is mostly guess work at this point.
    modulegrouptojname = {
        # Standard
        'pp': 'powerplant',
        't': 'thrusters',
        'fsd': 'frameshiftdrive',
        'ls': 'lifesupport',
        'pd': 'powerdistributor',
        's': 'sensors',
        'ft': 'fueltank',
        'pas': 'planetaryapproachsuite',
        # Internal
        'fs': 'fuelscoop',
        'sc': 'scanner',
        'am': 'autofieldmaintenanceunit',
        'bsg': 'biweaveshieldgenerator',
        'cr': 'cargorack',
        'fi': 'frameshiftdriveinterdictor',
        'hb': 'hatchbreakerlimpetcontroller',
        'hr': 'hullreinforcementpackage',
        'rf': 'refinery',
        'scb': 'shieldcellbank',
        'sg': 'shieldgenerator',
        'pv': 'planetaryvehiclehangar',
        'psg': 'prismaticshieldgenerator',
        'dc': 'dockingcomputer',
        'fx': 'fueltransferlimpetcontroller',
        'pc': 'prospectorlimpetcontroller',
        'cc': 'collectorlimpetcontroller',
        # Hard Points
        'bl': 'beamlaser',
        'ul': 'burstlaser',
        'c': 'cannon',
        'cs': 'cargoscanner',
        'cm': 'countermeasure',
        'fc': 'fragmentcannon',
        'ws': 'frameshiftwakescanner',
        'kw': 'killwarrantscanner',
        'nl': 'minelauncher',
        'ml': 'mininglaser',
        'mr': 'missilerack',
        'pa': 'plasmaaccelerator',
        'mc': 'multicannon',
        'pl': 'pulselaser',
        'rg': 'railgun',
        'sb': 'shieldbooster',
        'tp': 'torpedopylon'
    }

    modulejnametogroup = {
        v: k for k, v in modulegrouptojname.items()
    }

    def modulegroup_jtoc(self, name):
        # Convert a journal name to a coriolis name
        if name in self.modulejnametogroup.keys():
            return self.modulejnametogroup[name]
        else:
            printdebug('Journal Module Type %s not found in Coriolis mappings' % name)
            return 'NoCName'

    def modulegroup_ctoj(self, name):
        # Convert a coriolis name to a journal name
        if name in self.modulegrouptojname.keys():
            return self.modulegrouptojname[name]
        else:
            printdebug('Coriolis Module Type %s not found in Journal mappings' % name)
            return 'NoJName'

    maphptmount_jtoc = {
        'fixed': 'F',
        'gimbal': 'G',
        'turret': 'T'
        }

    maphptmount_ctoj = {
        v: k for k, v in maphptmount_jtoc.items()
    }

    def hptmount_jtoc(self, name):
        # Convert a journal name to a coriolis name
        if name in self.maphptmount_jtoc.keys():
            return self.maphptmount_jtoc[name]
        else:
            printdebug('Journal Mount Type %s not found in Coriolis mappings' % name)
            return 'NoCName'

    def hptmount_ctoj(self, name):
        # Convert a coriolis name to a journal name
        if name in self.maphptmount_ctoj.keys():
            return self.maphptmount_ctoj[name]
        else:
            printdebug('Coriolis Mount Type %s not found in Journal mappings' % name)
            return 'NoJName'

    maphptsize_jtoc = {
        'utility': 0,
        'small': 1,
        'medium': 2,
        'large': 3,
        'huge': 4         # Possible this should be capital
        }

    maphptsize_ctoj = {
        v: k for k, v in maphptmount_jtoc.items()
    }

    def hptsize_jtoc(self, name):
        # Convert a journal name to a coriolis name
        if name in self.maphptsize_jtoc.keys():
            return self.maphptsize_jtoc[name]
        else:
            printdebug('Journal HPT Size %s not found in Coriolis mappings' % name)
            return 'NoCName'

    def hptsize_ctoj(self, name):
        # Convert a coriolis name to a journal name
        if name in self.maphptsize_ctoj.keys():
            return self.maphptsize_ctoj[name]
        else:
            printdebug('Coriolis HPT Size %s not found in Journal mappings' % name)
            return 'NoJName'


    def __init__(self):
        pass



class ModulesStandard(object):
    # Container for Standard Modules
    def __init__(self, mydict):
        self.data = mydict
        # Some indexes
        # a list of module types
        self.modtypes = mydict.keys()
        printdebug('Known Standard Module types are: %s' % self.modtypes)
        # Step through and create some lookup dicts
        self.idlookup = {}
        self.edidlookup = {}
        self.eddbidlookup = {}
        self.typeclassratinglookup = {}
        self.modulecount = 0
        for mymodtype in self.modtypes:
            # mymodtype is a list of dict
            for myitem in self.data[mymodtype]:
                # myitem is a dict containing the module info
                if 'id' in myitem.keys():
                    self.idlookup[myitem['id']] = myitem
                else:
                    printerror('id not found indexing standard mod: %s' % myitem)
                if 'edID' in myitem.keys():
                    self.edidlookup[myitem['edID']] = myitem
                else:
                    printerror('edID not found indexing standard mod: %s' % myitem)
                if 'eddbID' in myitem.keys():
                    self.eddbidlookup[myitem['eddbID']] = myitem
                else:
                    printerror('eddbID not found indexing standard mod: %s' % myitem)
                mytcr = ('%s%s%s' % (
                                    mymodtype,
                                    myitem['class'],
                                    myitem['rating']
                                    )
                                    )
                self.typeclassratinglookup[mytcr] = myitem
                self.modulecount += 1
        printdebug('%s Standard Module Types Loaded' % self.modulecount)

class ModulesHardpoints(object):
    # Container for Hardpoints

    def gethptbyjname(self, jname):
        # e.g. hpt_multicannon_gimbal_medium_name
        # Split jname by '_'
        jcomps = jname.split('_')
        # Decode group
        group = jcomps[1]
        mount = jcomps[2]
        sizename = jcomps[3]
        mymapper = Mapper()
        group = mymapper.modulegroup_jtoc(group)
        mount = mymapper.hptmount_jtoc(mount)
        sizename = mymapper.hptsize_jtoc(sizename)
        printdebug('%s converted to G: %s, M: %s, S: %s' % (
            jname, group, mount, sizename))
        mygmc = ('%s%s%s' % (group, mount, sizename))
        if mygmc in self.groupmountclasslookup.keys():
            return self.groupmountclasslookup[mygmc]
        else:
            return None

    def __init__(self, mydict):
        self.data = mydict
        # Some indexes
        # a list of module types
        self.modtypes = mydict.keys()
        printdebug('Known Hardpoint groups are: %s' % self.modtypes)
        # Step through and create some lookup dicts
        self.idlookup = {}
        self.edidlookup = {}
        self.eddbidlookup = {}
        self.typeclassratinglookup = {}
        self.groupmountclasslookup = {}
        self.modulecount = 0
        for mymodtype in self.modtypes:
            # mymodtype is a list of dict
            for myitem in self.data[mymodtype]:
                # myitem is a dict containing the module info
                if 'id' in myitem.keys():
                    self.idlookup[myitem['id']] = myitem
                else:
                    printerror('id not found indexing hardpoint: %s' % myitem)
                if 'edID' in myitem.keys():
                    self.edidlookup[myitem['edID']] = myitem
                else:
                    printerror('edID not found indexing hardpoint: %s' % myitem)
                if 'eddbID' in myitem.keys():
                    self.eddbidlookup[myitem['eddbID']] = myitem
                else:
                    printerror('eddbID not found indexing hardpoint: %s' % myitem)
                # Search by type class and rating
                try:
                    mytcr = ('%s%s%s' % (
                                        mymodtype,
                                        myitem['class'],
                                        myitem['rating']
                                        )
                                        )
                    self.typeclassratinglookup[mytcr] = myitem
                except:
                    # This would mostly be a key error
                    printdebug('Could not TCR index item: %s' % myitem)
                try:
                    mygmc = ('%s%s%s' % (
                                        myitem['grp'],
                                        myitem['mount'],
                                        myitem['class']
                                        )
                                        )
                    self.groupmountclasslookup[mygmc] = myitem
                except:
                    # This would mostly be a key error
                    # Not all items have these keys so that's probably fine.
                    printdebug('Could not GMC index item: %s' % myitem)
                self.modulecount += 1
        printdebug('%s Hardpoint Types Loaded' % self.modulecount)

class ModulesInternal(object):
    # Container for Standard Modules

    def getmodbyjname(self, jname):
        # e.g. "SellItem":"int_cargorack_size1_class1"
        # TODO What (if any) is the difference between size and class?
        # What about rating?

        # Split jname by '_'
        jcomps = jname.split('_')
        # Decode group
        group = jcomps[1]
        size = [int(c) for c in jcomps[2] if c.isdigit()][0]  # extract int
        cclass = [int(c) for c in jcomps[3] if c.isdigit()][0] # extract int
        mymapper = Mapper()
        group = mymapper.modulegroup_jtoc(group)
        mount = mymapper.hptmount_jtoc(mount)
        sizename = mymapper.hptsize_jtoc(sizename)
        printdebug('%s converted to G: %s, M: %s, S: %s' % (
            jname, group, mount, sizename))
        mygmc = ('%s%s%s' % (group, mount, sizename))
        if mygmc in self.groupmountclasslookup.keys():
            return self.groupmountclasslookup[mygmc]
        else:
            return None

    def __init__(self, mydict):
        self.data = mydict
        # Some indexes
        # a list of module types
        self.modtypes = mydict.keys()
        printdebug('Known Internal Module types are: %s' % self.modtypes)
        # Step through and create some lookup dicts
        self.idlookup = {}
        self.edidlookup = {}
        self.eddbidlookup = {}
        self.typeclassratinglookup = {}
        self.modulecount = 0
        for mymodtype in self.modtypes:
            # mymodtype is a list of dict
            for myitem in self.data[mymodtype]:
                # myitem is a dict containing the module info
                if 'id' in myitem.keys():
                    self.idlookup[myitem['id']] = myitem
                else:
                    printerror('id not found indexing internal: %s' % myitem)
                if 'edID' in myitem.keys():
                    self.edidlookup[myitem['edID']] = myitem
                else:
                    printerror('edID not found indexing internal: %s' % myitem)
                if 'eddbID' in myitem.keys():
                    self.eddbidlookup[myitem['eddbID']] = myitem
                else:
                    printerror('eddbID not found indexing internal: %s' % myitem)
                mytcr = ('%s%s%s' % (
                                    mymodtype,
                                    myitem['class'],
                                    myitem['rating']
                                    )
                                    )
                self.typeclassratinglookup[mytcr] = myitem
                self.modulecount += 1
        printdebug('%s Internal Modules Loaded' % self.modulecount)


class Modules(object):
    # Container for Modules

    def gethpbyid(self, myid='xx'):
        # Get a hardpoint by it's ID
        # lookups are str not int
        if type(myid) is not str:
            myid = str(myid)
        if myid in self.hardpoints.idlookup.keys():
            return self.hardpoints.idlookup[myid]
        elif myid == '0':
            # means empty, not the same as '00' (chaff Launcher)
            return None
        else:
            printerror('%s not found in hardpoint idlookup' % myid)
            printerror(sorted(self.hardpoints.idlookup.keys()))
            return None

    def getintbyid(self, myid='xx'):
        # Get an internal module by it's ID
        # lookups are str not int
        if type(myid) is not str:
            myid = str(myid)
        if myid in self.internal.idlookup.keys():
            return self.internal.idlookup[myid]
        elif myid == '0':
            # means empty, not the same as '00' (chaff Launcher)
            return None
        else:
            printerror('%s not found in internals idlookup' % myid)
            printerror(sorted(self.internal.idlookup.keys()))
            return None

    def getmodbyedid(self, myid='999'):
        if type(myid) is not int:
            myid = int(myid)
        if int(myid) in self.edidlookup.keys():
            printdebug('ED ID %s found in EDDB ID lookup' % myid)
            return self.edidlookup[myid]
        else:
            printdebug('ED ID %s not found in EDDB ID lookup' % myid)
            return None

    def getmodbyeddbid(self, myid='xx'):
        if myid in self.eddbidlookup.keys():
            printdebug('EDDB ID %s found in EDDB ID lookup' % myid)
            return self.eddbidlookup[myid]
        else:
            printdebug('EDDB ID %s not found in EDDB ID lookup' % myid)
            return None

    def getmodbytcr(self, modtype='xx', cclass="x", rating="x"):
        mytcr = ('%s%s%s' % (modtype, cclass, rating))
        if mytcr in self.typeclassratinglookup.keys():
            return self.typeclassratinglookup[mytcr]
        else:
            return None

    def getmodbyjname(self, jname):
        # e.g. hpt_multicannon_gimbal_medium_name
        # Split jname by '_'
        jcomps = jname.split('_')
        if jcomps[0] == '$hpt':
            return self.hardpoints.gethptbyjname(jname)
        elif jcomps[0] == 'int':
            # "SellItem":"int_cargorack_size1_class1"
            return self.internals.getmodbyjname(jname)
        else:
            return None

    def __init__(self, mydict):
        self.standard = ModulesStandard(mydict['standard'])
        self.hardpoints = ModulesHardpoints(mydict['hardpoints'])
        self.internal = ModulesInternal(mydict['internal'])
        #
        # Now let's make some lookup functions
        # These just combine the lookup dictionaries of our components
        '''
        Can't do this because there is id overlap between hardpoints
        and internals
        self.idlookup = {}
        self.idlookup.update(self.standard.idlookup)
        self.idlookup.update(self.hardpoints.idlookup)
        self.idlookup.update(self.internal.idlookup)
        '''
        self.edidlookup = {}
        self.edidlookup.update(self.standard.edidlookup)
        self.edidlookup.update(self.hardpoints.edidlookup)
        self.edidlookup.update(self.internal.edidlookup)
        self.eddbidlookup = {}
        self.eddbidlookup.update(self.standard.eddbidlookup)
        self.eddbidlookup.update(self.hardpoints.eddbidlookup)
        self.eddbidlookup.update(self.internal.eddbidlookup)
        self.typeclassratinglookup = {}
        self.typeclassratinglookup.update(self.standard.typeclassratinglookup)
        self.typeclassratinglookup.update(self.hardpoints.typeclassratinglookup)
        self.typeclassratinglookup.update(self.internal.typeclassratinglookup)
        self.modulecount = (self.standard.modulecount +
                            self.hardpoints.modulecount +
                            self.internal.modulecount)
        printdebug('System know a total of %d modules.' % self.modulecount)



class Ship(object):
    # A single Ship

    def __init__(self, mydict):
        self.data = mydict          # always there if we need it.
        try:
            self.edid = mydict['edID']
            self.eddbid = mydict['eddbID']
            self.properties = mydict['properties']
            self.retailcost = mydict['retailCost']
            self.bulkheads = mydict['bulkheads']
            self.slots_standard = mydict['slots']['standard']
            self.slots_hardpoints = mydict['slots']['hardpoints']
            self.slots_internal = mydict['slots']['internal']
            self.defaults_standard = mydict['defaults']['standard']
            self.defaults_hardpoints = mydict['defaults']['hardpoints']
            self.defaults_internal = mydict['defaults']['internal']
            printdebug('Loaded Ship: %s' % self.properties['name'])
        except Exception as e:
            printerror('Could not load Ship: %s %s' % (str(e), str(mydict)))

class Ships(object):
    # Container for Ships
    # This is nothing more than a dictionary of Ship instances
    # presented as an object, with some useful methods added.

    def get_by_name(self, name):
        '''
        This returns a ship identied by the ship type
        We in sequence:
            direct key lookup (key values from coriolis)
            check for mapping between journal name (jname) and coriolis name
            other...
        '''
        keycache = self.ships.keys()
        if name in keycache:
            return self.ships[name]
        else:
            mymap = Mapper()
            cname = mymap.shipname_jtoc(name)  # Try Journal map
            if cname in keycache:
                return self.ships[cname]
            else:
                # other checks could go here
                return False


    def __init__(self, mydict):
        self.ships = {}
        for k in mydict.keys():
            self.ships[k] = Ship(mydict[k])

class Coriolis(object):
    '''
    This is the primary Coriolis object
    it consists of .ships. and .modules.
    '''

    def json_parser(self, myobj):
        # TODO can probably be removed now
        # Need to replace the odd key
        # print(dict(myobj))
        #print(myobj.keys())
        return myobj
        # None of the below is currently used.
        # Kept for reference
        for k in myobj.keys():
            if k == 'class':     # Can't use class
                myobj['cclass'] = myobj.pop('class')
        # And then convert to objects
        if 'adder' in myobj.keys():
            # Retain as dictionary
            return myobj
        else:   # Convert to objects
            myobj = namedtuple('X', myobj.keys())(*myobj.values())
            return myobj

    def data_load_process(self):
        # Called after data is loaded from JSON
        # Improves usability by creating objects for the items
        self.ships = Ships(self.data['Ships'])
        self.modules = Modules(self.data['Modules'])


    def __init__(self, filepath='modules\coriolis-data\dist\index.json'):
        # Well, we need to open the filepath
        if isfile(filepath):
            printdebug('%s found. Trying to load Coriolis data.' % filepath)
            try:
                with open(filepath, 'r') as myfile:
                    self.data = json.load(myfile, object_hook=self.json_parser)
                    myfile.close
                printdebug('Successfully loaded JSON: %s' % filepath)
                self.data_load_process()
                printdebug('Test get ship by name: %s' % self.ships.get_by_name('keelback').properties['name'])
                self.loaded = True  # TODO better checks here
            except Exception as e:
                print(str(e))

        else:
            printerror('%s not found. Cannot load Coriolis data.' % filepath)
