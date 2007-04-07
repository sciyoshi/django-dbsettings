import re, datetime

from django.db import models
from django.utils.text import capfirst
from django.core import validators

_cache = {}

class SubclassField(models.CharField):
    def __init__(self, cls, *args, **kwargs):
        try:
            __old__ = cls.__metaclass__.__init__

            def __init__(cls, name, bases, attrs):
                __old__(cls, name, bases, attrs)
                key = '%s.%s' % (cls.__module__, name)
                _cache[key] = cls
                self.choices.append((key, capfirst(cls._meta.verbose_name)))

            cls.__metaclass__.__init__ = __init__
            super(SubclassField, self).__init__(maxlength=255, *args, **kwargs)
        except AttributeError:
            raise SubclassField.MetaclassError("'%s' must be metaclassed to use SubclassField" % cls.__name__)

    def to_python(self, value):
        print 'to_python: %s' % value
        if value in _cache:
            return _cache[value]
        raise validators.ValidationError('The specified subclass is not known')

    def get_internal_type(self):
        return "CharField"

    def get_db_prep_lookup(self, lookup_type, value):
        if issubclass(value, self.cls):
            value = '%s.%s' % (value.__module__, value.__name__)

        return super(SubclassField, self).get_db_prep_lookup(lookup_type, value)

    class MetaclassError(Exception):
        pass

rgb_hex = re.compile(r'^[0-9A-Fa-f]{6}$')

class RGBField(models.CharField):
    def __init__(self, *args, **kwargs):
        super(RGBField, self).__init__(maxlength=6, *args, **kwargs)

    def get_internal_type(self):
        return "CharField"

    def validate(self, field_data, all_data):
        if not rgb_hex.match(field_data):
            raise validators.ValidationError('This field requires %d hexadecimal characters (0-9, A-F).' % self.maxlength)

class DurationField(models.FloatField):

    def __init__(self, *args, **kwargs):
        super(DurationField, self).__init__(max_digits=20, decimal_places=6)

    def get_internal_type(self):
        return "FloatField"

    def to_python(self, value):
        print 'BLAHBLAHBLAH'
        try:
            return datetime.timedelta(seconds=value)
        except TypeError:
            raise validators.ValidationError('This value must be a real number.')
        except OverflowError:
            raise validators.ValidationError('The maximum allowed value is %s' % datetime.timedelta.max)

