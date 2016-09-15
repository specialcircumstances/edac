#!/usr/bin/env python
# -*- coding: utf-8 -*-

from waitress import serve

from edacdb.wsgi import application

if __name__ == '__main__':
    serve(application, port='8000')
