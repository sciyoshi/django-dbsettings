import datetime

from django import newforms as forms

__all__ = ['Value', 'BooleanValue', 'DurationValue', 'FloatValue',
    'IntegerValue', 'PercentValue', 'PositiveIntegerValue', 'StringValue']

class Value(object):

    creation_counter = 0

    def __init__(self, description=None, help_text=None, choices=None):
        self.description = description
        self.help_text = help_text
        self.choices = choices or []

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
        self.module_name = cls.__module__
        self.class_name = ''
        self.attribute_name = attribute_name
        self.description = self.description or attribute_name.replace('_', ' ')

        setattr(cls, self.attribute_name, self)

    def __get__(self, instance=None, type=None):
        if instance == None:
            raise AttributeError, "%r is only accessible from %s instances." % (self.attribute_name, type.__name__)
        try:
            return self.to_python(self.storage.value)
        except:
            return None

    def __set__(self, instance, value):
        raise NotImplementedError, "Settings may not changed in this manner."

    # Subclasses should override the following methods where applicable

    def to_python(self, value):
        "Returns a native Python object suitable for immediate use"
        return value

    def get_db_prep_save(self, value):
        "Returns a value suitable for storage into a CharField"
        return str(value)

    def to_editor(self, value):
        "Returns a value suitable for display in a form widget"
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

class FloatValue(Value):
    field = forms.FloatField

    def to_python(self, value):
        return float(value)

class IntegerValue(Value):
    field = forms.IntegerField

    def to_python(self, value):
        return int(value)

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

class PositiveIntegerValue(IntegerValue):

    class field(forms.IntegerField):

        def __init__(self, *args, **kwargs):
            kwargs['min_value'] = 0
            forms.IntegerField.__init__(self, *args, **kwargs)

class StringValue(Value):
    field = forms.CharField