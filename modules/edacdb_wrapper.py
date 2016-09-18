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
from multiprocessing import Process, Queue, JoinableQueue
from coreapi.compat import b64encode
from urllib import parse as parse

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



class SystemBulkUpdateProcess(Process):
    # Based on https://pymotw.com/2/multiprocessing/communication.html
    def __init__(self, slumapi, task_queue, result_queue):
        Process.__init__(self)
        self.slumapi = slumapi
        self.task_queue = task_queue
        self.result_queue = result_queue
        printdebug('Created System Bulk Update Process')

    def run(self):
        proc_name = self.name
        printdebug('Starting run of %s' % proc_name)
        while True:
            next_task = self.task_queue.get()
            if next_task is None:
                # Poison pill means shutdown
                printdebug('%s: Exiting' % proc_name)
                self.task_queue.task_done()
                self.result_queue.close()
                break
            # print('%s: %d' % (proc_name, len(next_task)))
            result = self.slumapi.systems.post(next_task)
            self.task_queue.task_done()
            self.result_queue.put(result)
        return


class FactionBulkUpdateProcess(Process):
    # Based on https://pymotw.com/2/multiprocessing/communication.html
    ''' NOT CURRENTLY USED '''
    def __init__(self, slumapi, task_queue, result_queue):
        Process.__init__(self)
        self.slumapi = slumapi
        self.task_queue = task_queue
        self.result_queue = result_queue
        printdebug('Created Faction Bulk Update Process')

    def run(self):
        proc_name = self.name
        printdebug('Starting run of %s' % proc_name)
        while True:
            next_task = self.task_queue.get()
            if next_task is None:
                # Poison pill means shutdown
                printdebug('%s: Exiting' % proc_name)
                self.task_queue.task_done()
                self.result_queue.close()
                break
            # print('%s: %d' % (proc_name, len(next_task)))
            result = self.slumapi.factions.post(next_task)
            self.task_queue.task_done()
            self.result_queue.put(result)
        return


class SystemIDImporter(Process):
    # Based on https://pymotw.com/2/multiprocessing/communication.html
    def __init__(self, client, schema, task_queue, result_queue):
        Process.__init__(self)
        self.client = client
        self.schema = schema
        self.task_queue = task_queue
        self.result_queue = result_queue
        printdebug('Created SystemIDImporter Process')

    def run(self):
        proc_name = self.name
        printdebug('Starting run of %s' % proc_name)
        while True:
            next_task = self.task_queue.get()
            if next_task is None:
                # Poison pill means shutdown
                printdebug('%s: Exiting' % proc_name)
                self.task_queue.task_done()
                self.result_queue.close()
                break
            # print('%s: %d' % (proc_name, len(next_task)))
            # TODO this is a little susceptable to issues server side.
            result = self.client.action(
                                self.schema,
                                [next_task['list'], 'list'],
                                params={'limit': next_task['limit'],
                                        'offset': next_task['offset']})
            self.task_queue.task_done()
            self.result_queue.put(result)
        return


class FactionCache(object):
    # There are quite a lot of these, so this can slow down bulk system
    # import, so add a bulk update method for Factions also.
    # The thing to watch here is that the Faction must be loaded before
    # the system...
    ''' THIS IS NOT CURRENTLY USED BECAUSE I NEED THE ID to populate the
    system records '''

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
            self.bulklist.append(myparams)
            self.bulkcount += 1
            if self.bulkcount > 256:
                self.bulkqueue.put(self.bulklist)
                self.bulklist = []
                self.bulkcount = 0
            # TODO update cache
            self.items[item] = 0   # Means I know it but not really

    def flushbulkupdate(self):
        # Empties any queue and tells process to end.
        # Can only be called once as it stops the process
        # Must be called for a clean close.
        self.bulkqueue.put(self.bulklist)
        for myid in range(0, self.bulkprocesses):
            self.bulkqueue.put(None)
        self.bulkqueue.close()
        printdebug('FactionCache: Queuing complete. Waiting for DB commit.')
        self.bulkqueue.join()
        while self.resultqueue.empty() is not True:
            garbage = self.resultqueue.get()
        printdebug('FactionCache: DB committed.')
        for myid in range(0, self.bulkprocesses):
            self.bulkprocess[myid].join()
        printdebug('Flushed Faction Bulk Update Process.')

    # As per the ItemCache, I could be cleverer with inheritence here
    def refresh(self):
        mylist = self.client.action(self.schema, [self.mylist, 'list'])
        self.count = mylist['count']
        limit = 10000
        offset = 0
        mydict = {}
        while offset < self.count:
            mylist = self.client.action(
                                self.schema,
                                [self.mylist, 'list'],
                                params={'limit': limit, 'offset': offset})
            if len(mylist) > 0:
                for odict in mylist['results']:
                    mydict[odict['name']] = odict['id']
            offset += limit
        self.items = mydict

    def __init__(self, client, schema, slumapi, mylist):
        printdebug('Loading Faction Cache')
        self.client = client
        self.schema = schema
        self.mylist = mylist
        self.slumapi = slumapi
        self.refresh()
        self.bulklist = []
        self.bulkcount = 0
        self.bulkthreads = 0
        self.bulkqueue = JoinableQueue()
        self.resultqueue = Queue()
        self.bulkprocesses = 2
        self.bulkprocess = {}
        # Create processes
        for myid in range(0, self.bulkprocesses):
            self.bulkprocess[myid] = FactionBulkUpdateProcess(
                                        self.slumapi,
                                        self.bulkqueue,
                                        self.resultqueue)
            self.bulkprocess[myid].start()
        #print(self.items)


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
        if self.bulkcount > 8000:
            # This hands it to other process via queue
            self.bulkqueue.put(self.bulklist)
            self.bulklist = []
            self.bulkcount = 0
            while self.bulkqueue.qsize() > self.bulkprocesses:
                # no point letting the queue get too big
                # This blocks
                time.sleep(0.1)
            # TODO update cache

    def flushbulkupdate(self):
        # Empties any queue and tells process to end.
        # Can only be called once as it stops the process
        # Must be called for a clean close.
        self.bulkqueue.put(self.bulklist)
        for myid in range(0, self.bulkprocesses):
            self.bulkqueue.put(None)    # One for each process?
        self.bulkqueue.close()
        printdebug('closed bulkqueue')
        self.bulkqueue.join()
        printdebug('bulkqueue join complete')
        while self.resultqueue.empty() is not True:
            garbage = self.resultqueue.get()
        for myid in range(0, self.bulkprocesses):
            self.bulkprocess[myid].join()
        printdebug('Flushed System Bulk Update Process.')

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
            self.addtobulkupdate(system)
            return True
        else:
            # check if we need to update
            if self.duphash[dbid] != system['duphash']:
                system['pk'] = dbid
                try:        # TODO make a bulk updater
                    newsys = self.client.action(self.schema, ['systems', 'update'], params=system)
                    self.addtocache(newsys)
                except Exception as e:
                    print(str(e))
                    print(system)
                return True
            else:
                return False

    '''
    Not required with CBOR method
    def readsysidfromqueue(self):
        mylist = self.idresultqueue.get()
        if len(mylist) > 0:
            for odict in mylist['results']:
                # print(odict)
                eddbid = odict['eddbid']
                edsmid = odict['edsmid']
                pk = odict['pk']
                if eddbid is not None:
                    self.eddb[eddbid] = pk
                if edsmid is not None:
                    self.edsm[edsmid] = pk
                self.duphash[pk] = odict['duphash']
                self.idsprocessed += 1
                timenow = int(time.clock() - self.timestart)
                srate = self.idsprocessed / timenow
                print('Processed %d systems (%d/s).             \r'
                      % (self.idsprocessed,
                         srate),
                      end='')
    '''

    def refresh(self):
        '''
        This version of refresh (our data getter) uses slumber and
        cbor to massively reduce the time it take to get a fresh copy
        of the SysID cache.
        '''
        printdebug('Requesting CBOR dump of System IDs')
        packedlist = self.cborapi.cborsystemids.get()
        printdebug('Reconstituting data structure')
        # Reconstruct the data
        mylist = []
        if len(packedlist) > 0:
            cols = packedlist[0]
            heads = packedlist[1:cols+1]
            mylist = [
                        {heads[il]:ol[il] for il in range(0, cols)}
                        for ol in packedlist[cols+1:]
                        ]
            # Done - now I have a list of dicts
        printdebug('Constructing lookup dicts')
        idsprocessed = 0
        # Optimisation
        # Precreate dicts using sets
        eddbset = set([item['eddbid'] for item in mylist])
        edsmset = set([item['edsmid'] for item in mylist])
        duphashset = set([item['duphash'] for item in mylist])
        # What I want are several lookup dictionaries
        self.eddb = dict.fromkeys(eddbset)  # Find by eddb
        self.edsm = dict.fromkeys(edsmset)  # Find by edsm
        self.duphash = dict.fromkeys(duphashset)   # Check if update required
        self.timestart = time.time()
        if len(mylist) > 0:
            for odict in mylist:
                # print(odict)
                eddbid = odict['eddbid']
                edsmid = odict['edsmid']
                pk = odict['pk']
                if eddbid is not None:
                    self.eddb[eddbid] = pk
                if edsmid is not None:
                    self.edsm[edsmid] = pk
                self.duphash[pk] = odict['duphash']
                idsprocessed += 1
                timenow = int(time.time() - self.timestart)
                srate = (idsprocessed + 1) / (timenow + 1)
                print('Processed %d systems (%d/s).             \r'
                      % (idsprocessed,
                         srate),
                      end='')
        self.sysidcount = idsprocessed



    '''
    Old version - too hard to use JSON  - too slow
    was all getting too complex...

    def refresh(self):
        mylist = self.client.action(self.schema, [self.mylist, 'list'])
        self.count = mylist['count']
        limit = 8000  # Number of records to try and get at once
        offset = 0
        self.idsprocessed = 0
        self.eddb = {}  # Find by eddb
        self.edsm = {}  # Find by edsm
        self.duphash = {}   # Check if update required
        # multiprocessing stuff
        self.idqueue = JoinableQueue()
        self.idresultqueue = Queue()
        self.idprocesses = 8
        self.idprocess = {}
        # Create processes
        for myid in range(0, self.idprocesses):
            self.idprocess[myid] = SystemIDImporter(
                                    self.client,
                                    self.schema,
                                    self.idqueue,
                                    self.idresultqueue)
            self.idprocess[myid].start()
        # Queue up request parameters
        while offset < self.count:
            task = {
                'list': self.mylist,
                'limit': limit,
                'offset': offset
            }
            self.idqueue.put(task)
            offset += limit
        # Create some poisoned pills
        for myid in range(0, self.idprocesses):
            self.idqueue.put(None)    # One for each process?
        self.idqueue.close()    # I won't write anymore
        # Now we wait for the processes to complete
        processesalive = True
        while processesalive is True:
            processesalive = False
            # See if any processes are still alive
            for myid in range(0, self.idprocesses):
                if self.idprocess[myid].is_alive():
                    processesalive = True
                    #printdebug('%d still alive' % myid)
            # dequeue and process results (may as well)
            if self.idresultqueue.empty() is not True:
                self.readsysidfromqueue()        # Process as we go
        while self.idresultqueue.empty() is not True:
            self.readsysidfromqueue()            # And the rest
        #
        printdebug('Waiting for all SysID retrievers to exit.')
        for myid in range(0, self.idprocesses):
            printdebug('Waiting for join: %d' % myid)
            self.idprocess[myid].join()      # One for each process?
        self.idresultqueue.close()
        self.idresultqueue.join_thread()
        self.idqueue.join()
        seconds = int(time.clock() - self.timestart)
        srate = self.idsprocessed / seconds
        printdebug('SysID Cache loaded (%d/s). Finally...' % srate)
    '''



    def __init__(self, client, schema, slumapi, cborapi, mylist):
        printdebug('Loading SysID Cache - this can take some time...')
        self.client = client
        self.schema = schema
        self.slumapi = slumapi
        self.cborapi = cborapi
        self.mylist = mylist
        self.sysidcount = 0
        self.bulklist = []
        self.bulkcount = 0
        self.bulkthreads = 0
        self.timestart = time.clock()
        self.refresh()
        self.bulkqueue = JoinableQueue()
        self.resultqueue = Queue()
        self.bulkprocesses = 4
        self.bulkprocess = {}
        # Create processes
        for myid in range(0, self.bulkprocesses):
            self.bulkprocess[myid] = SystemBulkUpdateProcess(
                                        self.slumapi,
                                        self.bulkqueue,
                                        self.resultqueue)
            self.bulkprocess[myid].start()
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
        self.count = mylist['count']
        limit = 10000
        offset = 0
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
        while offset < self.count:
            mylist = self.client.action(
                                self.schema,
                                [self.mylist, 'list'],
                                params={'limit': limit, 'offset': offset})
            if len(mylist) > 0:
                for odict in mylist['results']:
                    mydict[odict['name']] = odict['id']
            offset += limit
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

    def __init__(self, client, schema, slumapi, cborapi):
        self.systemids = SysIDCache(client, schema, slumapi, cborapi, 'systemids')
        self.securitylevels = ItemCache(client, schema, 'securitylevels')
        self.allegiances = ItemCache(client, schema, 'allegiances')
        self.sysstates = ItemCache(client, schema, 'sysstates')
        self.factions = ItemCache(client, schema, 'factions')
        self.powers = ItemCache(client, schema, 'powers')
        self.powerstates = ItemCache(client, schema, 'powerstates')
        self.governments = ItemCache(client, schema, 'governments')
        self.economies = ItemCache(client, schema, 'economies')
        self.bulkfactions = FactionCache(client, schema, slumapi, 'factions')


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
            bulkapi=default_bulkapi,
            cborurl=default_cborapi,
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
        self.cborurl = cborurl
        self.schema = self.client.get(self.dbapi)
        self.bulkschema = self.client.get(self.bulkapi)
        # Slumber Test
        self.slumapi = slumber.API(bulkapi, auth=(username, password))

        self.cborapi = slumber.API(cborurl,
                                   auth=(username, password)
                                  )
        print(self.schema)  # Ordered Dict of objects
        print(self.bulkschema)
        self.cache = DBCache(self.client, self.schema, self.slumapi, self.cborapi)
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
