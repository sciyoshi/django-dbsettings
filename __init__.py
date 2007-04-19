import re, datetime
from bisect import bisect

from django.utils.functional import curry
from django import newforms as forms
from django.db import transaction

import models

_values, _values_by_model = {}, {}

# A transaction is necessary for backends like PostgreSQL
transaction.enter_transaction_management()
try:
    # Retrieve all stored values once during startup
    for value in models.Value.objects.all():
        _values[value.app_label, value.model, value.name] = value
except:
    # Necessary in case values were used in models
    # prior to syncdb setting up the value storage
    transaction.rollback()
transaction.leave_transaction_management()

def get_value(app_label, model_name, name):
    return _values[app_label, model_name, name].content

def get_descriptor(app_label, model_name, name):
    return _values[app_label, model_name, name].descriptor

def set_value(app_label, model_name, name, value):
    model = _values.get((app_label, model_name, name), None)
    if model is None:
        _values[app_label, model_name, name] = model = models.Value(
            app_label=app_label,
            model=model_name,
            name=name,
        )
    try:
        model.content = model.descriptor.get_db_prep_save(value)
    except AttributeError:
        model.content = str(value)
    model.save()

def get_values_by_model(app_label, model):
    return _values_by_model[app_label, model]

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

    def contribute_to_class(self, cls, name):
        self.app_label = cls._meta.app_label
        self.model = cls.__name__.lower()
        self.name = name
        self.description = self.description or name.replace('_', ' ')
        self.key = (self.app_label, self.model, self.name)
        if self.key not in _values:
            # This value isn't already stored in the database
            _values[self.key] = models.Value(
                app_label=self.app_label,
                model=self.model,
                name=self.name,
            )

        permission = (
            'can_edit_%s_values' % cls._meta.verbose_name,
            'Can edit %s values' % cls._meta.verbose_name,
        )
        if permission not in cls._meta.permissions:
            # Add a permission for the value editor
            try:
                cls._meta.permissions.append(permission)
            except AttributeError:
                # Permissions were supplied as a tuple, so preserve that
                cls._meta.permissions = tuple(cls._meta.permissions + (permission,))

        # Set up cache storage for external access
        _values[self.key].descriptor = self
        if (self.app_label, self.model) not in _values_by_model:
            _values_by_model[self.app_label, self.model] = []
        by_model_list = _values_by_model[self.app_label, self.model]
        by_model_list.insert(bisect(by_model_list, self), self)

        setattr(cls, self.name, self)

    def __get__(self, instance=None, type=None):
        if instance != None:
            raise AttributeError, "%s isn't accessible via %s instances" % (self.name, type.__name__)
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

