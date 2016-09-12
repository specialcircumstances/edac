#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
This is a wrapper around coreapi to make talking to our DB easier

Our DB is a django based solution, exposing a REST API

At the moment django is using it's default sqllite DB, but there's nothing
to stop it using something else, like MySQL if you prefer.

'''

import coreapi

# Just using django runserver at the Movement
default_db = 'http://127.0.0.1:8000/edacapi/'
default_username = 'root'
default_password = 'password1234'


class EDACDB(object):
    # primary object
    # http://www.coreapi.org/specification/document/

    def __init__(
            self,
            mydb=default_db,
            username=default_username,
            password=default_password
            ):
        self.client = coreapi.Client()
        self.mydb = mydb
        self.username = username
        self.password = password
        self.schema = self.client.get(self.mydb)
        print(self.schema)  # Ordered Dict of objects
        # e.g.
        # OrderedDict([
        #    ('cmdrs', 'http://127.0.0.1:8000/edacapi/cmdrs/'),
        #    ('ships', 'http://127.0.0.1:8000/edacapi/ships/'),
        #    ('systems', 'http://127.0.0.1:8000/edacapi/systems/')
        #   ])
        print('Commanders Schema')
        print(self.schema['cmdrs'])
        self.cmdrs = self.client.get(self.schema['cmdrs'])
        print('Commanders')
        print(self.cmdrs)
        #self.cmdrtest = self.client.get(self.cmdrs[1])
        self.ships = self.client.get(self.schema['ships'])
        print('Ships')
        print(self.ships)
        self.systems = self.client.get(self.schema['systems'])
        print('Systems')
        print(self.systems)



if __name__ == '__main__':
    obj = EDACDB()
