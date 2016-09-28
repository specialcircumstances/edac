#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import cbor
import time
import pprint
import hashlib
import base64
# For file downloads
import urllib.request
import shutil
from gzip import GzipFile
import config


# These files should be from
# https://github.com/EDCD/FDevIDs
bodiesfile = config.settings.getsourcefile('eddbbodiesfile')
commoditiesfile = config.settings.getsourcefile('eddbcommoditiesfile')
listingsfile = config.settings.getsourcefile('eddblistingsfile')
modulesfile = config.settings.getsourcefile('eddbmodulesfile')
stationsfile = config.settings.getsourcefile('eddbstationsfile')
systemsfile = config.settings.getsourcefile('eddbsystemsfile')
populatedsystemsfile = config.settings.getsourcefile('eddbpopulatedsystemsfile')

bodiesurl = config.settings.getsourceurl('bodies')
commoditiesurl = config.settings.getsourceurl('commodities')
listingurl = config.settings.getsourceurl('listings')
modulesurl = config.settings.getsourceurl('modules')
stationsurl = config.settings.getsourceurl('stations')
systemsurl = config.settings.getsourceurl('systems')
popsystemsurl = config.settings.getsourceurl('popsystems')


def getfile(url, file_name):
    # Download the file from `url` and save it locally under `file_name`:
    req = urllib.request.Request(url)
    req.add_header('Accept-Encoding', 'gzip, deflate, sdch')
    with urllib.request.urlopen(req) as response, open(file_name, 'wb') as out_file:
        print(url)
        print(req.headers)
        print(response.info())
        if response.info().get('Content-Encoding') == 'gzip':
            unzipped = GzipFile(fileobj=response)
            shutil.copyfileobj(unzipped, out_file)
        else:
            shutil.copyfileobj(response, out_file)

def getalleddbfiles():
    getfile(bodiesurl, bodiesfile)
    getfile(commoditiesurl, commoditiesfile)
    getfile(listingurl, listingsfile)
    getfile(modulesurl, modulesfile)
    getfile(stationsurl, stationsfile)
    getfile(systemsurl, systemsfile)
    getfile(popsystemsurl, populatedsystemsfile)


def jsontocbor():
    systems_count = 0
    '''
    with open(systemsfile, 'r', encoding='utf-8') as myfile:
        with open(systemsfileout, 'wb') as outfile:
            for line in myfile:
                item = (json.loads(line))
                outfile.write(cbor2.dumps(item))
                systems_count += 1
                print('Read %d systems                 \r' %
                        (systems_count),
                        end='')
    myfile.close
    '''

    print('JSON Load')
    time_start = time.clock()
    with open(systemsfile, 'r', encoding='utf-8') as myfile:
            for line in myfile:
                item = (json.loads(line))
    time_stop = time.clock()
    print(time_stop - time_start)


    print('CBOR2 Load')
    time_start = time.clock()
    with open(systemsfileout, 'rb') as myfile:
            for line in myfile:
                item = (cbor.loads(line))
                print(item)
    time_stop = time.clock()
    print(time_stop - time_start)


def getheadingsfromdict(item, myresults, nameditems):
    for mykey in item.keys():
        if mykey not in myresults.keys():
            print(mykey)
            myresults[mykey] = {}
            myresults[mykey]['count'] = 1
        else:
            myresults[mykey]['count'] += 1
        if mykey in nameditems.keys():
            if item[mykey] not in nameditems[mykey]:
                nameditems[mykey].append(item[mykey])
        if type(item[mykey]) is dict:
            getheadingsfromdict(item[mykey], myresults[mykey], nameditems)
        elif type(item[mykey]) is list:
            getheadingsfromlist(item[mykey], myresults[mykey], nameditems)
    return myresults

def getheadingsfromlist(items, myresults, nameditems):
    for myitem in items:
        if type(myitem) is dict:
            getheadingsfromdict(myitem, myresults, nameditems)
        elif type(myitem) is list:
            getheadingsfromlist(myitem, myresults, nameditems)
    return myresults


def listallheadings(myfile):
    print('JSON Load to find all headings')
    time_start = time.clock()
    myresults = {}
    nameditems = {
        'atmosphere_component_name': [],
        'atmosphere_type_name': [],
        'group_name': [],
        'material_name': [],
        'ring_type_name': [],
        'solid_component_name': [],
        'type_name': [],
        'volcanism_type_name': [],
        'type': [],
        'station_type': [],
        'name': [],
        'weapon_mode': [],
        'missile_type': [],
        'class': []
    }
    with open(myfile, 'r', encoding='utf-8') as myfile:
            for line in myfile:
                item = (json.loads(line))
                if type(item) is dict:
                    myresults = getheadingsfromdict(item, myresults, nameditems)
                elif type(item) is list:
                    myresults = getheadingsfromlist(item, myresults, nameditems)

    time_stop = time.clock()
    print(time_stop - time_start)
    pprint.pprint(myresults)
    pprint.pprint(nameditems)
    return myresults

def duphash(data):
    data = str(data).encode('utf-8')
    #print(data)
    dig = hashlib.md5(data).digest()  # b']A@*\xbcK*v\xb9q\x9d\x91\x10\x17\xc5\x92'
    b64 = base64.b64encode(dig)       # b'XUFAKrxLKna5cZ2REBfFkg=='
    return b64.decode()[0:8]

def comparefirstlines(file01, file02):
    print('JSON Load to compare first line of two files')
    with open(file01, 'r', encoding='utf-8') as myfile:
            x = 0
            for line in myfile:
                item1 = (json.loads(line))
                pprint.pprint(item1)
                x += 1
                if x >10:
                    break   # dirty
    with open(file02, 'r', encoding='utf-8') as myfile:
            x = 0
            for line in myfile:
                item2 = (json.loads(line))
                pprint.pprint(item2)
                x += 1
                if x >10:
                    break   # dirty
    print(sorted(item1.keys()))
    print(sorted(item2.keys()))
    hashdata1 = ''
    for key in sorted(item1.keys()):
        hashdata1 += str(item1[key])
    print(hashdata1)
    hashdata2 = ''
    for key in sorted(item1.keys()):
        hashdata2 += str(item2[key])
    print(hashdata2)
    print(duphash(hashdata1))
    print(duphash(hashdata2))
    for keys in item1.keys():
        note = 'SAME'
        if item1[keys] != item2[keys]:
            note = 'DIFF'
        print('%s: %s : %s : %s'  % (keys, item1[keys], item2[keys], note))




if __name__ == '__main__':
    #listallheadings(modulesfile)
    #comparefirstlines('modules\eddb-data\systems.jsonl',
    #                  'modules\eddb-data\systemsc.jsonl')
    getalleddbfiles()
