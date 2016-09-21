#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Loads FDevIDs into useful objects
# Module data is read at first import
# Class instances copy the data? TBC

import csv
import json
import ijson
import time
import gc
from os.path import isfile
try:
    from modules.edacdb_wrapper import EDACDB
except:
    from edacdb_wrapper import EDACDB

# Many module globals

# These files should be from
# https://github.com/EDCD/FDevIDs
bodiesfile = 'modules\eddb-data\\bodies.jsonl'
commodiesfile = 'modules\eddb-data\commodies.json'
listingsfile = 'modules\eddb-data\listings.csv'
modulesfile = 'modules\eddb-data\modules.json'
stationsfile = 'modules\eddb-data\stations.json'
systemsfile = 'modules\eddb-data\systems.jsonl'
populatedsystemsfile = 'modules\eddb-data\systems_populated.jsonl'

listings = {}
listings_count = 0

DEBUG = True
ERROR = True
VERSION = '2.2 Beta'


def printdebug(mystring):
    if DEBUG is True:
        print("DEBUG eddb: %s" % mystring)


def printerror(mystring):
    if ERROR is True:
        print("ERROR eddb: %s" % mystring)



def listingsindexer(mydict):
    # mydict looks like:
    # {'name': 'Sidewinder', 'id': '128049249', 'symbol': 'SideWinder'}
    listings_count += 1
    return


def import_listings(filepath=listingsfile):
    if isfile(filepath):
        with open(filepath, 'r') as myfile:
            extract = csv.DictReader(myfile, dialect='excel')
            for row in extract:
                listingsindexer(row)
            myfile.close
    else:
        printerror('%s not found. Cannot load shipyard data.' % filepath)


''' example of populated system record
    "id": 5,
    "edsm_id": 10902,
    "name": "1 Kappa Cygni",
    "x": -117.75,
    "y": 37.78125,
    "z": 11.1875,
    "faction": "1 Kappa Cygni Movement",
    "population": 24843190,
    "government": "Dictatorship",
    "allegiance": "Independent",
    "state": "None",
    "security": "High",
    "primary_economy": "Industrial",
    "power": "Pranav Antal",
    "power_state": "Exploited",
    "needs_permit": 0,
    "updated_at": 1460287999,
    "simbad_ref": "",
    "is_populated": 1,
    "reserve_type": null
'''

class Systems(object):

    ''' The systems JSON looks like this
    {
    'x': Decimal('-104.71875'), 'primary_economy': None, 'is_populated': 1,
    'name': 'Pegasi Sector JW-W c1-23', 'population': None, 'simbad_ref': None,
    'z': Decimal('-61.09375'), 'needs_permit': 0, 'updated_at': 1473087801,
    'reserve_type': None, 'edsm_id': 150932, 'security': None, 'state': None,
    'allegiance': None, 'faction': None, 'power': 'None', 'government': None,
    'id': 2388643, 'y': Decimal('-121.875'), 'power_state': None
    }

    There are about 2.5 million of them in the full JSON dump!

    Moved to using jsonl files as much easier to process.
    systemsfile = 'modules\eddb-data\systems.jsonl'
    2439071 systems at last count, even adding items to a list results in
    over 2GB list. So as I was to remain 32-bit compatible, this cannot live
    in memory. I start to see problems at about 1.3 mil.

    populatedsystemsfile = 'modules\eddb-data\systems_populated.jsonl'
    19436 systems at last count, which is much more managable.

    '''



    def data_load_process(self):
        # Called after data is loaded from JSON
        # Improves usability by creating objects for the items
        print('Number of systems loaded:' %  (len(self.data)))
        #self.ships = Ships(self.data['Ships'])
        #self.modules = Modules(self.data['Modules'])

    def json_parser(self, myobj):
        # TODO can probably be removed now
        # Need to replace the odd key
        # print(dict(myobj))
        print(myobj.keys())
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


    def __init__(self, dbapi, filepath=systemsfile):
        if type(dbapi) is not EDACDB:
            printerror('dbapi must be of type EDACDB()')
            return False
        self.systems = {}
        self.systems_count = 0
        self.systems_changed = 0
        self.types = {}
        self.lastsystem = None
        self.dbapi = dbapi
        ''' Need to convert from
        {'updated_at': 1460286842, 'government': 'Corporate', 'y': 28.53125,
        'faction': '1 Hydrae Vision Solutions', 'simbad_ref': '1 Hydrae',
        'id': 3, 'x': 60.90625, 'reserve_type': None, 'z': -54.90625,
        'primary_economy': 'Agriculture', 'power_state': 'Exploited',
        'is_populated': 1, 'edsm_id': 15225, 'security': 'High',
        'power': 'Felicia Winters', 'name': '1 Hydrae', 'needs_permit': 0,
        'allegiance': 'Independent', 'population': 6028981745, 'state': 'Boom'}
        to
        # [edsmid], [edsmdate], [name], [coord_x], [coord_y], [coord_z],
        # [eddbid], [is_populated], [population], [simbad_ref], [needs_permit],
        # [eddbdate], [reserve_type], [security], [state], [allegiance],
        # [faction], [power], [government], [power_state]
        '''
        self.factioncount = 0
        if isfile(populatedsystemsfile):
            printdebug('%s found.' % populatedsystemsfile)
            printdebug('Preloading Factions.... can take a minute or two')
            self.timestart = time.clock()
            if True:
                with open(populatedsystemsfile, 'r', encoding='utf-8') as myfile:
                    for line in myfile:
                        item = json.loads(line)
                        self.systems_count += 1
                        if item['faction'] is not None:
                            self.dbapi.factionpreload(item['faction'])
                            self.factioncount += 1
                        #print('Read %d systems, found %d Factions              \r' %
                        #        (self.systems_count, self.factioncount),
                        #        end='')
                myfile.close
                self.dbapi.factionpreload_flush()
            printdebug('Read %d populated systems, saw %d factions.' %
                  (self.systems_count, self.factioncount)
                  )
        # OK, now bulk system updates will be more functional (mostly)
        self.systems_count = 0
        if isfile(filepath):
            printdebug('%s found. Starting to load EDDB data.' % filepath)
            self.timestart = time.clock()
            if True:
                with open(filepath, 'r', encoding='utf-8') as myfile:
                    for line in myfile:
                        item = json.loads(line)
                        self.systems_count += 1
                        # Tidy up fields to match DB
                        item['eddbid'] = item.pop('id')
                        item['eddbdate'] = item.pop('updated_at')
                        item['coord_x'] = item.pop('x')
                        item['coord_y'] = item.pop('y')
                        item['coord_z'] = item.pop('z')
                        item['edsmid'] = item.pop('edsm_id')
                        if item['reserve_type'] is None:
                            item['reserve_type']  = ''
                        if item['simbad_ref'] is None:
                            item['simbad_ref'] = ''
                        if self.dbapi.create_system_in_db(item) is True:
                            self.systems_changed += 1
                        if self.systems_count % 10000 == 0:
                            seconds = int(time.clock() - self.timestart)
                            srate = (self.systems_count + 1) / (seconds + 1)
                            crate = (self.systems_changed + 1) / (seconds + 1)
                            print('Read %d systems (%d/s), changed %d(%d/s)              \r' % (
                                    self.systems_count, srate,
                                    self.systems_changed, crate),
                                    end='')
                    myfile.close
                    self.dbapi.create_system_bulk_flush()
                seconds = int(time.clock() - self.timestart)
                srate = (self.systems_count + 1) / (seconds + 1)
                crate = (self.systems_changed + 1) / (seconds + 1)
                printdebug('Read %d systems (%d/s), changed %d(%d/s)              \r' % (
                        self.systems_count, srate,
                        self.systems_changed, crate)
                        )
                printdebug('Successfully loaded JSON: %s' % filepath)
                # Need to reload the SystemID cache if anything changed
                # As the bulk updater doesn't current update the cache contents
                if self.systems_changed > 0:
                    printdebug('Reloading SystemID Cache')
                    self.dbapi.cache.systemsids.refresh()
                #self.data_load_process()
                #printdebug('Test get ship by name: %s' % self.ships.get_by_name('keelback').properties['name'])
                self.loaded = True  # TODO better checks here
            #except Exception as e:
            #    print(str(e))

        else:
            printerror('%s not found. Cannot load EDDB systems data.' % filepath)

class Bodies(object):

    def __init__(self, dbapi, filepath=bodiesfile):
        # Well, we need to open the filepath
        if type(dbapi) is not EDACDB:
            printerror('dbapi must be of type EDACDB()')
            return False
        self.bodies = {}
        self.bodies_count = 0
        self.bodies_changed = 0
        self.types = {}
        self.dbapi = dbapi
        if isfile(filepath):
            printdebug('%s found. Starting to load EDDB Bodies data.' % filepath)
            self.timestart = time.clock()
            if True:
                with open(filepath, 'r', encoding='utf-8') as myfile:
                    for line in myfile:
                        item = json.loads(line)
                        self.bodies_count += 1
                        # Tidy up fields to match DB
                        # print(item)
                        item['eddbid'] = item.pop('id')
                        item['eddb_created_at'] = item.pop('created_at')
                        item['eddb_updated_at'] = item.pop('updated_at')
                        # These are Ints for me
                        if item['catalogue_hd_id'] == '':
                            item['catalogue_hd_id'] = None
                        elif type(item['catalogue_hd_id']) is str:
                            item['catalogue_hd_id'] = int(item['catalogue_hd_id'].replace(',', '').replace('.', ''))
                        #
                        if item['catalogue_hipp_id'] == '':
                            item['catalogue_hipp_id'] = None
                        elif type(item['catalogue_hipp_id']) is str:
                            item['catalogue_hipp_id'] = int(item['catalogue_hipp_id'].replace(',', '').replace('.', ''))
                        # str cannot be Null in DB
                        if item['catalogue_gliese_id'] is None:
                            item['catalogue_gliese_id'] = ''
                        # str cannot be Null in DB
                        if item['luminosity_sub_class'] is None:
                            item['luminosity_sub_class'] = ''
                        # str cannot be Null in DB
                        if item['full_spectral_class'] is None:
                            item['full_spectral_class'] = ''
                        # str cannot be Null in DB
                        if item['luminosity_class'] is None:
                            item['luminosity_class'] = ''
                        # str cannot be Null in DB
                        if item['spectral_class'] is None:
                            item['spectral_class'] = ''
                        #
                        if self.dbapi.create_eddb_body_in_db(item) is True:
                            self.systems_changed += 1
                        if self.bodies_changed % 100 == 0:
                            seconds = int(time.clock() - self.timestart)
                            srate = (self.bodies_count + 1) / (seconds + 1)
                            crate = (self.bodies_changed + 1) / (seconds + 1)
                            print('Read %d bodies (%d/s), changed %d(%d/s)              \r' % (
                                    self.bodies_count, srate,
                                    self.bodies_changed, crate),
                                    end='')
                    myfile.close
                    #self.dbapi.create_system_bulk_flush()
                seconds = int(time.clock() - self.timestart)
                srate = (self.bodies_count + 1) / (seconds + 1)
                crate = (self.bodies_changed + 1) / (seconds + 1)
                printdebug('Read %d bodies (%d/s), changed %d(%d/s)              \r' % (
                        self.bodies_count, srate,
                        self.bodies_changed, crate)
                        )
                printdebug('Successfully loaded bodies JSON: %s' % filepath)
                #self.data_load_process()
                #printdebug('Test get ship by name: %s' % self.ships.get_by_name('keelback').properties['name'])
                self.loaded = True  # TODO better checks here
            #except Exception as e:
            #    print(str(e))

        else:
            printerror('%s not found. Cannot load EDDB Bodies data.' % filepath)



if __name__ == '__main__':
    #import_listings()
    #print('Listings count is: %d' % listings_count)
    dbapi = EDACDB()
    mysystems = Systems(dbapi)
    mybodies = Bodies(dbapi)
    #print(mysystems.lastsystem)
    #print(mysystems.types)
    #max_len =  0
    #for key in mysystems.types.keys():
    #    if len(str(key)) > max_len:
    #        max_len = len(str(key))
    #print(max_len)
