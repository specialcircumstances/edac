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


class CompositionBulkUpdateProcess(Process):
    # Based on https://pymotw.com/2/multiprocessing/communication.html
    def __init__(self, bulkapi, mylist, task_queue, result_queue):
        Process.__init__(self)
        self.slumapi = slumber.API(bulkapi['url'],
                                   format='cbor',
                                   auth=(bulkapi['username'],
                                         bulkapi['password']))
        self.task_queue = task_queue
        self.result_queue = result_queue
        self.mylist = mylist
        printdebug('Created Composition Bulk Update Process for %s'
                   % self.mylist)

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
            try:
                # More complex this, need to pop type and mode from  next_task
                jobtype = next_task.pop('jobtype')     # 'atmos', 'materials', etc
                jobmode = next_task.pop('jobmode')   # 'update' or 'create'
                                                     # I think unnecessary at
                                                     # The moment
                content = next_task.pop('content')

                if jobtype == 'atmoscomposition':
                    result = self.slumapi.atmoscomposition.post(
                                content)
                elif jobtype == 'materialcomposition':
                    result = self.slumapi.materialcomposition.post(
                                content)
                elif jobtype == 'solidcomposition':
                    result = self.slumapi.solidcomposition.post(
                                content)
                else:
                    printerror('Composition Bulk Updater - Unknown Target')
                    result = 0
                self.result_queue.put(result)
            except Exception as exc:
                printerror(exc)
            finally:
                self.task_queue.task_done()
        return


class SystemBulkUpdateProcess(Process):
    # Based on https://pymotw.com/2/multiprocessing/communication.html
    def __init__(self, bulkapi, mode, task_queue, result_queue):
        Process.__init__(self)
        self.slumapi = slumber.API(bulkapi['url'],
                                   format='cbor',
                                   auth=(bulkapi['username'],
                                         bulkapi['password']))
        self.mode = mode
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
            try:
                if self.mode == 'create':
                    result = self.slumapi.bcreatesystems.post(next_task)
                else:
                    result = self.slumapi.bupdatesystems.post(next_task)
                self.result_queue.put(result)
            except Exception as exc:
                printerror(exc)
            finally:
                self.task_queue.task_done()
        return


class FactionBulkUpdateProcess(Process):
    # Based on https://pymotw.com/2/multiprocessing/communication.html

    def __init__(self, bulkapi, task_queue, result_queue):
        Process.__init__(self)
        self.slumapi = slumber.API(bulkapi['url'],
                                   format='cbor',
                                   auth=(bulkapi['username'],
                                         bulkapi['password']))
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

    def __init__(self, client, schema, bulkapi, mylist):
        printdebug('Loading Faction Cache')
        self.client = client
        self.schema = schema
        self.mylist = mylist
        self.bulkapi = bulkapi
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
                                        self.bulkapi,
                                        self.bulkqueue,
                                        self.resultqueue)
            self.bulkprocess[myid].start()
        #print(self.items)


class SysIDCache(object):

    def eddbidexists(self, eddbid):
        if eddbid in self.eddb:
            return True
        else:
            return False

    def getpkfromeddbid(self, eddbid):
        if eddbid in self.eddb:
            return self.eddb[eddbid]
        else:
            return None

    def addtocache(self, newsys):
        # We send pk but get id! grrr
        if 'id' in newsys.keys():
            newsys['pk'] = newsys['id']
        if newsys['eddbid'] is not None:
            self.eddb[newsys['eddbid']] = newsys['pk']
        if newsys['edsmid'] is not None:
            self.edsm[newsys['edsmid']] = newsys['pk']
        self.duphash[newsys['pk']] = newsys['duphash']

    def addtobulkupdate(self, newsys, mode):
        if mode == 'create':
            self.bulklist_create.append(newsys)
            self.bulkcount_create += 1
            if self.bulkcount_create > 8000:
                # This hands it to other process via queue
                self.bulkqueue_create.put(self.bulklist_create)
                self.bulklist_create = []
                self.bulkcount_create = 0
                while self.bulkqueue_create.qsize() > self.bulkprocesses:
                    # no point letting the queue get too big
                    # This blocks
                    time.sleep(0.1)
                # TODO update cache
        elif mode == 'update':
            self.bulklist_update.append(newsys)
            self.bulkcount_update += 1
            if self.bulkcount_update > 8000:
                # This hands it to other process via queue
                self.bulkqueue_update.put(self.bulklist_update)
                self.bulklist_update = []
                self.bulkcount_update = 0
                while self.bulkqueue_update.qsize() > self.bulkprocesses:
                    # no point letting the queue get too big
                    # This blocks
                    time.sleep(0.1)
                # TODO update cache

    def flushbulkupdate(self):
        # Empties any queue and tells process to end.
        # Can only be called once as it stops the process
        # Must be called for a clean close.
        self.bulkqueue_create.put(self.bulklist_create)
        self.bulkqueue_update.put(self.bulklist_update)
        for myid in range(0, self.bulkprocesses, 2):
            self.bulkqueue_create.put(None)    # One for each process?
            self.bulkqueue_update.put(None)    # One for each process?
        self.bulkqueue_create.close()
        self.bulkqueue_update.close()
        printdebug('closed bulkqueues')
        self.bulkqueue_create.join()
        self.bulkqueue_update.join()
        printdebug('bulkqueue joins complete')
        while self.resultqueue_create.empty() is not True:
            garbage = self.resultqueue_create.get()
        while self.resultqueue_update.empty() is not True:
            garbage = self.resultqueue_update.get()
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
            self.addtobulkupdate(system, 'create')
            return True
        else:
            # check if we need to update
            if self.duphash[dbid] != system['duphash']:
                system['pk'] = dbid
                self.addtobulkupdate(system, 'update')
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
        gc.collect()            # some items can be large
        bulkapi = self.bulkapi
        slumapi = slumber.API(bulkapi['url'],
                                   format='cbor',
                                   auth=(bulkapi['username'],
                                         bulkapi['password']))
        printdebug('Requesting CBOR dump of System IDs')
        packedlist = slumapi.cbor.cborsystemids.get()
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
        # free up the memory
        del packedlist
        printdebug('Pre-constructing lookup dicts')
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
        printdebug('Populating lookup dicts')
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
        printdebug('Processed %d systems (%d/s).' % (idsprocessed, srate))

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



    def __init__(self, client, schema, bulkapi, mylist):
        printdebug('Loading SysID Cache - this can take some time...')
        self.client = client
        self.schema = schema
        self.bulkapi = bulkapi
        self.mylist = mylist
        self.sysidcount = 0
        self.bulklist_create = []
        self.bulklist_update = []
        self.bulkcount_create = 0
        self.bulkcount_update = 0
        self.timestart = time.clock()
        self.refresh()
        self.bulkqueue_create = JoinableQueue()
        self.bulkqueue_update = JoinableQueue()
        self.resultqueue_create = Queue()
        self.resultqueue_update = Queue()
        self.bulkprocesses = 8
        self.bulkprocess = {}
        # Create processes
        for myid in range(0, self.bulkprocesses, 2):
            self.bulkprocess[myid] = SystemBulkUpdateProcess(
                                        self.bulkapi,
                                        'create',   # mode
                                        self.bulkqueue_create,
                                        self.resultqueue_create)
            self.bulkprocess[myid + 1] = SystemBulkUpdateProcess(
                                        self.bulkapi,
                                        'update',   # mode
                                        self.bulkqueue_update,
                                        self.resultqueue_update)
            self.bulkprocess[myid].start()
            self.bulkprocess[myid + 1].start()
        #print(self.items)


class BodyCache(object):
    #

    def addtocache(self, newsys):
        # We send pk but get id! grrr
        if 'id' in newsys.keys():
            newsys['pk'] = newsys['id']
        if newsys['eddbid'] is not None:
            self.eddb[newsys['eddbid']] = newsys['pk']
        if newsys['edsmid'] is not None:
            self.edsm[newsys['edsmid']] = newsys['pk']
        self.duphash[newsys['pk']] = newsys['duphash']

    def findoradd(self, body):
        dbid = None
        if body['eddbid'] is not None:
            if body['eddbid'] in self.eddb.keys():
                dbid = self.eddb[body['eddbid']]
            elif 'edsmid' in body:
                if body['edsmid'] is not None:
                    if body['edsmid'] in self.edsm.keys():
                        dbid = self.edsm[body['edsmid']]
        if dbid is None:
            try:
                newitem = self.client.action(
                                self.schema,
                                [self.mylist, 'create'],
                                params=body)
                self.addtocache(newitem)
                return newitem['pk']
            except Exception as e:
                print('Exception in Body FoA create.')
                print(str(e))
                print(body)
                return None
        else:
            # check if we need to update
            if self.duphash[dbid] != body['duphash']:
                body['pk'] = dbid
                try:        # TODO make a bulk updater?
                    newitem = self.client.action(self.schema,
                                                [self.mylist, 'update'],
                                                params=body)
                    self.addtocache(newitem)    # to update duphash
                except Exception as e:
                    print('Exception in Body FoA update.')
                    print(str(e))
                    print(body)
                return dbid
            else:
                return dbid

    def refresh(self):
        mylist = self.client.action(self.schema, [self.mylist, 'list'])
        self.count = mylist['count']
        limit = 10000
        offset = 0
        # mydict = {}
        while offset < self.count:
            mylist = self.client.action(
                                self.schema,
                                [self.mylist, 'list'],
                                params={'limit': limit, 'offset': offset})
            if len(mylist) > 0:
                for odict in mylist['results']:
                    # print(odict)
                    eddbid = odict['eddbid']
                    edsmid = odict['edsmid']       # Does EDSM track bodies?
                    duphash = odict['duphash']
                    pk = odict['id']    # WHY IS THIS NOT PK ???????
                    if eddbid is not None:
                        self.eddb[eddbid] = pk
                    if edsmid is not None:
                        self.edsm[edsmid] = pk
                    if duphash is not None:
                        self.duphash[pk] = duphash
            offset += limit
        # self.items = mydict

    def __init__(self, client, schema, mylist):
        printdebug('Loading %s Cache' % mylist)
        self.client = client
        self.schema = schema
        self.mylist = mylist
        self.eddb = {}
        self.edsm = {}
        self.duphash = {}
        self.refresh()
        # print(self.items)


class CompositionCache(object):
    # Composition Cache

    def addtobulkupdate(self, composition, mode):
        if mode not in self.bulklist:
            self.bulklist[mode] = []
        if mode not in self.bulkcount:
            self.bulkcount[mode] = 0
        self.bulklist[mode].append(composition)
        self.bulkcount[mode] += 1
        if self.bulkcount[mode] > 1000:
            # This hands in bulk to other process via queue
            # wrap up in dict to indicate target in API
            mydict = {}
            mydict['content'] = self.bulklist[mode]
            mydict['jobtype'] = self.mylist
            mydict['jobmode'] = mode
            self.bulkqueue.put(mydict)
            self.bulklist[mode] = []
            self.bulkcount[mode] = 0
            while self.bulkqueue.qsize() > self.bulkprocesses:
                # no point letting the queue get too big
                # This blocks
                time.sleep(0.1)
            # TODO update cache

    def findoradd(self, indict):
        if type(indict) is dict:
            if 'related_body' in indict:
                # Means we have a dict containing a body reference
                if 'component' in indict:
                    # and a component
                    if 'share' in indict:
                        pass
                    else:
                        printerror('CompositionCache requires a share')
                        return None
                else:
                    printerror('CompositionCache requires a component')
                    return None
            else:
                # Unsupported dict
                printerror('CompositionCache requires a related_body')
                return None
        else:
            printerror('Composition Cache needs a dict please.')
            return None
        body = indict['related_body']
        comp = indict['component']
        share = indict['share']
        action = 'create'
        if body in self.items:   # We already have this body in our cache
            if comp in self.items[body]:
                if self.items[body][comp]['share'] == share:
                    return self.items[body][comp]['id']
                else:
                    action = 'update'  # Update existing
        myparams = {
            'component': comp,
            'related_body': body,
            'share': share
        }
        if action == 'update':
            myparams['pk'] = self.items[body][comp]['id']
        try:
            if self.bulkmode is True:
                self.addtobulkupdate(myparams, action)
                return None
            else:
                odict = self.client.action(
                                self.schema,
                                [self.mylist, action],
                                params=myparams)
                body = odict['related_body']
                comp = odict['component']
                share = odict['share']
                pk = odict['id']
                if body not in self.items:
                    self.items[body] = {}
                self.items[body][comp] = {'share': share, 'id': pk}
                return self.items[body][comp]['id']
        except Exception as e:
            printerror('Exception in Component Cache FoA')
            printerror(str(e))
            printerror(myparams)
            return None

    def refresh(self):
        mylist = self.client.action(self.schema, [self.mylist, 'list'])
        self.count = mylist['count']
        limit = 10000
        offset = 0
        '''
        I get a list of dicts with component, related_body and share
        I was a dict of related_body with dicts of components containing shares
        and the pk - might the pk for updates off share values (WTF?)
        '''
        mydict = {}
        while offset < self.count:
            mylist = self.client.action(
                                self.schema,
                                [self.mylist, 'list'],
                                params={'limit': limit, 'offset': offset})
            if len(mylist) > 0:
                for odict in mylist['results']:
                    body = odict['related_body']
                    comp = odict['component']
                    share = odict['share']
                    pk = odict['id']
                    if body not in mydict:
                        mydict[body] = {}
                    mydict[body][comp] = {'share': share, 'id': pk}
            offset += limit
        self.items = mydict

    def startbulkmode(self):
        # Start Bulk Upload processes
        if self.bulkmode is False:
            self.bulklist = {}  # Dict for different batch types
            self.bulkcount = {}
            self.bulkqueue = JoinableQueue()
            self.resultqueue = Queue()
            self.bulkprocesses = 2
            self.bulkprocess = {}
            # Create processes
            for myid in range(0, self.bulkprocesses):
                self.bulkprocess[myid] = CompositionBulkUpdateProcess(
                                            self.bulkapi,
                                            self.mylist,
                                            self.bulkqueue,
                                            self.resultqueue)
                self.bulkprocess[myid].start()
            self.bulkmode = True
        else:
            printerror('Composition Cache %s Bulkmode already enabled'
                       % self.mylist)

    def endbulkmode(self):
        # Start Bulk Upload processes
        if self.bulkmode is True:
            for mode in self.bulklist:
                mydict = {}
                mydict['content'] = self.bulklist[mode]
                mydict['jobtype'] = self.mylist
                mydict['jobmode'] = mode
                self.bulkqueue.put(mydict)
            for myid in range(0, self.bulkprocesses):
                self.bulkqueue.put(None)
            self.bulkqueue.close()
            printdebug('Composition Cache: Queuing complete. Waiting for DB commit.')
            self.bulkqueue.join()
            while self.resultqueue.empty() is not True:
                garbage = self.resultqueue.get()
            printdebug('Composition Cache: DB committed.')
            for myid in range(0, self.bulkprocesses):
                self.bulkprocess[myid].join()
            printdebug('Flushed Composition Cache Bulk Update Process.')
            self.bulkmode = False
            self.refresh()
        else:
            printerror('Composition Cache %s Bulkmode not running.'
                       % self.mylist)

    def __init__(self, client, schema, bulkapi, mylist):
        printdebug('Loading %s Cache' % mylist)
        self.client = client
        self.schema = schema
        self.mylist = mylist
        self.bulkapi = bulkapi
        self.bulkmode = False
        self.refresh()
        #print(self.items)


class HashedItemCache(object):
    #

    def addtocache(self, newitem):
        # We send pk but get id! grrr
        if 'id' in newitem:
            newitem['pk'] = newitem['id']
        if newitem['eddbid'] is not None:
            self.eddb[newitem['eddbid']] = newitem['pk']
        self.duphash[newitem['pk']] = newitem['duphash']

    def findoradd(self, myitem):
        dbid = None
        if myitem['eddbid'] is not None:
            if myitem['eddbid'] in self.eddb.keys():
                dbid = self.eddb[myitem['eddbid']]
        if dbid is None:
            try:
                newitem = self.client.action(
                                self.schema,
                                [self.mylist, 'create'],
                                params=myitem)
                self.addtocache(newitem)
                return newitem['pk']
            except Exception as e:
                printerror('Exception in HashItem FoA create.')
                printerror(str(e))
                printerror(myitem)
                return None
        else:
            # check if we need to update
            if self.duphash[dbid] != myitem['duphash']:
                myitem['pk'] = dbid
                try:        # TODO make a bulk updater?
                    newitem = self.client.action(self.schema,
                                                 [self.mylist, 'update'],
                                                 params=myitem)
                    self.addtocache(newitem)    # to update duphash
                except Exception as e:
                    printerror('Exception in HashItem FoA update.')
                    printerror(str(e))
                    printerror(myitem)
                return dbid
            else:
                return dbid

    def refresh(self):
        mylist = self.client.action(self.schema, [self.mylist, 'list'])
        self.count = mylist['count']
        limit = 10000
        offset = 0
        # mydict = {}
        while offset < self.count:
            mylist = self.client.action(
                                self.schema,
                                [self.mylist, 'list'],
                                params={'limit': limit, 'offset': offset})
            if len(mylist) > 0:
                for odict in mylist['results']:
                    # print(odict)
                    eddbid = odict['eddbid']
                    duphash = odict['duphash']
                    pk = odict['id']    # WHY IS THIS NOT PK ???????
                    if eddbid is not None:
                        self.eddb[eddbid] = pk
                    if duphash is not None:
                        self.duphash[pk] = duphash
            offset += limit
        # self.items = mydict

    def __init__(self, client, schema, mylist):
        printdebug('Loading %s Hashed Cache' % mylist)
        self.client = client
        self.schema = schema
        self.mylist = mylist
        self.eddb = {}
        self.duphash = {}
        self.refresh()
        # print(self.items)


class ItemCache(object):
    # Default Item Cache, suitable for most items.

    def findoradd(self, initem):
        isdict = False
        iseddblookup = False
        if type(initem) is dict:
            isdict = True
            if 'eddbid' in initem:
                # Means we have a dict containing eddbid and name
                # for the various lookup tables we mirror
                iseddblookup = True
                item = initem['eddbid']
            else:
                # Unsupported dict
                printerror('ItemCache does not support this dictionary')
                printerror(initem)
                return None
        else:
            # assume single item is name
            item = initem
        if item is None:
                return None
        if item == 'None':
                return None
        if item == '':
                return None
        if item in self.items.keys():   # We already have this in our cache
            return self.items[item]
        else:
            if iseddblookup is True:
                myparams = {
                    'eddbid': item,
                    'name': initem['name']
                }
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
                if iseddblookup is True:
                    self.items[newitem['eddbid']] = newitem['id']
                else:
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
                    if 'eddbid' in odict:
                        mydict[odict['eddbid']] = odict['id']
                    else:
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

    def __init__(self, client, schema, bulkapi):
        # Systems Caches (not exclusively)
        self.systemids = SysIDCache(client, schema, bulkapi, 'systemids')
        self.securitylevels = ItemCache(client, schema, 'securitylevels')
        self.allegiances = ItemCache(client, schema, 'allegiances')
        self.sysstates = ItemCache(client, schema, 'sysstates')
        self.factions = ItemCache(client, schema, 'factions')
        self.powers = ItemCache(client, schema, 'powers')
        self.powerstates = ItemCache(client, schema, 'powerstates')
        self.governments = ItemCache(client, schema, 'governments')
        self.economies = ItemCache(client, schema, 'economies')
        self.bulkfactions = FactionCache(client, schema, bulkapi, 'factions')
        # Bodies Caches
        self.atmostypes = ItemCache(client, schema, 'atmostypes')
        self.atmoscomponents = ItemCache(client, schema, 'atmoscomponents')
        self.bodygroups = ItemCache(client, schema, 'bodygroups')
        self.bodytypes = ItemCache(client, schema, 'bodytypes')
        self.volcanismtypes = ItemCache(client, schema, 'volcanismtypes')
        self.ringtypes = ItemCache(client, schema, 'ringtypes')
        self.rings = HashedItemCache(client, schema, 'rings')
        self.bodies = BodyCache(client, schema, 'bodies')
        self.solidtypes = ItemCache(client, schema, 'solidtypes')
        self.materials = ItemCache(client, schema, 'materials')
        # Composition Caches
        self.atmoscomposition = CompositionCache(client, schema, bulkapi, 'atmoscomposition')
        self.solidcomposition = CompositionCache(client, schema, bulkapi, 'solidcomposition')
        self.materialcomposition = CompositionCache(client, schema, bulkapi, 'materialcomposition')





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

    def startbodybulkmode(self):
        self.cache.atmoscomposition.startbulkmode()
        self.cache.solidcomposition.startbulkmode()
        self.cache.materialcomposition.startbulkmode()

    def endbodybulkmode(self):
        self.cache.atmoscomposition.endbulkmode()
        self.cache.solidcomposition.endbulkmode()
        self.cache.materialcomposition.endbulkmode()

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
                if result is None:
                    printerror('Could not findadd ring.')
                    printerror(ring)
                    printerror(body)
        #



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
        #print(domain)
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

        #print(self.schema)  # Ordered Dict of objects
        #print(self.bulkschema)
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
