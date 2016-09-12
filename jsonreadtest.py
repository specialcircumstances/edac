#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from pprint import pprint as pprint
from time import sleep as sleep
from modules.edjhandler import JournalHandler
from modules.pobjs import PrimaryObject
from modules.EDMarketConnector.companion import Session as CompanionSession

DEBUG = True
#with open('data.json', 'r') as f:
#     data = json.load(f)

def printdebug(mystring):
    if DEBUG is True:
        print(mystring)

'''
The following are the key objects I'll require.
pobj_state - this is for general system status
             (e.g. INACTIVE, CMDR_LOADED)
pobj_cmdr - this is the current commander,
            including any materials and prefs
pobj_ship - this is the current ship, including loadout and cargo
pobj_universe - this is the universe (everything we know about it!)
                items such as coriolis and eddb are in here
pobj_starsystem - this is the current star system
pobj_localbody - this is the current local body

For ease of use I  wrap them up in a single object
e.g. pobj.ship
'''

myhandler = JournalHandler()
pobj = PrimaryObject()


with open("Journal.160726141417.01.log", "r") as f:
    for line in f:
        j = json.loads(line)
        print('MAIN - Reading line of Journal: %s' % j['event'])
        myhandler.routetohandler(j, pobj)
pprint(vars(pobj.cmdr))
pprint(vars(pobj.ship))
pprint(vars(pobj.ship.standard))
pprint(vars(pobj.ship.internals))
for k, v in pobj.ship.internals.mount.items():
    pprint(vars(v))
pprint(vars(pobj.ship.hardpoints))
for k, v in pobj.ship.hardpoints.mount.items():
    pprint(vars(v))
# CompanionAPI tested using module from EDMarketConnector
# with a little bit of modification mainly for Python 3
# apisession = CompanionSession()
# Note for testing the cookie is in root dir and has been
# authenticated/verified though python shell
# apisession.login('email', 'XXXXXXX')
# pprint(apisession.fixup(apisession.query()))
