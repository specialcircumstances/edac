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

DEBUG = True
ERROR = True
VERSION = '2.2 Beta'


def printdebug(mystring):
    if DEBUG is True:
        print("DEBUG edacdb_cache: %s" % mystring)


def printerror(mystring):
    if ERROR is True:
        print("ERROR edacdb_cache: %s" % mystring)


class CompositionBulkUpdateProcess(Process):
    # Based on https://pymotw.com/2/multiprocessing/communication.html
    # Also supports rings (HashedItemCache)
    # and bodies (BodyCache)
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
        printdebug('Starting run of %s for %s' % (proc_name, self.mylist))
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
                                                     # or 'delete'
                content = next_task.pop('content')
                if jobmode == 'create':
                    if jobtype == 'atmoscomposition':
                        result = self.slumapi.atmoscomposition.post(content)
                    elif jobtype == 'materialcomposition':
                        result = self.slumapi.materialcomposition.post(content)
                    elif jobtype == 'solidcomposition':
                        result = self.slumapi.solidcomposition.post(content)
                    elif jobtype == 'rings':
                        result = self.slumapi.rings.post(content)
                    elif jobtype == 'bodies':
                        result = self.slumapi.bodies.post(content)
                    elif jobtype == 'stations':
                        result = self.slumapi.stations.post(content)
                    elif jobtype == 'stationcommodities':
                        result = self.slumapi.stationcommodities.post(content)
                    elif jobtype == 'stationeconomies':
                        result = self.slumapi.stationeconomies.post(content)

                elif jobmode == 'update':
                    if jobtype == 'atmoscomposition':
                        result = self.slumapi.atmoscomposition.put(content)
                    elif jobtype == 'materialcomposition':
                        result = self.slumapi.materialcomposition.put(content)
                    elif jobtype == 'solidcomposition':
                        result = self.slumapi.solidcomposition.put(content)
                    elif jobtype == 'rings':
                        result = self.slumapi.rings.put(content)
                    elif jobtype == 'bodies':
                        result = self.slumapi.bodies.put(content)
                    elif jobtype == 'stations':
                        result = self.slumapi.stations.put(content)
                    elif jobtype == 'stationcommodities':
                        result = self.slumapi.stationcommodities.put(content)
                    elif jobtype == 'stationeconomies':
                        result = self.slumapi.stationeconomies.put(content)

                elif jobmode == 'delete':
                    if jobtype == 'stations':
                        result = self.slumapi.stations.put(content)
                    elif jobtype == 'stationcommodities':
                        result = self.slumapi.stationcommodities.delete(content)
                    elif jobtype == 'stationeconomies':
                        result = self.slumapi.stationeconomies.delete(content)
                else:
                    printerror('Composition Bulk Updater - Unknown Target')
                    result = 0
                self.result_queue.put(result)
            except Exception as exc:
                printerror('Error in %s for %s' % (proc_name, self.mylist))
                printerror('%s : %s : %s' % (jobmode, jobtype, content))
                printerror(exc)
                print("Unexpected error:", sys.exc_info()[0])
                # printerror(content)
                raise
            finally:
                self.task_queue.task_done()
                # Yes, even if the data is lost... just rerun...
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

    def addtobulkupdate(self, orignewsys, mode):
        newsys = copy.deepcopy(orignewsys)
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
        # clear the boards...
        self.eddb = {}
        self.edsm = {}
        self.duphash = {}
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
        # What I want are several lookup dictionaries
        eddbset = set([item['eddbid'] for item in mylist])
        self.eddb = dict.fromkeys(eddbset)  # Find by eddb
        del eddbset
        edsmset = set([item['edsmid'] for item in mylist])
        self.edsm = dict.fromkeys(edsmset)  # Find by edsm
        del edsmset
        duphashset = set([item['pk'] for item in mylist])
        self.duphash = dict.fromkeys(duphashset)   # Check if update required
        del duphashset
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

    # This could probably be refactored alongside Composition Cache
    def addtobulkupdate(self, origcomposition, mode):
        composition = copy.deepcopy(origcomposition)
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
                if self.bulkmode is True:
                    self.addtobulkupdate(body, 'create')
                    return None
                else:
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
                    if self.bulkmode is True:
                        body['id'] = body.pop('pk')   # ANNOYING!
                        self.addtobulkupdate(body, 'update')
                        return None
                    else:
                        newitem = self.client.action(self.schema,
                                                    [self.mylist, 'update'],
                                                    params=body)
                        self.addtocache(newitem)    # to update duphash
                except Exception as e:
                    printdebug('Exception in Body FoA update.')
                    printdebug(str(e))
                    printdebug(body)
                return dbid
            else:
                return dbid

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
            printerror('Body Cache %s Bulkmode already enabled'
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
            printdebug('Body Cache: Queuing complete. Waiting for DB commit.')
            self.bulkqueue.join()
            while self.resultqueue.empty() is not True:
                garbage = self.resultqueue.get()
            printdebug('Body Cache: DB committed.')
            for myid in range(0, self.bulkprocesses):
                self.bulkprocess[myid].join()
            printdebug('Flushed Body Cache Bulk Update Process.')
            self.bulkmode = False
            self.refresh()
        else:
            printerror('Body Cache %s Bulkmode not running.'
                       % self.mylist)

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

    def __init__(self, client, schema, bulkapi, mylist):
        printdebug('Loading %s Cache' % mylist)
        self.client = client
        self.schema = schema
        self.mylist = mylist
        self.bulkapi = bulkapi
        self.bulkmode = False
        self.eddb = {}
        self.edsm = {}
        self.duphash = {}
        self.refresh()
        # print(self.items)


class CompositionCache(object):
    # Composition Cache

    def addtobulkupdate(self, origcomposition, mode):
        composition = copy.deepcopy(origcomposition)
        if mode not in self.bulklist:
            self.bulklist[mode] = []
        if mode not in self.bulkcount:
            self.bulkcount[mode] = 0
        self.bulklist[mode].append(composition)
        self.bulkcount[mode] += 1
        if self.bulkcount[mode] > 8000:
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
        if body is None:
            return None
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
                if action == 'update':
                    myparams['id'] = myparams.pop('pk')   # ANNOYING!
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
            printerror('Exception in %s Composition Cache FoA' % self.mylist)
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


class StationCommodityCache(CompositionCache):
    # Inherit what I can
    def findoradd(self, indict):
        # Need to override this
        if type(indict) is dict:
            if 'station' not in indict:
                printerror('StationCommodityCache requires a station')
                return None
            if 'commodities' not in indict:
                printerror('StationCommodityCache requires commodities')
                return None
            elif indict['commodities'] == []:
                # empty list - ignore
                return None
        else:
            printerror('StationCommodityCache needs a dict please.')
            return None
        station = indict['station']
        if station is None:
            printerror('StationCommodityCache station is None.')
            return None
        myparams = {
            'station': station,
            'imported': False,
            'exported': False,
            'prohibited': False
        }
        if indict['imported'] is True:
            ctype = 'imported'
        elif indict['exported'] is True:
            ctype = 'exported'
        elif indict['prohibited'] is True:
            ctype = 'prohibited'
        else:
            printerror('StationCommodityCache ctype not recognised.')
            return None
        myparams[ctype] = True
        action = 'create'
        pklist = []
        if station in self.items:   # We already have this body in our cache
            if ctype in self.items[station]:
                if set(self.items[station][ctype].keys()
                        ) == set(indict['commodities']):
                    return False         # Yes I found it, but no update.
                else:
                    # We have no "update" action, we always delete
                    # and replace. Need a list of PKs to delete
                    pklist = [v for k, v in self.items[station][ctype].items()]
        try:
            # Delete the previous list if there is one
            for pk in pklist:
                if self.bulkmode is True:
                    mydelparams = pk
                    self.addtobulkupdate(mydelparams, 'delete')
                else:
                    self.client.action(
                                    self.schema,
                                    [self.mylist, 'delete'],
                                    params=pk)
            # Make the new one(s)
            for thiscomm in indict['commodities']:
                if thiscomm is None:
                    continue    # No point putting THAT in the DB
                myparams['commodity'] = thiscomm
                # print(thiscomm)
                if self.bulkmode is True:
                    # For these we need to delete (as above) and create new
                    # So we always create
                    self.addtobulkupdate(myparams, 'create')
                    # print('Bulk add myparams:')
                    # print(myparams)
                else:
                    odict = self.client.action(
                                    self.schema,
                                    [self.mylist, 'create'],
                                    params=myparams)
                    ostation = odict['station']
                    if odict['imported'] is True:
                        octype = 'imported'
                    elif odict['exported'] is True:
                        octype = 'exported'
                    elif odict['prohibited'] is True:
                        octype = 'prohibited'
                    else:
                        printerror('StationCommodityCache Unknown octype in DB.')
                        octype = 'prohibited'
                    ocommodity = odict['commodity']
                    if ostation not in self.items:
                        self.items[ostation] = {}
                    if ctype not in self.items[ostation]:
                        self.items[ostation][ctype] = {}
                    self.items[ostation][ctype][ocommodity] = odict['id']
            return True
        except Exception as e:
            printerror('Exception in %s StationCommodityCache FoA' % self.mylist)
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
                    # print(odict)
                    ostation = odict['station']
                    if odict['imported'] is True:
                        octype = 'imported'
                    elif odict['exported'] is True:
                        octype = 'exported'
                    elif odict['prohibited'] is True:
                        octype = 'prohibited'
                    else:
                        printerror('StationCommodityCache Unknown octype in DB.')
                        octype = 'unknown'
                    ocommodity = odict['commodity']
                    if ostation not in mydict:
                        # print('New Station %d' % ostation)
                        mydict[ostation] = {}
                    if octype not in mydict[ostation]:
                        mydict[ostation][octype] = {}
                        # print('New octype %s' % octype)
                    mydict[ostation][octype][ocommodity] = odict['id']
                    # print(mydict[ostation])
                    # time.sleep(0.2)
            offset += limit
        self.items = mydict

class StationJoinCache(CompositionCache):
    # Try to make this work for StationEconomy, StationShip and StationModule
    def findoradd(self, indict):
        # Need to override this
        if type(indict) is dict:
            if 'station' not in indict:
                printerror('StationJoinCache requires a station')
                return None
        else:
            printerror('StationJoinCache needs a dict please.')
            return None
        station = indict['station']
        if station is None:
            printerror('StationJoinCache station is None.')
            return None
        # Test for mode once
        if 'economy' in indict:
            lookupf = 'economy'
        elif 'ship' in indict:
            lookupf = 'ship'
        elif 'module' in indict:
            lookupf = 'module'
        else:
            printerror('FoA in StationJoinCache unknown/bad join table.')
            return None
        myparams = {
            'station': station,
        }
        action = 'create'
        pklist = []
        if station in self.items:   # We already have this body in our cache
            if set(self.items[station].keys()
                    ) == set(indict[lookupf]):
                # Note indict[lookupf] is a list but we need compare with
                # dict keys, in order, so use sets.
                return False         # Yes I found it, but no update required
            else:
                # We have no "update" action, we always delete
                # and replace. Need a list of PKs to delete
                pklist = [v for k, v in self.items[station].items()]
        try:
            # Delete the previous list if there is one
            for pk in pklist:
                if self.bulkmode is True:
                    mydelparams = pk
                    self.addtobulkupdate(mydelparams, 'delete')
                else:
                    self.client.action(
                                    self.schema,
                                    [self.mylist, 'delete'],
                                    params=pk)
            # Make the new one(s)
            for thisthing in indict[lookupf]:
                if thisthing is None:
                    continue    # No point putting THAT in the DB
                myparams[lookupf] = thisthing
                # print(thiscomm)
                if self.bulkmode is True:
                    # For these we need to delete (as above) and create new
                    # So we always create
                    self.addtobulkupdate(myparams, 'create')
                    # print('Bulk add myparams:')
                    # print(myparams)
                else:
                    odict = self.client.action(
                                    self.schema,
                                    [self.mylist, 'create'],
                                    params=myparams)
                    # Test for mode once
                    ostation = odict['station']
                    rthing = odict[lookupf]
                    if ostation not in odict:
                        odict[ostation] = {}
                    if rthing not in odict[ostation]:
                        odict[ostation][rthing] = odict['id']
                    else:
                        printerror('Duplicate in DB for StationJoin with %s'
                                    % rthing)
            return True
        except Exception as e:
            printerror('Exception in %s StationJoin FoA' % self.mylist)
            printerror(str(e))
            printerror(myparams)
            return None


    def refresh(self):
        mylist = self.client.action(self.schema, [self.mylist, 'list'])
        self.count = mylist['count']        # Get count of list
        limit = 10000
        offset = 0
        mydict = {}
        while offset < self.count:          # Get in batches of size: limit
            mylist = self.client.action(
                                self.schema,
                                [self.mylist, 'list'],
                                params={'limit': limit, 'offset': offset})
            if len(mylist['results']) > 0:
                # Test for mode once
                if 'economy' in mylist['results'][0]:
                    lookupf = 'economy'
                elif 'ship' in mylist['results'][0]:
                    lookupf = 'ship'
                elif 'module' in mylist['results'][0]:
                    lookupf = 'module'
                else:
                    printerror('Refresh in StationJoinCache unknown/bad join table.')
                    return None
                for odict in mylist['results']:
                    # print(odict)
                    ostation = odict['station']
                    thing = odict[lookupf]
                    if ostation not in mydict:
                        mydict[ostation] = {}
                    if thing not in mydict[ostation]:
                        mydict[ostation][thing] = odict['id']
                    else:
                        printerror('Duplicate in DB for StationJoin with %s'
                                    % thing)
            offset += limit
        self.items = mydict


class HashedItemCache(object):
    # This could probably be refactored alongside Composition Cache
    def getpkfromeddbid(self, eddbid):
        if eddbid in self.eddb:
            return self.eddb[eddbid]
        else:
            return None

    def getpkfromeddbname(self, name):
        if name in self.eddbname:
            return self.eddbname[name]
        else:
            return None

    def addtobulkupdate(self, composition, mode):
        if mode not in self.bulklist:
            self.bulklist[mode] = []
        if mode not in self.bulkcount:
            self.bulkcount[mode] = 0
        self.bulklist[mode].append(composition)
        self.bulkcount[mode] += 1
        if self.bulkcount[mode] > 8000:
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
            if myitem['eddbid'] in self.eddb:
                dbid = self.eddb[myitem['eddbid']]
        if dbid is None:
            try:
                if self.bulkmode is True:
                    self.addtobulkupdate(myitem, 'create')
                    return None
                else:
                    newitem = self.client.action(
                                    self.schema,
                                    [self.mylist, 'create'],
                                    params=myitem)
                    self.addtocache(newitem)
                    return newitem['pk']
            except Exception as e:
                printerror('Exception in %s HashItem FoA create.' % self.mylist)
                printerror(str(e))
                printerror(myitem)
                return None
        else:
            # check if we need to update
            if self.duphash[dbid] != myitem['duphash']:
                myitem['pk'] = dbid
                try:        # TODO make a bulk updater?
                    if self.bulkmode is True:
                        myitem['id'] = myitem.pop('pk')   # ANNOYING!
                        self.addtobulkupdate(myitem, 'update')
                        return None
                    else:
                        newitem = self.client.action(self.schema,
                                                     [self.mylist, 'update'],
                                                     params=myitem)
                        self.addtocache(newitem)    # to update duphash
                except Exception as e:
                    printerror('Exception in %s HashItem FoA create.'
                               % self.mylist)
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
                    if 'eddbname' in odict:
                        eddbname = odict['eddbname']
                    else:
                        eddbname = None
                    pk = odict['id']    # WHY IS THIS NOT PK ???????
                    if eddbid is not None:
                        self.eddb[eddbid] = pk
                    if eddbname is not None:
                        self.eddbname[eddbname] = pk
                    if duphash is not None:
                        self.duphash[pk] = duphash
            offset += limit
        # self.items = mydict

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
            printerror('Hashed Item Cache %s Bulkmode already enabled'
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
            printdebug('Hashed Item Cache: Queuing complete. Waiting for DB commit.')
            self.bulkqueue.join()
            while self.resultqueue.empty() is not True:
                garbage = self.resultqueue.get()
            printdebug('Hashed Item Cache: DB committed.')
            for myid in range(0, self.bulkprocesses):
                self.bulkprocess[myid].join()
            printdebug('Flushed Hashed Item Cache Bulk Update Process.')
            self.bulkmode = False
            self.refresh()
        else:
            printerror('Hashed Item Cache %s Bulkmode not running.'
                       % self.mylist)

    def __init__(self, client, schema, bulkapi, mylist):
        printdebug('Loading %s Hashed Cache' % mylist)
        self.client = client
        self.schema = schema
        self.mylist = mylist
        self.bulkapi = bulkapi
        self.bulkmode = False
        self.eddb = {}
        self.eddbname = {}
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
        self.rings = HashedItemCache(client, schema, bulkapi, 'rings')
        self.bodies = BodyCache(client, schema, bulkapi, 'bodies')
        self.solidtypes = ItemCache(client, schema, 'solidtypes')
        self.materials = ItemCache(client, schema, 'materials')
        # Composition Caches
        self.atmoscomposition = CompositionCache(client, schema, bulkapi, 'atmoscomposition')
        self.solidcomposition = CompositionCache(client, schema, bulkapi, 'solidcomposition')
        self.materialcomposition = CompositionCache(client, schema, bulkapi, 'materialcomposition')
        # Station related
        self.commoditycats = ItemCache(client, schema, 'commoditycats')
        self.commodities = HashedItemCache(client, schema, bulkapi, 'commodities')
        self.stationtypes = ItemCache(client, schema, 'stationtypes')
        self.stations = HashedItemCache(client, schema, bulkapi, 'stations')
        self.stationcommodities = StationCommodityCache(client, schema, bulkapi, 'stationcommodities')
        self.stationeconomies = StationJoinCache(client, schema, bulkapi, 'stationeconomies')
        #self.stationships = StationJoinCache(client, schema, bulkapi, 'stationships')
        #self.stationmodules = StationJoinCache(client, schema, bulkapi, 'stationmodules')
