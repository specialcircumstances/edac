'''
This is a direct adaptation of Django Rest Framework Msgpack (v1.0.1)
https://github.com/juanriaza/django-rest-framework-msgpack
to use the cbor2 library
https://pypi.org/project/cbor2/

'''

import cbor2 as cbor       # In my tests this appeared to give better perf than cbor
import decimal
import datetime
import sys      # temp??
import gc

from rest_framework.renderers import BaseRenderer


class CBOREncoder(object):

    def encode(self, obj):
        # I think this might not be necessary with the CBOR2 encoder
        # I'm not using it, but include it for future reference
        if isinstance(obj, datetime.datetime):
            return {'__class__': 'datetime', 'as_str': obj.isoformat()}
        elif isinstance(obj, datetime.date):
            return {'__class__': 'date', 'as_str': obj.isoformat()}
        elif isinstance(obj, datetime.time):
            return {'__class__': 'time', 'as_str': obj.isoformat()}
        elif isinstance(obj, decimal.Decimal):
            return {'__class__': 'decimal', 'as_str': str(obj)}
        else:
            return obj


class CBORRenderer(BaseRenderer):
    """
    Renderer which serializes to CBOR.
    """

    media_type = 'application/cbor'
    format = 'cbor'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Renders *obj* into serialized CBOR.
        """
        if data is None:
            return ''
        # print('START CBOR RENDER')
        #gc.collect()
        #insize = sys.getsizeof(data)
        #outdata = cbor.dumps(data)
        #outsize = sys.getsizeof(outdata)
        #print('CBOR render from %d to %d' % (insize, outsize))
        #return outdata
        return cbor.dumps(data)
