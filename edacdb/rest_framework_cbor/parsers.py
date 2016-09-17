'''
This is a direct adaptation of Django Rest Framework Msgpack (v1.0.1)
https://github.com/juanriaza/django-rest-framework-msgpack
to use the cbor2 library
https://pypi.org/project/cbor2/

'''

import decimal
#import msgpack
import cbor2        # In my tests this appeared to give better perf than cbor
#from dateutil.parser import parse

from rest_framework.parsers import BaseParser
from rest_framework.exceptions import ParseError


class CBORDecoder(object):

    # TODO Verify if these MessagePack decodes are appropriate for CBOR
    # I think CBOR2 module does all these for me?

    def decode(self, obj):
        if '__class__' in obj:
            decode_func = getattr(self, 'decode_%s' % obj['__class__'])
            return decode_func(obj)
        return obj

    def decode_datetime(self, obj):
        return parse(obj['as_str'])

    def decode_date(self, obj):
        return parse(obj['as_str']).date()

    def decode_time(self, obj):
        return parse(obj['as_str']).time()

    def decode_decimal(self, obj):
        return decimal.Decimal(obj['as_str'])


class CBORParser(BaseParser):
    """
    Parses CBOR-serialized data.
    """

    media_type = 'application/cbor'

    def parse(self, stream, media_type=None, parser_context=None):
        try:
            # return cbor2.load(stream,
            #                    use_list=True,
            #                    encoding="utf-8",
            #                    object_hook=CBORDecoder().decode)
            # return cbor2.load(stream)
            data = stream.read().decode(encoding)
            return cbor2.loads(data)
        except Exception as exc:
            raise ParseError('CBOR parse error - %s' % unicode(exc))
