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
try:
    from modules.edacdb_cache import DBCache
except:
    from edacdb_cache import DBCache

# Just using django runserver at the moment
default_dbapi = 'http://127.0.0.1:8000/edacapi/'
default_bulkapi = 'http://127.0.0.1:8000/edacapi/bulk/'
default_cborapi = 'http://127.0.0.1:8000/edacapi/bulk/cbor'
default_username = 'root'
default_password = 'password1234'

DEBUG = True
ERROR = True
VERSION = '2.2 Beta'


def printdebug(mystring):
    if DEBUG is True:
        print("DEBUG edacdb_wrapper: %s" % mystring)


def printerror(mystring):
    if ERROR is True:
        print("ERROR edacdb_wrapper: %s" % mystring)


class EDACDB(object):
    # primary object
    # http://www.coreapi.org/specification/document/

    def create_system_bulk_flush(self):
        # Should be called when using bulk update method
        # to ensure anything not sent is sent before object deleted
        self.cache.systemids.flushbulkupdate()

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
        self.cache.stations.startbulkmode()
        self.cache.stationcommodities.startbulkmode()
        self.cache.stationeconomies.startbulkmode()

    def endstationbulkmode(self):
        self.cache.stations.endbulkmode()
        self.cache.stationcommodities.endbulkmode()
        self.cache.stationeconomies.endbulkmode()

    def create_eddb_station_in_db(self, station):
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
        # Pop any lists we need separated
        imports = station.pop('import_commodities')
        exports = station.pop('export_commodities')
        prohibited = station.pop('prohibited_commodities')
        economies = station.pop('economies')
        selling_ships = station.pop('selling_ships')
        selling_modules = station.pop('selling_modules')
        #
        # TODO findoradd station
        hashdata = ""
        for key in sorted(station.keys()):
            hashdata += str(station[key])
        station['duphash'] = self.duphash(hashdata)
        newstationid = self.cache.stations.findoradd(station)
        # Make commodities                  # For new stations will require 2nd
                                            # run
        # temp
        if newstationid is not None:        # Allow for bulk station creation
            for ctype in [imports, exports, prohibited]:
                comdict = {
                    'station': newstationid,
                    'imported': ctype is imports,
                    'exported': ctype is exports,
                    'prohibited': ctype is prohibited,
                    'commodities': [
                        self.cache.commodities.getpkfromeddbname(commodity)
                        for commodity in ctype]
                }
                result = self.cache.stationcommodities.findoradd(comdict)
                # Warning this result is True, False or None

            # Add economy joins
            ecodict = {
                    'station': newstationid,
                    'economy': [
                        self.cache.economies.findoradd(thiseconomy)
                        for thiseconomy in economies
                        ]
            }
            result = self.cache.stationeconomies.findoradd(ecodict)
            # Warning this result is True, False or None


    def startbodybulkmode(self):
        self.cache.atmoscomposition.startbulkmode()
        self.cache.solidcomposition.startbulkmode()
        self.cache.materialcomposition.startbulkmode()
        self.cache.rings.startbulkmode()
        self.cache.bodies.startbulkmode()

    def endbodybulkmode(self):
        self.cache.atmoscomposition.endbulkmode()
        self.cache.solidcomposition.endbulkmode()
        self.cache.materialcomposition.endbulkmode()
        self.cache.rings.endbulkmode()
        self.cache.bodies.endbulkmode()

    def create_eddb_body_in_db(self, body):
        # find or add will add to db if necessary and refresh
        # This replaces eddb lookups with our own
        # Simple bits first
        # Check if related system is in our DB
        # printdebug('Simple Lookups')
        if self.cache.systemids.eddbidexists(body['system_id']) is False:
            printerror('EDDB System ID (%d) is unknown in EDDB bodies import.'
                       % body['system_id'])
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
        # printdebug('Compositions - Components')
        # OK Atmosphere Compositions
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
        materials = body.pop('materials')
        if len(materials) > 0:
            # Ensure all the components exist
            for component in materials:
                component['material_id'] = self.cache.materials.findoradd({
                    'eddbid': component['material_id'],
                    'name': component['material_name']
                    })
                component.pop('material_name')
        # Add body to DB if required:
        hashdata = ""
        for key in sorted(body.keys()):
            hashdata += str(body[key])
        body['duphash'] = self.duphash(hashdata)
        newitemid = self.cache.bodies.findoradd(body)
        # print('Body ID: %d' % newitemid)
        # Now we have a reference ID for the system we can update the
        # Composition tables
        # Skip these if newitemid is None (probably a bulk operation)
        if newitemid is not None:
            if len(atmoscomposition) > 0:
                # Ensure all the components exist
                for component in atmoscomposition:
                    self.cache.atmoscomposition.findoradd({
                        'component': component['atmosphere_component_id'],
                        'related_body': newitemid,
                        'share': component['share']
                    })
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
            if len(materials) > 0:
                # Ensure all the components exist
                for component in materials:
                    self.cache.materialcomposition.findoradd({
                        'component': component['material_id'],
                        'related_body': newitemid,
                        'share': component['share']
                    })
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


    def create_system_in_db(self, system):
        # System is Dict
        # Everything is optional...
        # [edsmid], [edsmdate], [name], [coord_x], [coord_y], [coord_z],
        # [eddbid], [is_populated], [population], [simbad_ref], [needs_permit],
        # [eddbdate], [reserve_type], [security], [state], [allegiance],
        # [faction], [power], [government], [power_state], [primary_economy]
        #print("Creating a new system")
        #print(system)
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
