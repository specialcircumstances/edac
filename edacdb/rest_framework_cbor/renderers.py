'''
This is a direct adaptation of Django Rest Framework Msgpack (v1.0.1)
https://github.com/juanriaza/django-rest-framework-msgpack
to use the cbor2 library
https://pypi.org/project/cbor2/

'''

#import msgpack
import cbor2        # In my tests this appeared to give better perf than cbor
import decimal
import datetime
import sys # temp

from rest_framework.renderers import BaseRenderer


class CBOREncoder(object):

    def encode(self, obj):
        # I think this might not be necessary with the CBOR2 encoder
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
        print('Start CBOR')
        print(sys.getsizeof(data))
        outdata = cbor2.dumps(data)
        print(sys.getsizeof(outdata))
        print('Finish CBOR')
        return outdata
        return cbor2.dumps(data)
