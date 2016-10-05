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


def printdebug(mystring, inplace=False):
    if DEBUG is True:
        if inplace is True:
            print("DEBUG edacdb_cache: %s                             \r"
                  % mystring, end='')
        else:
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
                printdebug('%s-%s: Exiting' % (proc_name, self.mylist))
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
                    elif jobtype == 'stationimports':
                        result = self.slumapi.stationimports.post(content)
                    elif jobtype == 'stationexports':
                        result = self.slumapi.stationexports.post(content)
                    elif jobtype == 'stationprohibited':
                        result = self.slumapi.stationprohibited.post(content)
                    elif jobtype == 'stationeconomies':
                        result = self.slumapi.stationeconomies.post(content)
                    elif jobtype == 'stationships':
                        result = self.slumapi.stationships.post(content)
                    elif jobtype == 'stationmodules':
                        result = self.slumapi.bstationmodules.post(content)
                    elif jobtype == 'systemids':
                        result = self.slumapi.bcreatesystems.post(content)
                    else:
                        printerror('Composition Bulk Updater - Unknown Target')
                        result = 0

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
                    elif jobtype == 'stationimports':
                        result = self.slumapi.stationimports.put(content)
                    elif jobtype == 'stationexports':
                        result = self.slumapi.stationexports.put(content)
                    elif jobtype == 'stationprohibited':
                        result = self.slumapi.stationprohibited.put(content)
                    elif jobtype == 'stationeconomies':
                        result = self.slumapi.stationeconomies.put(content)
                    elif jobtype == 'stationships':
                        result = self.slumapi.stationships.put(content)
                    elif jobtype == 'stationmodules':
                        result = self.slumapi.bstationmodules.put(content)
                    elif jobtype == 'systemids':
                        result = self.slumapi.bupdatesystems.post(content)
                        # TODO bring this more into line
                    else:
                        printerror('Composition Bulk Updater - Unknown Target')
                        result = 0

                elif jobmode == 'delete':
                    if jobtype == 'stations':
                        result = self.slumapi.stations.delete(content)
                    elif jobtype == 'stationimports':
                        result = self.slumapi.stationimports.delete(content)
                    elif jobtype == 'stationexports':
                        result = self.slumapi.stationexports.delete(content)
                    elif jobtype == 'stationprohibited':
                        result = self.slumapi.stationprohibited.delete(content)
                    elif jobtype == 'stationeconomies':
                        result = self.slumapi.stationeconomies.delete(content)
                    elif jobtype == 'stationships':
                        result = self.slumapi.stationships.delete(content)
                    elif jobtype == 'stationmodules':
                        result = self.slumapi.stationmodules.delete(content)
                    else:
                        printerror('Composition Bulk Updater - Unknown Target')
                        result = 0

                else:
                    printerror('Composition Bulk Updater - Unknown Target')
                    result = 0
                self.result_queue.put(result)
            except Exception as exc:
                printerror('Error in %s for %s' % (proc_name, self.mylist))
                #printerror('%s : %s : %s' % (jobmode, jobtype, content))
                printerror('%s : %s' % (jobmode, jobtype))
                printerror(exc)
                exctype, value = sys.exc_info()[:2]
                print("Unexpected error: %s :: %s" % (exctype, value))
                # printerror(content)
                # raise
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


class CBORJoinCache(object):
    # Refactoring other items
    # This is now a base for many classes

    def addtobulkupdate(self, origitem, mode):
        thisitem = copy.deepcopy(origitem)
        # We can signal the record needs refreshing later here
        if (self.partialfield is not None) and (mode != 'delete'):
            if self.partialfield in thisitem:
                self.partiallist.append(thisitem[self.partialfield])
        #
        if mode not in self.bulklist:
            self.bulklist[mode] = []
        if mode not in self.bulkcount:
            self.bulkcount[mode] = 0
        self.bulklist[mode].append(thisitem)
        self.bulkcount[mode] += 1
        if self.bulkcount[mode] > self.bulklimit:    # Higher as these are small records
            # We need to make sure that if there is any delete queue
            # that it is processed first.
            if 'delete' in self.bulklist:
                if len(self.bulklist['delete']) > 0:
                    mydictd = {}
                    mydictd['content'] = self.bulklist['delete']
                    mydictd['jobtype'] = self.mylist
                    mydictd['jobmode'] = 'delete'
                    self.bulkqueue.put(mydictd)
                    self.bulklist['delete'] = []
                    self.bulkcount['delete'] = 0
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

    def clearcache(self):
        self.items = {}

    def precreate(self, mylist):
        return

    def cacheloaditem(self, odict):
        # we must have a pk/id and a station
        # these items use pk
        printerror('cacheloaditem not defined for object attached to  %s'
                    % self.mylist)

    def getitemstorefresh(self):
        # Returns a dictionary. Called by a partial refresh
        # self.partialfield and self.partiallist should probably be
        # set explicitly.
        mydict = {
            'lookupkey': self.partialfield,
            'valuelist': self.partiallist,
        }
        printdebug('There are %d items in %s partial list. Lookup is: %s'
              % (len(self.partiallist), self.mylist, self.partialfield))
        return mydict

    def refresh(self, partial=False):
        bulkapi = self.bulkapi
        slumapi = slumber.API(bulkapi['url'],
                              format='cbor',
                              auth=(bulkapi['username'],
                              bulkapi['password']))
        response = getattr(slumapi.cbor, self.mylist).get(
                            offset=0, limit=1)
        count = response['count']       # Total number of records
        totalcount = 0
        limit = 500000                  # These are small records, get lots
        offset = 0                      # Start here
        if partial is True:
            printdebug('Fetching packed CBOR partial dump of %s' % self.mylist)
            rdict = self.getitemstorefresh()
            myfield = rdict['lookupkey']
            myvalues = rdict['valuelist']
            partialcount = len(myvalues)
            partialoffset = 0
            partiallimit = 1000     # Step through in chunks
        else:
            printdebug('Fetching packed CBOR dump of %s' % self.mylist)
            partialcount = 1
            partialoffset = 0
            self.clearcache()
        while (offset < count) and (partialoffset < partialcount):
            printdebug('Please wait. Loading. Loaded %d of %d....' % (
                    offset, count), inplace=True)
            if partial is True:
                # get chunk of values
                endlimit = partialoffset + partiallimit
                valuechunk = myvalues[partialoffset:endlimit]
                #
                response = getattr(slumapi.cbor, self.mylist).get(
                                offset=offset, limit=limit,
                                field=myfield, v=valuechunk)
                count = response['count']
            else:
                response = getattr(slumapi.cbor, self.mylist).get(
                                offset=offset, limit=limit)
            packedlist = response['results']
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
            del packedlist      # free up the memory
            idsprocessed = 0
            # Populate dict
            if len(mylist) > 0:
                totalcount += len(mylist)
                self.precreate(mylist)
                for odict in mylist:
                    self.cacheloaditem(odict)
            if partial is True:
                printdebug('offset: %d, limit: %d, count: %d'
                            % (offset, limit, count))
                printdebug('Partial mode: adding offset')
                offset += limit
                if offset > count:
                    printdebug('Partial mode: resetting offset for next chunk')
                    printdebug('partialoffset: %d, partiallimit: %d'
                                % (partialoffset, partiallimit))
                    partialoffset += partiallimit
                    offset = 0
            else:
                offset += limit
        printdebug('Load complete. Loaded %d records.                ' % totalcount)

    def startbulkmode(self):
        # Start Bulk Upload processes
        if self.bulkmode is False:
            self.bulklist = {}  # Dict for different batch types
            self.bulkcount = {}
            self.bulkqueue = JoinableQueue()
            self.resultqueue = Queue()
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
            printdebug('Cache: %s: Queuing complete. Waiting for DB commit.'
                       % self.mylist)
            self.bulkqueue.join()
            while self.resultqueue.empty() is not True:
                garbage = self.resultqueue.get()
            printdebug('Cache: %s: DB committed.' % self.mylist)
            for myid in range(0, self.bulkprocesses):
                self.bulkprocess[myid].join()
            printdebug('Flushed Cache %s Bulk Update Process.' % self.mylist)
            self.bulkmode = False
            if self.partialfield is not None:
                mylen = len(self.partiallist)
                if (mylen < self.bulklimit) and ((mylen * 2) < self.getcount()):
                    self.refresh(partial=True)
            else:
                self.refresh()
        else:
            printerror('Composition Cache %s Bulkmode not running.'
                       % self.mylist)

    def getcount(self):
        return len(self.items)

    def initadd(self):
        # Stub, can add init commands here.
        # Run just before refresh
        pass

    def __init__(self, client, schema, bulkapi, mylist):
        printdebug('Loading %s Cache' % mylist)
        self.client = client
        self.schema = schema
        self.mylist = mylist
        self.bulkprocesses = 2
        self.bulkapi = bulkapi
        self.bulkmode = False
        self.bulklimit = 32000
        self.partialfield = None
        self.partiallist = []
        self.initadd()
        self.refresh()


class CompositionCache(CBORJoinCache):
    # Composition Cache

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

    def precreate(self, mylist):
        keyset = set([item['related_body'] for item in mylist])
        self.items.update(dict.fromkeys(keyset))

    def cacheloaditem(self, odict):
        # we must have a pk/id and a station
        # these items use pk
        body = odict['related_body']
        comp = odict['component']
        share = odict['share']
        pk = odict['id']
        if body not in self.items:
            self.items[body] = {}
        elif type(self.items[body]) is not dict:
            self.items[body] = {}
        self.items[body][comp] = {'share': share, 'id': pk}


class StationJoinCache(CBORJoinCache):
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
        myparams = {
            'station_id': station,
        }                                   # Tell DB to use key directly
        action = 'create'
        pklist = []
        if station in self.items:   # We already have this station in our cache
            # Note indict[lookupf] is a list but we need compare with
            # dict keys, in order, so use sets.
            existingset = set(self.items[station].keys())
            newset = set(indict[self.lookupf])
            #if None in newset:
            #    printerror("New set from Station: %d contains None: %s in %s"
            #               % (station, newset, self.mylist))
            if (existingset is not None) and (newset is not None):
                # TODO Check logic for removal of items completely
                #       e.g shipyard closed
                # otherwise just continue with creates
                existingset = sorted(existingset)
                # newset could contain Nones, we need to get rid of them
                # otherwise we cannot sort in Python3
                newset = sorted(set(filter(None.__ne__, newset)))
                #
                if newset == existingset:
                    return False    # Yes I found it, and no update required
                else:
                    printdebug('Need to update because these do not match')
                    printdebug("existing set: %s" % existingset)
                    printdebug("new set: %s" % newset)
                    # We have no "update" action, we always delete
                    # and replace. Need a list of PKs to delete
                    pklist = [v for k, v in self.items[station].items()
                              if v is not None]
                    # Don't forget to remove the entries in the cache now!
                    self.items[station] = {}
        # Delete the previous list if there is one
        for pk in pklist:
            if self.bulkmode is True:
                mydelparams = pk
                self.addtobulkupdate(mydelparams, 'delete')
            else:
                try:
                    self.client.action(
                                    self.schema,
                                    [self.mylist, 'destroy'],
                                    params={'pk': pk})
                except Exception as e:
                    printerror('Exception in %s StationJoin FoA' % self.mylist)
                    printerror(str(e))
                    printerror(myparams)
                    return None
        # Make the new one(s)
        for thisthing in indict[self.lookupf]:
            if thisthing is None:
                continue   # No point putting THAT in DB so fall through
            dbfield = self.lookupf + '_id'   # Tell DB to use key directly
            myparams[dbfield] = thisthing
            if self.bulkmode is True:
                # For these we need to delete (as above) and create new
                # So we always create
                self.addtobulkupdate(myparams, 'create')
                self.cacheloaditem(myparams)
            else:
                try:
                    odict = self.client.action(
                                    self.schema,
                                    [self.mylist, 'create'],
                                    params=myparams)
                    self.cacheloaditem(odict)
                except Exception as e:
                    printerror('Exception in %s StationJoin FoA' % self.mylist)
                    printerror(str(e))
                    printerror(myparams)
                    return None
        return True

    def clearcache(self):
        # We override to set lookupf based on self.mylist
        self.items = {}

    def precreate(self, mylist):
        keyset = set([item['station'] for item in mylist
                     if item['station'] not in self.items])
        self.items.update(dict.fromkeys(keyset))

    def cacheloaditem(self, odict):
        # we must have a pk/id and a station
        # these items use id
        if ('id' in odict) and ('station' in odict):
            ostation = odict['station']
            thing = odict[self.lookupf]
            if ostation not in self.items:
                self.items[ostation] = {}
            elif type(self.items[ostation]) is not dict:
                self.items[ostation] = {}
            if thing not in self.items[ostation]:
                self.items[ostation][thing] = odict['id']
            elif self.items[ostation][thing] is None:
                # Exists but is not known (could be bulk insert related)
                self.items[ostation][thing] = odict['id']
            elif self.items[ostation][thing] == odict['id']:
                # we can ignore this, it means no change
                #printerror('Ignoring Clone in DB in StationJoinCache %s, station %s, item %s'
                #            % (self.mylist, ostation, thing))
                pass
            else:
                printerror('Duplicate in DB in StationJoinCache %s, station %s, item %s'
                            % (self.mylist, ostation, thing))
        elif 'station_id' in odict:
            # Assume a bulk insert, so no ID, but we can track
            # possible duplicate here
            ostation = odict['station_id']      # Note prepend of _id
            dbfield = self.lookupf + '_id'
            thing = odict[dbfield]
            if ostation not in self.items:
                self.items[ostation] = {}
            elif type(self.items[ostation]) is not dict:
                self.items[ostation] = {}
            if thing not in self.items[ostation]:
                self.items[ostation][thing] = None      # i.e. unknown
        else:
            printerror('StationJoinCache:%s:cacheloaditem: ID and station required.'
                       % self.mylist)

    def initadd(self):
        # Can add init commands here.
        # Run just before refresh
        # Setting a partial field will enable partial refresh after bulk
        self.partialfield = 'station'
        # Setup lookupf based on listid
        if self.mylist == 'stationeconomies':
            self.lookupf = 'economy'
        elif self.mylist == 'stationships':
            self.lookupf = 'shiptype'
        elif self.mylist == 'stationmodules':
            self.lookupf = 'module'
        elif self.mylist == 'stationimports':
            self.lookupf = 'commodity'
        elif self.mylist == 'stationexports':
            self.lookupf = 'commodity'
        elif self.mylist == 'stationprohibited':
            self.lookupf = 'commodity'
        else:
            printerror('StationJoinCache:initadd:%s unknown cache.'
                       % self.mylist)
            self.lookupf = None


class HashedItemCache(CBORJoinCache):
    # This could probably be refactored alongside Composition Cache
    def getpkfromeddbid(self, eddbid):
        if eddbid in self.eddb:
            return self.eddb[eddbid]
        else:
            return None

    def eddbidexists(self, eddbid):
        if eddbid in self.eddb:
            return True
        else:
            return False

    def getpkfromeddbname(self, name):
        if name in self.eddbname:
            return self.eddbname[name]
        else:
            printdebug('Failed to find %s in %s lookup.' % (name, self.mylist))
            return None

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
                    self.cacheloaditem(newitem)
                    return newitem['id']
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
                        self.cacheloaditem(newitem)    # to update duphash
                except Exception as e:
                    printerror('Exception in %s HashItem FoA create.'
                               % self.mylist)
                    printerror(str(e))
                    printerror(myitem)
                return dbid
            else:
                return dbid

    def clearcache(self):
        self.eddb = {}      # eddbid
        self.eddbname = {}
        self.duphash = {}

    def precreate(self, mylist):
        # None for this at the moment
        return

    def cacheloaditem(self, odict):
        # we must have a pk/id and a station
        # these items use id
        if ('id' in odict):
                # print(odict)
                eddbid = odict.get('eddbid')
                duphash = odict.get('duphash')
                eddbname = odict.get('eddbname')
                pk = odict['id']
                if eddbid is not None:
                    self.eddb[eddbid] = pk
                if eddbname is not None:
                    self.eddbname[eddbname] = pk
                if duphash is not None:
                    self.duphash[pk] = duphash
        else:
            printerror('HashedItemCache:%s:cacheloaditem: ID required.'
                       % self.mylist)

    def getcount(self):
        return len(self.duphash)

    def initadd(self):
        # Stub, can add init commands here.
        # Run just before refresh
        self.bulklimit = 8000


class SysIDCache2(HashedItemCache):

    def clearcache(self):
        self.eddb = {}      # eddbid
        self.edsm = {}
        self.duphash = {}

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
                if self.bulkmode is True:
                    self.addtobulkupdate(system, 'update')
                    return True
                else:
                    printerror('SysIDCache2: Please enable bulkmode first.')
                    return False
            else:
                return False

    def precreate(self, mylist):
        eddbset = set([item['eddbid'] for item in mylist])
        self.eddb.update(dict.fromkeys(eddbset))  # Find by eddb
        edsmset = set([item['edsmid'] for item in mylist])
        self.edsm.update(dict.fromkeys(edsmset))  # Find by edsm
        duphashset = set([item['pk'] for item in mylist])
        self.duphash.update(dict.fromkeys(duphashset))   # Check if update required

    def cacheloaditem(self, odict):
        # we must have a pk/id and a station
        # these items use id
        if 'pk' in odict:
            odict['id'] = odict.pop('pk')
        if 'id' in odict:
                # print(odict)
                eddbid = odict.get('eddbid')
                duphash = odict.get('duphash')
                edsmid = odict.get('edsmid')
                pk = odict['id']
                if eddbid is not None:
                    self.eddb[eddbid] = pk
                if edsmid is not None:
                    self.edsm[edsmid] = pk
                if duphash is not None:
                    self.duphash[pk] = duphash
        else:
            printerror('HashedItemCache:%s:cacheloaditem: ID required.'
                       % self.mylist)

    def initadd(self):
        # Run just before refresh
        # Setting a partial field will enable partial refresh after bulk
        self.partialfield = 'eddbid'
        self.bulklimit = 8000


class ItemCache(object):
    # Default Item Cache, suitable for most items.

    def getidbyname(self, name):
        # bit blind, but will work.
        if name in self.items:
            return self.items[name]
        else:
            printdebug('Itemcache:%s:Name not found:%s' % (self.mylist, name))
            return None

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
        #if item == 'None':
        #        return None
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
        # print(self.items)


class KitItemCache(CBORJoinCache):
    # Variant of ItemCache for Ships and Modules
    # No real need to bulk update
    # However, need to support more sophisticated updating.
    # We expect a dictionary, suitable for DB insertion

    def getidbyname(self, name):
        if name in self.names:
            # printdebug('Found name %s in getidbyname/KitItemCache' % name)
            return self.names[name]['id']
        else:
            return None

    def getpkfromeddbname(self, name):
        if name in self.eddbnames:
            #printdebug('Found name %s in getidbyname/KitItemCache' % name)
            return self.eddbnames[name]['id']
        else:
            return None

    def getidbyeddbid(self, eddbid):
        if eddbid in self.eddbids:
            # printdebug('Found name %s in getidbyname/KitItemCache' % name)
            return self.eddbids[eddbid]['id']
        else:
            printdebug('Not Found: %d in getidbyname/KitItemCache for %s'
                       % (eddbid, self.mylist))
            return None

    def getcount(self):
        return len(self.symbols)

    def clearcache(self):
        self.ids = {}
        self.eddbids = {}
        self.symbols = {}
        self.edids = {}
        self.names = {}
        self.eddbnames = {}

    def cacheloaditem(self, odict):
        # we must have a pk/id
        if 'id' in odict:
            myid = odict['id']
            self.ids[myid] = odict
            if 'eddbid' in odict:
                self.eddbids[odict['eddbid']] = self.ids[myid]
            if 'edsymbol' in odict:
                self.symbols[odict['edsymbol']] = self.ids[myid]
            if 'edid' in odict:
                self.edids[odict['edid']] = self.ids[myid]
            if 'name' in odict:
                self.names[odict['name']] = self.ids[myid]
            if 'eddbname' in odict:
                self.eddbnames[odict['eddbname']] = self.ids[myid]
        else:
            printerror('KitItemCache:%s:cacheloaditem: No ID field in dict.'
                       % self.mylist)

    def findoradd(self, initem):
        isdict = False
        iseddblookup = False
        issymbollookup = False
        isedidlookup = False
        if type(initem) is dict:
            isdict = True
            if 'edsymbol' in initem:
                # Good, we like symbols
                issymbollookup = True
                item = initem['edsymbol']
            elif 'edid' in initem:
                isedidlookup = True
                item = initem['edid']
            elif 'eddbid' in initem:
                iseddblookup = True
                item = initem['eddbid']
            elif 'name' in initem:
                isnamelookup = True
                item = initem['name']
            else:
                # Unsupported dict
                printerror('KitItemCache does not support this dictionary')
                printerror(initem)
                return None
        else:
            printerror('KitItemCache required a dictionary')
            printerror(initem)
            return None
        # Check for nonsense
        if item is None:
                return None
        if item == 'None':
                return None
        if item == '':
                return None
        # Does this object exist in cache?
        if issymbollookup is True:
            lookupdict = self.symbols
            label = 'edsymbol'
        elif isedidlookup is True:
            lookupdict = self.edids
            label = 'edid'
        elif iseddblookup is True:
            lookupdict = self.eddbids
            label = 'eddbid'
        elif isnamelookup is True:
            lookupdict = self.names
            label = 'name'
        if item in lookupdict:   # Do we already have this in our cache?
            # Do we need to add new data?
            cachedversion = lookupdict[item]
            changed = False
            value = initem.pop(label)   # Take this out temporarily
            for k, v in initem.items():
                if k not in cachedversion:      # check all keys in both
                    cachedversion[k] = v
                    changed = True              # This should update the dict
                elif cachedversion[k] is None and v is not None:
                    cachedversion[k] = v
                    changed = True
            if changed is True:
                try:
                    myparams = cachedversion
                    myparams[label] = value     # Add this back in
                    myparams['pk'] = myparams.pop('id')  # Really Annoying
                    odict = self.client.action(
                                    self.schema,
                                    [self.mylist, 'update'],
                                    params=myparams)
                    # Need to ensure both lookupdicts are updated.
                    self.cacheloaditem(odict)
                except Exception as e:
                    printerror('Exception in Update KitItemCache')
                    printerror(str(e))
                    printerror(myparams)
            return lookupdict[item]['id']
        else:                    # Not in cache at all, so a new item
            myparams = initem
            try:
                odict = self.client.action(
                                self.schema,
                                [self.mylist, 'create'],
                                params=myparams)
                self.cacheloaditem(odict)
            except Exception as e:
                print('Exception in Create KitItemCache')
                print(str(e))
                print(myparams)
            return lookupdict[item]['id']


class DBCache(object):
    # improve system import time

    def __init__(self, client, schema, bulkapi):
        # Systems Caches (not exclusively)
        self.systemids = SysIDCache2(client, schema, bulkapi, 'systemids')
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
        self.stationimports = StationJoinCache(client, schema, bulkapi, 'stationimports')
        self.stationexports = StationJoinCache(client, schema, bulkapi, 'stationexports')
        self.stationprohibited = StationJoinCache(client, schema, bulkapi, 'stationprohibited')
        self.stationeconomies = StationJoinCache(client, schema, bulkapi, 'stationeconomies')
        self.stationships = StationJoinCache(client, schema, bulkapi, 'stationships')
        self.stationmodules = StationJoinCache(client, schema, bulkapi, 'stationmodules')
        # Ships and Modules
        self.shiptypes = KitItemCache(client, schema, bulkapi, 'shiptypes')
        self.modules = KitItemCache(client, schema, bulkapi, 'modules')
        self.modulecats = KitItemCache(client, schema, bulkapi, 'modulecats')
        self.modulegroups = KitItemCache(client, schema, bulkapi, 'modulegroups')
        self.modguidances = ItemCache(client, schema, 'modguidances')
        self.modmounts = ItemCache(client, schema, 'modmounts')
