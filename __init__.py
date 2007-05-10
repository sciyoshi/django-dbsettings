import datetime, re, sys
from bisect import bisect

from django.utils.functional import curry
from django import newforms as forms
from django.db import transaction

import models

_values = {}
_value_list = []

# A transaction is necessary for backends like PostgreSQL
transaction.enter_transaction_management()
try:
    # Retrieve all stored values once during startup
    for value in models.Value.objects.all():
        _values[value.module_name, value.class_name, value.attribute_name] = value
except:
    # Necessary in case values were used in models
    # prior to syncdb setting up the value storage
    transaction.rollback()
transaction.leave_transaction_management()

def get_value(module_name, class_name, attribute_name):
    return _values[module_name, class_name, attribute_name].content

def get_descriptor(module_name, class_name, attribute_name):
    return _values[module_name, class_name, attribute_name].descriptor

def set_value(module_name, class_name, attribute_name, value):
    model = _values.get((module_name, class_name, attribute_name), None)
    if model is None:
        _values[module_name, class_name, attribute_name] = model = models.Value(
            module_name=module_name,
            class_name=class_name,
            attribute_name=attribute_name,
        )
    try:
        model.content = model.descriptor.get_db_prep_save(value)
    except AttributeError:
        model.content = str(value)
    model.save()

def get_all_values():
    return _value_list

class OptionsBase(type):
    def __init__(cls, name, bases, attrs):
        if not bases or bases == (object,):
            return
        attrs.pop('__module__', None)
        for attribute_name, attr in attrs.items():
            if not isinstance(attr, Value):
                raise TypeError('The type of %s (%s) is not a valid Value.' % (attribute_name, attr.__class__.__name__))
            cls.add_to_class(attribute_name, attr)

# FIXME: Add in the rest of the options
class Options(object):
    __metaclass__ = OptionsBase

    def __new__(cls):
        attrs = [(k, v.copy()) for (k, v) in cls.__dict__.items() if isinstance(v, Value)]
        attrs.sort(lambda a, b: cmp(a[1], b[1]))

        for key, attr in attrs:
            attr.creation_counter = Value.creation_counter
            Value.creation_counter += 1
            if attr.key not in _values:
                # This value isn't already stored in the database
                _values[attr.key] = models.Value(
                    module_name=attr.module_name,
                    class_name=attr.class_name,
                    attribute_name=attr.attribute_name,
                )

            # Set up cache storage for external access
            _values[attr.key].descriptor = attr
            _value_list.insert(bisect(_value_list, attr), attr)

        # Make sure the module reflects where it was executed
        attrs += (('__module__', sys._getframe(1).f_globals['__name__']),)

        # A new class is created so descriptors work properly
        # object.__new__ is necessary here to avoid recursion
        return object.__new__(type('Options', (cls,), dict(attrs)))

    def contribute_to_class(self, cls, name):
        # Override the class_name of all registered values
        for attr in self.__class__.__dict__.values():
            if isinstance(attr, Value):
                attr.module_name = cls.__module__
                attr.class_name = cls.__name__

                if attr.key not in _values:
                    # This value isn't already stored in the database
                    _values[attr.key] = models.Value(
                        module_name=attr.module_name,
                        class_name=attr.class_name,
                        attribute_name=attr.attribute_name,
                    )

                # Set up cache storage for external access
                _values[attr.key].descriptor = attr

        # Create permission for editing values on the model
        permission = (
            'can_edit_%s_values' % cls.__name__.lower(),
            'Can edit %s values' % cls._meta.verbose_name,
        )
        if permission not in cls._meta.permissions:
            # Add a permission for the value editor
            try:
                cls._meta.permissions.append(permission)
            except AttributeError:
                # Permissions were supplied as a tuple, so preserve that
                cls._meta.permissions = tuple(cls._meta.permissions + (permission,))

        # Finally, plaec the attribute on the class
        setattr(cls, name, self)

    def add_to_class(cls, attribute_name, value):
        value.contribute_to_class(cls, attribute_name)
    add_to_class = classmethod(add_to_class)

    def __add__(self, other):
        if not isinstance(other, Options):
            raise NotImplementedError('Options may only be added to other options.')

        options = type('Options', (Options,), {'__module__': sys._getframe(1).f_globals['__name__']})()

        for attribute_name, attr in self.__class__.__dict__.items():
            if isinstance(attr, Value):
                options.__class__.add_to_class(attribute_name, attr)
        for attribute_name, attr in other.__class__.__dict__.items():
            if isinstance(attr, Value):
                options.__class__.add_to_class(attribute_name, attr)
        return options

    @classmethod
    def __iter__(cls):
        attrs = [v for v in cls.__dict__.values() if isinstance(v, Value)]
        attrs.sort(lambda a, b: cmp(a[1], b[1]))
        for attr in attrs:
            yield attr
        return
        attrs = [(v.attribute_name, v.copy()) for v in cls if isinstance(v, Value)]
        attrs.sort()

class Value(object):

    creation_counter = 0

    def __init__(self, description=None, help_text=None):
        self.description = description
        self.help_text = help_text
        self.creation_counter = Value.creation_counter
        Value.creation_counter += 1

    def __cmp__(self, other):
        # This is needed because bisect does not take a comparison function.
        return cmp(self.creation_counter, other.creation_counter)

    def copy(self):
        new_value = self.__class__(self.description, self.help_text)
        new_value.__dict__ = self.__dict__.copy()
        return new_value

    def key(self):
        return self.module_name, self.class_name, self.attribute_name
    key = property(key)

    def contribute_to_class(self, cls, attribute_name):
        if not issubclass(cls, Options):
            pass#return
        self.module_name = cls.__module__
        self.class_name = ''
        self.attribute_name = attribute_name
        self.description = self.description or attribute_name.replace('_', ' ')

        setattr(cls, self.attribute_name, self)

    def __get__(self, instance=None, type=None):
        if instance == None:
            raise AttributeError, "%s is only accessible from %s instances." % (self.attribute_name, type.__name__)
        value = _values.get(self.key, None)
        if value:
            return self.to_python(value.content)

    def get_rendered_field(self):
        value = _values.get(self.key, None)
        if value:
            data = value.content
        else:
            data = ''
        return self.field.render(data)

    # Subclasses should override the following methods where applicable

    def to_python(self, value):
        "Returns a native Python object suitable for immediate use"
        return value

    def get_db_prep_save(self, value):
        "Returns a value suitable for storage into a CharField"
        return str(value)

    def to_editor(self, value):
        "Returns a value suitable for the value editor component"
        return str(value)

###############
# VALUE TYPES #
###############

class BooleanValue(Value):

    class field(forms.BooleanField):

        def __init__(self, *args, **kwargs):
            kwargs['required'] = False
            forms.BooleanField.__init__(self, *args, **kwargs)

    def to_python(self, value):
        if value in (True, 't', 'True'):
            return True
        return False

    to_editor = to_python

class IntegerValue(Value):
    field = forms.IntegerField

    def to_python(self, value):
        return int(value)

class PositiveIntegerValue(IntegerValue):

    class field(forms.IntegerField):

        def __init__(self, *args, **kwargs):
            kwargs['min_value'] = 0
            forms.IntegerField.__init__(self, *args, **kwargs)

class PercentValue(IntegerValue):

    class field(forms.IntegerField):

        def __init__(self, *args, **kwargs):
            forms.IntegerField.__init__(self, 100, 0, *args, **kwargs)

        class widget(forms.TextInput):
            def render(self, *args, **kwargs):
                # Place a percent sign after a smaller text field
                attrs = kwargs.pop('attrs', {})
                attrs['size'] = attrs['maxlength'] = 3
                return forms.TextInput.render(self, attrs=attrs, *args, **kwargs) + '%'

    def to_python(self, value):
        return float(value) / 100

class StringValue(Value):
    field = forms.CharField

# DurationValue has a lot of duplication and ugliness because of issue #2443
# Until DurationField is sorted out, this has to do some extra work
class DurationValue(Value):

    class field(forms.CharField):
        def clean(self, value):
            try:
                return datetime.timedelta(seconds=float(value))
            except (ValueError, TypeError):
                raise forms.ValidationError('This value must be a real number.')
            except OverflowError:
                raise forms.ValidationError('The maximum allowed value is %s' % datetime.timedelta.max)

    def to_python(self, value):
        if isinstance(value, datetime.timedelta):
            return value
        try:
            return datetime.timedelta(seconds=float(value))
        except (ValueError, TypeError):
            raise forms.ValidationError('This value must be a real number.')
        except OverflowError:
            raise forms.ValidationError('The maximum allowed value is %s' % datetime.timedelta.max)

    def get_db_prep_save(self, value):
        return str(value.days * 24 * 3600 + value.seconds + float(value.microseconds) / 1000000)

