#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
This is a wrapper around coreapi to make talking to our DB easier

Our DB is a django based solution, exposing a REST API

At the moment django is using it's default sqllite DB, but there's nothing
to stop it using something else, like MySQL if you prefer.

'''

import coreapi      # Doesn't appear to like bulk uploads
import slumber      # So I'll try slumber
import cbor2 as cbor        # Reduces data massively.
import hashlib
import time
import base64
import sys
import gc
import copy
from multiprocessing import Process, Queue, JoinableQueue
from coreapi.compat import b64encode
from urllib import parse as parse
# import numpy
import math
try:
    from modules.edacdb_cache import DBCache
except:
    from edacdb_cache import DBCache
import config

# Just using django runserver at the moment
default_dbapi = config.settings.edacapi('dbapiurl')
default_bulkapi = config.settings.edacapi('bulkapiurl')
default_cborapi = config.settings.edacapi('cborapiurl')
default_username = config.settings.edacapi('apiusername')
default_password = config.settings.edacapi('apipassword')

DEBUG = True
ERROR = True
VERSION = '2.2 Beta'


def printdebug(mystring):
    if DEBUG is True:
        print("DEBUG edacdb_wrapper: %s" % mystring)


def printerror(mystring):
    if ERROR is True:
        print("ERROR edacdb_wrapper: %s" % mystring)

class SystemFilter(object):

    # For reference
    def fastest_calc_dist(p1,p2):
        return math.sqrt((p2[0] - p1[0]) ** 2 +
                         (p2[1] - p1[1]) ** 2 +
                         (p2[2] - p1[2]) ** 2)

    def aoitest(self, system):
        # Areas of Interest
        # Return True if we should filter, ie if the test fails
        if len(self.aois) == 0:
            return True
        #c1 = numpy.array((system['coord_x'], system['coord_y'], system['coord_z']))
        for aoi in self.aois:
            # Test if inside cube (quick)
            if abs(system['coord_z'] - aoi['z']) > aoi['r']:
                self.aoistatz += 1
                continue
            if abs(system['coord_x'] - aoi['x']) > aoi['r']:
                self.aoistatx += 1
                continue
            if abs(system['coord_y'] - aoi['y']) > aoi['r']:
                self.aoistaty += 1
                continue
            # if pass then test if inside sphere (not as quick)
            #c2 = numpy.array((aoi['x'], aoi['y'], aoi['z']))
            #d = numpy.linalg.norm(c1-c2)
            d = math.sqrt((system['coord_z'] - aoi['z']) ** 2 +
                          (system['coord_x'] - aoi['x']) ** 2 +
                          (system['coord_y'] - aoi['y']) ** 2)
            if d <= aoi['r']:
                self.aoistatr += 1
                # In AOI
                return False
        self.aoistatn += 1
        return True

    def __init__(self):
        # Object to hold filter options neatly
        # defaults as below
        # Multiple may be set, checked in order.
        self.allobjects = False          # If true load all objects
        #
        self.populated = True           # If true load populated objects
        self.unpopulated = False         # If trye load unpopulated objects
        #
        self.aoi = True                 # Areas of Interest
        self.aois = [                   # List of AOIs
            {'x': 0.0, 'y': 0.0, 'z': 0.0, 'r': 300},    # x,y,z of centre + dist of sphere in ly
            {'x': -9530.5, 'y': -910.28125, 'z': 19808.125, 'r': 100},  # Eol Prou RS-T d3-94
            {'x': -78.59375, 'y': -149.625, 'z': -340.53125, 'r': 100},  # Merope
                    ]
        self.aoistatx = 0
        self.aoistaty = 0
        self.aoistatz = 0
        self.aoistatr = 0
        self.aoistatn = 0



class EDACDB(object):
    # primary object
    def printaoistats(self):
        printdebug('AOI X exclusions: %d' % self.filteropt.aoistatx)
        printdebug('AOI Y exclusions: %d' % self.filteropt.aoistaty)
        printdebug('AOI Z exclusions: %d' % self.filteropt.aoistatz)
        printdebug('AOI Radius inclusion: %d' % self.filteropt.aoistatr)
        printdebug('AOI Fallthrough exclusions: %d' % self.filteropt.aoistatn)


    def startsystemidbulkmode(self):
        self.cache.systemids.startbulkmode()

    def endsystemidbulkmode(self):
        self.cache.systemids.endbulkmode()

    def duphash(self, data):
        data = str(data).encode('utf-8')
        #print(data)
        dig = hashlib.md5(data).digest()  # b']A@*\xbcK*v\xb9q\x9d\x91\x10\x17\xc5\x92'
        b64 = base64.b64encode(dig)       # b'XUFAKrxLKna5cZ2REBfFkg=='
        return b64.decode()[0:8]          # JSON doesn't like bytes it seems
                                          # XUFAKrxLKna5cZ2REBfFkg==
        #return hashlib.md5(data).digest().encode("base64")
        #return hashlib.md5(data).hexdigest()[0:15]
        #b'iMjj8tMyETkJqEszZ-dZJQ=='

    def create_fdevidmodule_in_db(self, moddict):
        # {'category': 'internal', 'edid': '128666704', 'class': '1',
        # 'rating': 'E', 'entitlement': '', 'guidance': '', 'ship': '',
        # 'mount': '', 'name': 'Frame Shift Drive Interdictor',
        # 'edsymbol': 'Int_FSDInterdictor_Size1_Class1'}
        # also eddbid
        # Need to do lookups to resolve related items
        # This for: group, ship, mount, guidance
        # Get category reference for group
        mycat = self.cache.modulecats.findoradd({
                    'name': moddict.pop('category')
                    })
        groupdict = {
            'name': moddict['group'],
            'category': mycat
        }
        # Get group ref
        moddict['group'] = self.cache.modulegroups.findoradd({
                                'name': moddict['group'],
                                'category': mycat
                                }
                            )
        # Tidy field ref (can't use 'class')
        moddict['cclass'] = moddict.pop('class')
        # optional fields
        if moddict['ship'] != '':         # '' == None ??
            moddict['ship'] = self.cache.shiptypes.getidbyname(
                                moddict['ship'])
            # Show error if ship not found
            if moddict['ship'] is None:
                printerror('Error importing module, associated ship not known.')
        if moddict['guidance'] is not '':         # '' == None ??
            moddict['guidance'] = self.cache.modguidances.findoradd(
                                    moddict['guidance'])
        if moddict['mount'] != '':         # '' == None ??
            moddict['mount'] = self.cache.modmounts.getidbyname(
                                    moddict['mount'])
        # Finally add or create the Module
        result = self.cache.modules.findoradd(moddict)
        if result is not None:
            return True
        else:
            return False

    def create_fdevidship_in_db(self, shipdict):
        result = self.cache.shiptypes.findoradd(shipdict)

    def create_eddb_commodity_in_db(self, commodity):
        '''
        {"id":4,"name":"Pesticides","category_id":1,
        "average_price":241,"is_rare":0,
        "category":{"id":1,"name":"Chemicals"}},
        ------->
        {"eddbid":4,"eddbname":"Pesticides","category":X,
        "average_price":241,"is_rare":0, "duphash": 'skjfdhjd'},
        '''
        # Eddb loader will replace id with eddbid
        # and name with eddbname
        commodity['category'] = self.cache.commoditycats.findoradd(
                                {'eddbid': commodity['category']['id'],
                                 'name': commodity['category']['name']
                                 })
        commodity.pop('category_id')    # no longer required
        hashdata = ""
        for key in sorted(commodity.keys()):
            hashdata += str(commodity[key])
        commodity['duphash'] = self.duphash(hashdata)
        result = self.cache.commodities.findoradd(commodity)

    def startstationbulkmode(self):
        # The order matters
        self.cache.stations.startbulkmode()
        self.cache.stationimports.startbulkmode()
        self.cache.stationexports.startbulkmode()
        self.cache.stationprohibited.startbulkmode()
        self.cache.stationeconomies.startbulkmode()
        self.cache.stationships.startbulkmode()
        self.cache.stationmodules.startbulkmode()

    def endstationbulkmode(self):
        # The order matters
        self.cache.stations.endbulkmode()
        self.cache.stationimports.endbulkmode()
        self.cache.stationexports.endbulkmode()
        self.cache.stationprohibited.endbulkmode()
        self.cache.stationeconomies.endbulkmode()
        self.cache.stationships.endbulkmode()
        self.cache.stationmodules.endbulkmode()

    def create_eddb_station_in_db(self, istation):
        station = copy.copy(istation)
        # Based on info from EDDB create or update a Station in DB
        #
        # Forign keys are system, faction, government, allegiance
        # state, stationtype
        if self.cache.systemids.eddbidexists(station['system_id']) is False:
            printerror('EDDB System ID (%d) is unknown in EDDB Station import.'
                       % station['system_id'])
            return False
        station['system'] = self.cache.systemids.getpkfromeddbid(station['system_id'])
        station.pop('system_id')
        # Do our lookups
        station['faction'] = self.cache.factions.findoradd(station['faction'])
        station['government'] = self.cache.governments.findoradd(station['government'])
        station['allegiance'] = self.cache.allegiances.findoradd(station['allegiance'])
        station['state'] = self.cache.sysstates.findoradd(station['state'])
        station['stationtype'] = self.cache.stationtypes.findoradd({
                                    'eddbid': station.pop('type_id'),
                                    'name': station.pop('type')
                                })
        # Make a hash, including join data values
        hashdata = ""
        for key in sorted(station.keys()):
            hashdata += str(station[key])
        station['duphash'] = self.duphash(hashdata)
        # Load the station (if required)
        newstationid = self.cache.stations.findoradd(station)
        if type(newstationid) is int:
            return False
        else:
            return True

    def create_eddb_stationjoins_in_db(self, istation):
        # Based on info from EDDB create or update a Station in DB
        #
        # Forign keys are system, faction, government, allegiance
        # state, stationtype
        # Make commodities                  # For new stations will require 2nd
                                            # run
        # Check for bulk station creation and cache readiness
        station = copy.copy(istation)
        newstationid = self.cache.stations.getpkfromeddbid(station['eddbid'])
        # Pop any lists we need separated
        imports = station.pop('import_commodities')
        exports = station.pop('export_commodities')
        prohibited = station.pop('prohibited_commodities')
        economies = station.pop('economies')
        selling_ships = station.pop('selling_ships')
        selling_modules = station.pop('selling_modules')
        # Note that the join caches must be at least partially loaded
        # otherwise there could be collisions, this should be done by cache
        # but needs our cooperation, in that the caller must bulk stop then
        # bulk start between station loads and station join loads
        changed = False
        if newstationid is not None:
            for ctype in [imports, exports, prohibited]:
                comdict = {
                    'station': newstationid,
                    'commodity': [
                        self.cache.commodities.getpkfromeddbname(commodity)
                        for commodity in ctype]
                }
                if ctype is imports:
                    result = self.cache.stationimports.findoradd(comdict)
                    # Warning this result is True, False or None
                    if result is True:
                        changed = True
                if ctype is exports:
                    result = self.cache.stationexports.findoradd(comdict)
                    # Warning this result is True, False or None
                    if result is True:
                        changed = True
                if ctype is prohibited:
                    result = self.cache.stationprohibited.findoradd(comdict)
                    # Warning this result is True, False or None
                    if result is True:
                        changed = True
            # Add economy joins
            ecodict = {
                    'station': newstationid,
                    'economy': [
                        self.cache.economies.findoradd(thiseconomy)
                        for thiseconomy in economies
                        ]
            }
            result = self.cache.stationeconomies.findoradd(ecodict)
            if result is True:
                changed = True
            # Warning this result is True, False or None
            # Add StationShip joins
            shipdict = {
                        'station': newstationid,
                        'shiptype': [
                            self.cache.shiptypes.getpkfromeddbname(shiptype)
                            for shiptype in selling_ships
                            ]
                        }
            result = self.cache.stationships.findoradd(shipdict)
            # Warning this result is True, False or None
            if result is True:
                changed = True
            # Add StationModule joins
            moddict = {
                        'station': newstationid,
                        'module': [
                            self.cache.modules.getidbyeddbid(module)
                            for module in selling_modules
                            ]   # This could contain Nones
                        }
            result = self.cache.stationmodules.findoradd(moddict)
            # Warning this result is True, False or None
            if result is True:
                changed = True
        return changed

    def startbodybulkmode(self):
        self.cache.bodies.startbulkmode()
        self.cache.atmoscomposition.startbulkmode()
        self.cache.solidcomposition.startbulkmode()
        self.cache.materialcomposition.startbulkmode()
        self.cache.rings.startbulkmode()

    def endbodybulkmode(self):
        self.cache.bodies.endbulkmode()
        self.cache.atmoscomposition.endbulkmode()
        self.cache.solidcomposition.endbulkmode()
        self.cache.materialcomposition.endbulkmode()
        self.cache.rings.endbulkmode()

    def create_eddb_body_in_db(self, ibody):
        # find or add will add to db if necessary and refresh
        # This replaces eddb lookups with our own
        # Simple bits first
        # Check if related system is in our DB
        # printdebug('Simple Lookups')
        body = copy.copy(ibody)
        if self.cache.systemids.eddbidexists(body['system_id']) is False:
            # We will ASSUME we chose not to load this
            # printerror('EDDB System ID (%d) is unknown in EDDB bodies import.'
            #           % body['system_id'])
            return False
        #
        body['system'] = self.cache.systemids.getpkfromeddbid(body['system_id'])
        body.pop('system_id')
        body['atmosphere_type_id'] = self.cache.atmostypes.findoradd(
                                       {'eddbid': body['atmosphere_type_id'],
                                        'name': body['atmosphere_type_name']
                                        })
        body.pop('atmosphere_type_name')
        body['group_id'] = self.cache.bodygroups.findoradd(
                                       {'eddbid': body['group_id'],
                                        'name': body['group_name']
                                        })
        body.pop('group_name')
        body['type_id'] = self.cache.bodytypes.findoradd(
                                       {'eddbid': body['type_id'],
                                        'name': body['type_name']
                                        })
        body.pop('type_name')
        body['volcanism_type_id'] = self.cache.volcanismtypes.findoradd(
                                       {'eddbid': body['volcanism_type_id'],
                                        'name': body['volcanism_type_name']
                                        })
        body.pop('volcanism_type_name')
        # Add body to DB if required:
        hashdata = ""
        for key in sorted(body.keys()):
            if type(body[key]) is list:
                for subitem in body[key]:
                    if type(subitem) is dict:
                        for subsubitem in sorted(subitem.keys()):
                            hashdata += str(subitem[subsubitem])
                    else:
                        hashdata += str(body[key])
            else:
                hashdata += str(body[key])
        body['duphash'] = self.duphash(hashdata)
        atmoscomposition = body.pop('atmosphere_composition')
        solidcomposition = body.pop('solid_composition')
        materials = body.pop('materials')
        rings = body.pop('rings')
        newitemid = self.cache.bodies.findoradd(body)
        if type(newitemid) is int:
            return False
        else:
            return True
        # print('Body ID: %d' % newitemid)

    def create_eddb_bodyjoins_in_db(self, ibody):
        body = copy.copy(ibody)
        # Now we have a reference ID for the system we can update the
        # Composition tables
        # Skip these if newitemid is None
        newitemid = self.cache.bodies.getpkfromeddbid(body['eddbid'])
        #TODO rewrite to list comprehensions like systems
        if newitemid is not None:
            atmoscomposition = body.pop('atmosphere_composition')
            # List of "atmosphere_composition":
            # [{"atmosphere_component_id":9,"share":91.2,
            #   "atmosphere_component_name":"Nitrogen"},
            #  {"atmosphere_component_id":10,"share":8.7,
            # "atmosphere_component_name":"Oxygen"},
            if len(atmoscomposition) > 0:
                # Ensure all the components exist
                for component in atmoscomposition:
                    component['atmosphere_component_id'] = self.cache.atmoscomponents.findoradd({
                        'eddbid': component['atmosphere_component_id'],
                        'name': component['atmosphere_component_name']
                        })
                    component.pop('atmosphere_component_name')
            #
            if len(atmoscomposition) > 0:
                # Ensure all the components exist
                for component in atmoscomposition:
                    self.cache.atmoscomposition.findoradd({
                        'component': component['atmosphere_component_id'],
                        'related_body': newitemid,
                        'share': component['share']
                    })
            #
            solidcomposition = body.pop('solid_composition')
            if len(solidcomposition) > 0:
                # Ensure all the components exist
                for component in solidcomposition:
                    component['solid_component_id'] = self.cache.solidtypes.findoradd({
                        'eddbid': component['solid_component_id'],
                        'name': component['solid_component_name']
                        })
                    component.pop('solid_component_name')
            #
            if len(solidcomposition) > 0:
                # Ensure all the components exist
                for component in solidcomposition:
                    self.cache.solidcomposition.findoradd({
                        'component': component['solid_component_id'],
                        'related_body': newitemid,
                        'share': component['share']
                    })
            #
            materials = body.pop('materials')
            if len(materials) > 0:
                # Ensure all the components exist
                for component in materials:
                    component['material_id'] = self.cache.materials.findoradd({
                        'eddbid': component['material_id'],
                        'name': component['material_name']
                        })
                    component.pop('material_name')
            #
            if len(materials) > 0:
                # Ensure all the components exist
                for component in materials:
                    self.cache.materialcomposition.findoradd({
                        'component': component['material_id'],
                        'related_body': newitemid,
                        'share': component['share']
                    })
            #
            rings = body.pop('rings')
            '''
            "rings":[{"id":23,"created_at":1466612897,"updated_at":1466612897,
                "name":"D Ring","semi_major_axis":0,"ring_type_id":1,
                "ring_mass":250560.2,"ring_inner_radius":74500,
                "ring_outer_radius":140180,"ring_type_name":"Icy"}]
            '''
            if len(rings) > 0:
                for ring in rings:
                    ring['ring_type'] = self.cache.ringtypes.findoradd({
                        'eddbid': ring['ring_type_id'],
                        'name': ring['ring_type_name'],
                        })
                    ring.pop('ring_type_id')
                    ring.pop('ring_type_name')
            #
            if len(rings) > 0:
                # Ensure all the components exist
                '''
                "rings":[{"id":23,"created_at":1466612897,"updated_at":1466612897,
                    "name":"D Ring","semi_major_axis":0,"ring_type_id":1,
                    "ring_mass":250560.2,"ring_inner_radius":74500,
                    "ring_outer_radius":140180,"ring_type_name":"Icy"}]
                '''
                for ring in rings:
                    ring['eddbid'] = ring.pop('id')
                    ring['eddb_created_at'] = ring.pop('created_at')
                    ring['eddb_updated_at'] = ring.pop('updated_at')
                    ring['related_body'] = newitemid
                    hashdata = ""
                    for key in sorted(ring.keys()):
                        hashdata += str(ring[key])
                    ring['duphash'] = self.duphash(hashdata)
                    result = self.cache.rings.findoradd(ring)

    def system_filter(self, system):
        # Checks if we want this system
        # We assume we don't
        if self.filteropt.allobjects is True:
            return False        # We want everything so get on with it
        if self.filteropt.populated is True:
            if system['is_populated'] is True:
                return False
        if self.filteropt.unpopulated is True:
            if system['is_populated'] is True:
                return False
        if self.filteropt.aoi is True:
            if self.filteropt.aoitest(system) is False:
                return False
        return True

    def create_system_in_db(self, system):
        # System is Dict
        # Everything is optional...
        # [edsmid], [edsmdate], [name], [coord_x], [coord_y], [coord_z],
        # [eddbid], [is_populated], [population], [simbad_ref], [needs_permit],
        # [eddbdate], [reserve_type], [security], [state], [allegiance],
        # [faction], [power], [government], [power_state], [primary_economy]
        # print("Creating a new system")
        # print(system)
        # Do we want this system?
        if self.system_filter(system) is True:
            return False
        # print('System accepted for load: %s' % system['name'].encode('utf-8'))
        # Do lookups
        # find or add will add to db if necessary and refresh
        system['security'] = self.cache.securitylevels.findoradd(system['security'])
        system['allegiance'] = self.cache.allegiances.findoradd(system['allegiance'])
        system['state'] = self.cache.sysstates.findoradd(system['state'])
        system['faction'] = self.cache.factions.findoradd(system['faction'])
        system['power'] = self.cache.powers.findoradd(system['power'])
        system['power_state'] = self.cache.powerstates.findoradd(system['power_state'])
        system['government'] = self.cache.governments.findoradd(system['government'])
        system['primary_economy'] = self.cache.economies.findoradd(system['primary_economy'])
        #print(system)
        #
        hashdata = ""
        for key in sorted(system.keys()):
            hashdata += str(system[key])
        system['duphash'] = self.duphash(hashdata)
        #print(system['hash'])
        # return True if updated or added, else False
        return self.cache.systemids.updateoradd(system)

    def factionpreload(self, faction):
        self.cache.bulkfactions.findoradd(faction)

    def factionpreload_flush(self):
        self.cache.bulkfactions.flushbulkupdate()
        # temp
        self.cache.factions.refresh()

    def __init__(
            self,
            dbapi=default_dbapi,
            bulkurl=default_bulkapi,
            cborurl=default_cborapi,
            username=default_username,
            password=default_password
            ):
        credentials_string = '%s:%s' % (username, password)
        auth_header = 'Basic ' + b64encode(credentials_string)
        domain = parse.urlsplit(dbapi).hostname
        # print(domain)
        credentials = {
            domain: auth_header
        }
        http_transport = coreapi.transports.HTTPTransport(credentials=credentials)
        self.client = coreapi.Client(transports=[http_transport])
        self.dbapi = dbapi
        self.bulkapi = {
            'url': bulkurl,
            'username': username,
            'password': password
        }
        self.schema = self.client.get(self.dbapi)
        self.bulkschema = self.client.get(self.bulkapi['url'])
        self.filteropt = SystemFilter()
        # print(self.schema)  # Ordered Dict of objects
        print(self.bulkschema)
        self.cache = DBCache(self.client, self.schema, self.bulkapi)
        # e.g.
        # OrderedDict([
        #    ('cmdrs', 'http://127.0.0.1:8000/edacapi/cmdrs/'),
        #    ('ships', 'http://127.0.0.1:8000/edacapi/ships/'),
        #    ('systems', 'http://127.0.0.1:8000/edacapi/systems/')
        #   ])
        '''
        print('Using actions')
        print(self.client.action(self.schema, ['cmdrs', 'list']))
        print("Create a new CMDR")
        params = {
            'UID': 'NEWGUY2.2',
            'name': 'NEWGUY',
            'version': '2.2',
        }
        try:
            self.client.action(self.schema, ['cmdrs', 'create'], params=params)
        except Exception as e:
            print(str(e))
        '''



        '''
        #
        print('Commanders Schema')
        print(self.schema['cmdrs'])
        self.cmdrs = self.client.get(self.schema['cmdrs'])
        print('Commanders')
        print(self.cmdrs)
        print('Get BIGGLES')
        myurl = '%s?name=%s' % (self.schema['cmdrbyname'], parse.quote('BIGGLES'))
        self.cmdrtest = self.client.get(myurl)
        print(self.cmdrtest)
        print('Get someone that doesnt exist')
        myurl = '%s?name=%s' % (self.schema['cmdrbyname'], parse.quote('BLUEBERRY'))
        self.cmdrtest = self.client.get(myurl)
        print(self.cmdrtest)
        print("Create a new CMDR")
        params = {
            'UID': 'NEWGUY2.2',
            'name': 'NEWGUY',
            'version': '2.2'
        }
        self.client.action(self.cmdrs, 'create')


        self.ships = self.client.get(self.schema['ships'])
        print('Ships')
        print(self.ships)
        self.systems = self.client.get(self.schema['systems'])
        print('Systems')
        print(self.systems)
        '''


if __name__ == '__main__':
    obj = EDACDB()
