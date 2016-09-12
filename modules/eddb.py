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

# Many module globals

# These files should be from
# https://github.com/EDCD/FDevIDs
bodiesfile = 'modules\eddb-data\bodies.json'
commodiesfile = 'modules\eddb-data\commodies.json'
listingsfile = 'modules\eddb-data\listings.csv'
modulesfile = 'modules\eddb-data\modules.json'
stationsfile = 'modules\eddb-data\stations.json'
systemsfile = 'modules\eddb-data\systems.jsonl'
populatedsystemsfile = 'modules\eddb-data\systems_populated.jsonl'

DEBUG = True
ERROR = True
VERSION = '2.2 Beta'

listings = {}
listings_count = 0

DEBUG = True
ERROR = True
VERSION = '2.2 Beta'


def printdebug(mystring):
    if DEBUG is True:
        print("DEBUG coriolis: %s" % mystring)


def printerror(mystring):
    if ERROR is True:
        print("ERROR coriolis: %s" % mystring)



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

    So we won't load them idly... (or easily as it turns out...)
    The file is a single large json list with no CR, so normal json
    loads fail. Have resorted to ijson.

    Second issue is that it's just too much data for a simple dict, so the
    only real choice is to push each record straight into our DB backend.

    systemsfile = 'modules\eddb-data\systems.json'
    2439071 systems at last count, even adding items to a list results in
    over 2GB list. So as I was to remain 32-bit compatible, this cannot live
    in memory. I start to see problems at about 1.3 mil.

    populatedsystemsfile = 'modules\eddb-data\systems_populated.json'
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

    def old__init__(self, filepath=systemsfile):
            #
            self.systems = []
            self.systems_count = 0
            self.types = {}
            # Well, we need to open the filepath
            if isfile(filepath):
                printdebug('%s found. Starting to load EDDB Systems data.' % filepath)
                try:
                    with open(filepath, 'r', encoding="utf8") as myfile:
                            #filejson = json.load(myfile, encoding="utf8")
                            #parser = ijson.parse(myfile)
                            #for prefix, event, value in parser:
                            #    print(prefix, event, value)
                            items = ijson.items(myfile, 'item')
                            for item in items:
                                self.systems_count += 1
                                self.lastsystem = item
                                #if item['needs_permit'] == 1:
                                #    print('\n%s' % item['name'])
                                if item['power_state'] is not None:
                                    #print('\n%s' % item['security'])]
                                    if item['power_state'] in self.types.keys():
                                        self.types[item['power_state']] += 1
                                    else:
                                        self.types[item['power_state']] = 0
                                print('Read %d systems                     \r' % self.systems_count, end='')
                                #self.systems.append(item)
                            print('%d systems in file.' % self.systems_count)
                    myfile.close
                    #time.sleep(30)
                    printdebug('Successfully loaded JSON: %s' % filepath)
                    #self.systems_load_process()
                    self.loaded = True  # TODO better checks here
                except Exception as e:
                    print('%d systems loaded at error' % self.systems_count)
                    print(e)

    def __init__(self, filepath=systemsfile):
        # Well, we need to open the filepath
        self.systems = {}
        self.systems_count = 0
        self.types = {}
        self.lastsystem = None
        if isfile(filepath):
            printdebug('%s found. Starting to load EDDB data.' % filepath)
            if True:
                with open(filepath, 'r', encoding='utf-8') as myfile:
                    gc.disable
                    for line in myfile:
                        item = json.loads(line)
                        self.systems_count += 1
                        self.systems[item['id']] = item
                        if self.lastsystem is not None:
                            self.systems.pop(self.lastsystem)
                        self.lastsystem = item['id']
                        print('Read %d systems                     \r' % self.systems_count, end='')
                    myfile.close
                    gc.enable
                printdebug('Successfully loaded JSON: %s' % filepath)
                #self.data_load_process()
                #printdebug('Test get ship by name: %s' % self.ships.get_by_name('keelback').properties['name'])
                self.loaded = True  # TODO better checks here
            #except Exception as e:
            #    print(str(e))

        else:
            printerror('%s not found. Cannot load EDDB data.' % filepath)




if __name__ == '__main__':
    #import_listings()
    #print('Listings count is: %d' % listings_count)
    mysystems = Systems()
    #print(mysystems.lastsystem)
    #print(mysystems.types)
    #max_len =  0
    #for key in mysystems.types.keys():
    #    if len(str(key)) > max_len:
    #        max_len = len(str(key))
    #print(max_len)
