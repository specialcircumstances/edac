#!/usr/bin/env python
# -*- coding: utf-8 -*-

from cherrypy import wsgiserver
#This can be from cherrypy import wsgiserver if you're not running it standalone.
import os
import django
from django.conf import settings
from django.core.handlers.wsgi import WSGIHandler

if __name__ == "__main__":
    os.environ['DJANGO_SETTINGS_MODULE'] = 'edacdb.settings'
    django.setup()
    server = wsgiserver.CherryPyWSGIServer(
        ('0.0.0.0', 8000),
        WSGIHandler(),
        #server_name='www.django.example',
        numthreads = 20,
    )
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()
