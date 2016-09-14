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
import hashlib
import time
from multiprocessing import Process, Queue
from coreapi.compat import b64encode
from urllib import parse as parse

# Just using django runserver at the moment
default_dbapi = 'http://127.0.0.1:8000/edacapi/'
default_bulkapi = 'http://127.0.0.1:8000/edacapi/bulk/'
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


class SysIDCache(object):

    def addtocache(self, newsys):
        # We send pk but get id! grrr
        if 'id' in newsys.keys():
            newsys['pk'] = newsys['id']
        if newsys['eddbid'] is not None:
            self.eddb[newsys['eddbid']] = newsys['pk']
        if newsys['edsmid'] is not None:
            self.edsm[newsys['edsmid']] = newsys['pk']
        self.duphash[newsys['pk']] = newsys['duphash']

    def addtobulkupdate(self, newsys):
        self.bulklist.append(newsys)
        self.bulkcount += 1
        if self.bulkcount > 512:
            self.flushbulkupdate()


    def flushbulkupdate(self):
        #print('Attempting Bulk Update')
        #print(self.bulklist)
        #newsysb = self.client.action(self.bulkschema,
        #                            ['systems', 'create'],
        #                            params=self.bulklist)
        # Pass it to the queue
        #self.slumapi.systems.post(self.bulklist)
        self.bulkqueue.put(self.bulklist)
        self.bulklist = []
        self.bulkcount = 0
        print(self.bulkqueue.qsize())
        while self.bulkqueue.qsize() > 1:
            time.sleep(1)
        # TODO update cache

    def flushbulkqueue(self, myqueue):
        # Multiprocessing version
        self.slumapi.systems.post(myqueue.get())


    def updateoradd(self, system):
        # system in good state
        # Check if system is known
        dbid = None
        if system['eddbid'] is not None:
            if system['eddbid'] in self.eddb.keys():
                dbid = self.eddb[system['eddbid']]
            elif system['edsmid'] is not None:
                if system['edsmid'] in self.edsm.keys():
                    dbid = self.edsm[system['edsmid']]
        if dbid is None:
            # System not recognised by EDDB or EDSM id
            # TODO add coordinate checks for NEW systems!
            # So add system
            #try:
                #newsys = self.client.action(self.schema, ['systems', 'create'], params=system)
                #self.addtocache(newsys)
            self.addtobulkupdate(system)
            #except Exception as e:
            #    print(str(e))
            #    print(system)
        else:
            # check if we need to update
            if self.duphash[dbid] != system['duphash']:
                system['pk'] = dbid
                try:
                    newsys = self.client.action(self.schema, ['systems', 'update'], params=system)
                    self.addtocache(newsys)
                except Exception as e:
                    print(str(e))
                    print(system)


    def refresh(self):
        mylist = self.client.action(self.schema, [self.mylist, 'list'])
        '''
        Gives us a
        [OrderedDict([('id', 1), ('name', 'Low')]),
        OrderedDict([('id', 2), ('name', 'Medium')]),
        OrderedDict([('id', 3), ('name', 'HIgh')])]
        I want something simpler
        {'Low': 1, 'Medium': 2, 'HIgh': 3}
        I just want to see IDs for names
        '''
        self.eddb = {}  # Find by eddb
        self.edsm = {}  # Find by edsm
        self.duphash = {}   # Check if update required
        if len(mylist) > 0:
            for odict in mylist:
                #print(odict)
                if odict['eddbid'] is not None:
                    self.eddb[odict['eddbid']] = odict['pk']
                if odict['edsmid'] is not None:
                    self.edsm[odict['edsmid']] = odict['pk']
                self.duphash[odict['pk']] = odict['duphash']


    def __init__(self, client, schema, slumapi, mylist):
        printdebug('Loading SysID Cache')
        self.client = client
        self.schema = schema
        self.slumapi = slumapi
        self.mylist = mylist
        self.bulklist = []
        self.bulkcount = 0
        self.bulkthreads = 0
        self.refresh()
        self.bulkqueue = Queue()
        self.bulkprocess = Process(target=self.flushbulkqueue, args=(self.bulkqueue,))
        self.bulkprocess.start()
        #print(self.items)


class ItemCache(object):
    #

    def findoradd(self, item):
        if item is None:
                return None
        if item == 'None':
                return None
        if item == '':
                return None
        if item in self.items.keys():
            return self.items[item]
        else:
            myparams = {
                'name': item
            }
            try:
                newitem = self.client.action(
                                self.schema,
                                [self.mylist, 'create'],
                                params=myparams)
                # self.refresh() this too expensive when list is long
                # newitem might look like this
                # OrderedDict([('id', 2039),
                # ('name', 'Nationalists of Belarsuk'), ('reputaion', 'NEUTRAL')])
                self.items[newitem['name']] = newitem['id']
            except Exception as e:
                print(str(e))
                print(myparams)
            return self.items[item]

    def refresh(self):
        mylist = self.client.action(self.schema, [self.mylist, 'list'])
        '''
        Gives us a
        [OrderedDict([('id', 1), ('name', 'Low')]),
        OrderedDict([('id', 2), ('name', 'Medium')]),
        OrderedDict([('id', 3), ('name', 'HIgh')])]
        I want something simpler
        {'Low': 1, 'Medium': 2, 'HIgh': 3}
        I just want to see IDs for names
        '''
        mydict = {}
        if len(mylist) > 0:
            for odict in mylist:
                mydict[odict['name']] = odict['id']
        self.items = mydict

    def __init__(self, client, schema, mylist):
        printdebug('Loading %s Cache' % mylist)
        self.client = client
        self.schema = schema
        self.mylist = mylist
        self.refresh()
        #print(self.items)


class DBCache(object):
    # improve system import time

    def __init__(self, client, schema, slumapi):
        self.systemids = SysIDCache(client, schema, slumapi, 'systemids')
        self.securitylevels = ItemCache(client, schema, 'securitylevels')
        self.allegiances = ItemCache(client, schema, 'allegiances')
        self.sysstates = ItemCache(client, schema, 'sysstates')
        self.factions = ItemCache(client, schema, 'factions')
        self.powers = ItemCache(client, schema, 'powers')
        self.powerstates = ItemCache(client, schema, 'powerstates')
        self.governments = ItemCache(client, schema, 'governments')
        self.economies = ItemCache(client, schema, 'economies')


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
        return hashlib.md5(data).hexdigest()

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
        hashdata = ""
        for key in sorted(system.keys()):
            hashdata += str(system[key])
        system['duphash'] = self.duphash(hashdata)
        #print(system['hash'])
        self.cache.systemids.updateoradd(system)


    def __init__(
            self,
            dbapi=default_dbapi,
            bulkapi=default_bulkapi,
            username=default_username,
            password=default_password
            ):
        credentials_string = '%s:%s' % (username, password)
        auth_header = 'Basic ' + b64encode(credentials_string)
        domain = parse.urlsplit(dbapi).hostname
        #print(domain)
        credentials = {
            domain: auth_header
        }
        http_transport = coreapi.transports.HTTPTransport(credentials=credentials)
        self.client = coreapi.Client(transports=[http_transport])
        self.dbapi = dbapi
        self.bulkapi = bulkapi
        self.schema = self.client.get(self.dbapi)
        self.bulkschema = self.client.get(self.bulkapi)
        # Slumber Test
        self.slumapi = slumber.API(bulkapi, auth=(username, password))
        self.cache = DBCache(self.client, self.schema, self.slumapi)
        print(self.schema)  # Ordered Dict of objects
        print(self.bulkschema)
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
