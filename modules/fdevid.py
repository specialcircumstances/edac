#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Loads FDevIDs into useful objects
# Module data is read at first import
# Class instances copy the data? TBC

import csv
from os.path import isfile

# Many module globals

# These files should be from
# https://github.com/EDCD/FDevIDs
shipyardcsv = 'modules\FDevIDs\shipyard.csv'
outfittingcsv = 'modules\FDevIDs\outfitting.csv'
commoditycsv = 'modules\FDevIDs\commodity.csv'

DEBUG = True
ERROR = True
VERSION = '2.2 Beta'

shipyardbyname = {}
shipyardbyid = {}
shipyardbysymbol = {}   # All symbols will be keyed in lower case
outfittingnames = []     # Note not unique keys, so just a list
outfittingbysymbol = {}
outfittingbyid = {}
outfittingcategories = []
commoditiesbyid = {}
commoditiesbyname = {}
commoditycategories = []
# Including all the lookups, they are static


def printdebug(mystring):
    if DEBUG is True:
        print("DEBUG coriolis: %s" % mystring)


def printerror(mystring):
    if ERROR is True:
        print("ERROR coriolis: %s" % mystring)


def shipyardindexer(mydict):
    # mydict looks like:
    # {'name': 'Sidewinder', 'id': '128049249', 'symbol': 'SideWinder'}
    name = mydict['name']
    myid = mydict['id']
    symbol = mydict['symbol'].lower()
    shipyardbyname[name] = {'id': myid, 'symbol': symbol}
    shipyardbyid[myid] = {'name': name, 'symbol': symbol}
    shipyardbysymbol[symbol] = {'id': myid, 'name': name}
    return


def import_shipyard(filepath=shipyardcsv):
    if isfile(filepath):
        with open(filepath, 'r') as myfile:
            extract = csv.DictReader(myfile, dialect='excel')
            for row in extract:
                shipyardindexer(row)
            myfile.close
    else:
        printerror('%s not found. Cannot load shipyard data.' % filepath)

def outfittingindexer(mydict):
    # mydict looks like:
    # {'category': 'internal', 'id': '128666704', 'class': '1',
    # 'rating': 'E', 'entitlement': '', 'guidance': '', 'ship': '',
    # 'mount': '', 'name': 'Frame Shift Drive Interdictor',
    # 'symbol': 'Int_FSDInterdictor_Size1_Class1'}
    # As this is bigger use primary index by symbol then lookups to that.
    name = mydict['name']
    myid = mydict['id']
    symbol = mydict['symbol'].lower()
    category = mydict['category']
    outfittingbysymbol[symbol] = mydict
    if name not in outfittingnames:
        outfittingnames.append(name)   # Multiple items share a name
    if category not in outfittingcategories:
        outfittingcategories.append(category)
    outfittingbyid[myid] = outfittingbysymbol[symbol]
    return


def import_outfitting(filepath=outfittingcsv):
    if isfile(filepath):
        with open(filepath, 'r') as myfile:
            extract = csv.DictReader(myfile, dialect='excel')
            for row in extract:
                outfittingindexer(row)
            myfile.close
    else:
        printerror('%s not found. Cannot load shipyard data.' % filepath)

def commoditiesindexer(mydict):
    # mydict looks like:
    # {'category': 'Legal Drugs', 'name': 'Liquor', 'id': '128049216',
    # 'average': '587'}
    # We don't have symbols (yet) so index primarily by id, and ref name
    name = mydict['name']
    myid = mydict['id']
    category = mydict['category']
    # symbol = mydict['symbol']
    # outfittingbysymbol[symbol] = mydict
    commoditiesbyid[myid] = mydict
    commoditiesbyname[name] = commoditiesbyid[myid]
    if category not in commoditycategories:
        commoditycategories.append(category)
    return

def import_commodities(filepath=commoditycsv):
    if isfile(filepath):
        with open(filepath, 'r') as myfile:
            extract = csv.DictReader(myfile, dialect='excel')
            for row in extract:
                commoditiesindexer(row)
            myfile.close
    else:
        printerror('%s not found. Cannot load shipyard data.' % filepath)


class Mapper(object):
    # General Purpose mapper Functions
    def getshipbyname(self, name):
        if name in self.shipyardbyname.keys():
            return self.shipyardbyname[name]
        else:
            return None

    def getshipbyid(self, myid):
        if myid in self.shipyardbyid.keys():
            return self.shipyardbyid[myid]
        else:
            return None

    def getshipbysymbol(self, symbol):
        if symbol.lower() in self.shipyardbysymbol.keys():
            return self.shipyardbysymbol[symbol]
        else:
            return None

    def getmodulenames(self):
        return outfittingnames

    def getmodulebyid(self, myid):
        if myid in self.outfittingbyid.keys():
            return self.outfittingbyid[myid]
        else:
            return None

    def getmodulebysymbol(self, symbol):
        if symbol.lower() in self.outfittingbysymbol.keys():
            return self.outfittingbysymbol[symbol]
        else:
            return None

    def getmoduleidbysymbol(self, symbol):
        if symbol.lower() in self.outfittingbysymbol.keys():
            return self.outfittingbysymbol[symbol]['id']
        else:
            return None

    def getmodulecategories(self):
        return outfittingcategories

    def __init__(self):
        # TODO should there be a method to reload with alternative file path?
        # Not sure...

        # Make copies mutable copies of the module dictionaries
        self.shipyardbyname = shipyardbyname
        self.shipyardbyid = shipyardbyid
        self.shipyardbysymbol = shipyardbysymbol
        self.outfittingnames = outfittingnames
        self.outfittingbysymbol = outfittingbysymbol
        self.outfittingbyid = outfittingbyid
        self.outfittingcategories = outfittingcategories
        self.commoditiesbyid = commoditiesbyid
        self.commoditiesbyname = commoditiesbyname
        self.commoditycategories = commoditycategories

# Module intialisation Functions
import_shipyard()
import_outfitting()
import_commodities()

if __name__ == '__main__':
    print('Shipyard by name')
    print(shipyardbyname.keys())
    print('Shipyard by ID')
    print(shipyardbyid.keys())
    print('Shipyard by symbol')
    print(shipyardbysymbol.keys())
    print('Outfitting names')
    print(outfittingnames)
    print('Outfitting by ID')
    print(outfittingbyid.keys())
    print('Outfitting by symbol')
    print(outfittingbysymbol.keys())
    print('Outfitting Categories')
    print(outfittingcategories)
    print('Commodities by ID')
    print(commoditiesbyid.keys())
    print('Commodities by name')
    print(commoditiesbyname.keys())
    print('Commodity Categories')
    print(commoditycategories)
    mymapper = Mapper()
    print('Instance Commodity Categories')
    print(mymapper.commoditycategories)
    print('Testing get ship functions with Imperial Clipper')
    print(mymapper.getshipbyname('Imperial Clipper'))
    print(mymapper.getshipbyid('128049315'))
    print(mymapper.getshipbysymbol('Empire_Trader'))
    print('Testing get module functions with Hpt_PulseLaserBurst_Gimbal_Large')
    print(mymapper.getmodulenames())
    print(mymapper.getmodulecategories())
    print(mymapper.getmodulebyid('128049406'))
    print(mymapper.getmodulebysymbol('Hpt_PulseLaserBurst_Gimbal_Large'))
    print(mymapper.getmoduleidbysymbol('Hpt_PulseLaserBurst_Gimbal_Large'))
