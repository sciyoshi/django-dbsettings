import datetime
import time
import Image
from hashlib import md5
from os.path import join as pjoin

from django import forms
from django.conf import settings
from django.utils.safestring import mark_safe
from django.core.files.uploadedfile import SimpleUploadedFile

from dbsettings.loading import get_setting_storage, set_setting_value

try:
    from decimal import Decimal
except ImportError:
    from django.utils._decimal import Decimal

__all__ = ['Value', 'BooleanValue', 'DecimalValue', 'EmailValue', 
           'DurationValue', 'FloatValue', 'IntegerValue', 'PercentValue', 
           'PositiveIntegerValue', 'StringValue', 'TextValue', 
           'MultiSeparatorValue', 'ImageValue']

class Value(object):

    creation_counter = 0
    unitialized_value = None

    def __init__(self, description=None, help_text=None, choices=None, required=True, default=None):
        self.description = description
        self.help_text = help_text
        self.choices = choices or []
        self.required = required
        if default == None:
            self.default = self.unitialized_value
        else:
            self.default = default

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
            storage = get_setting_storage(*self.key)
            return self.to_python(storage.value)
        except:
            return None

    def __set__(self, instance, value):
        current_value = self.__get__(instance)
        if self.to_python(value) != current_value:
            set_setting_value(*(self.key + (value,)))

    # Subclasses should override the following methods where applicable

    def to_python(self, value):
        "Returns a native Python object suitable for immediate use"
        return value

    def get_db_prep_save(self, value):
        "Returns a value suitable for storage into a CharField"
        return unicode(value)

    def to_editor(self, value):
        "Returns a value suitable for display in a form widget"
        return unicode(value)

###############
# VALUE TYPES #
###############

class BooleanValue(Value):
    unitialized_value = False
    class field(forms.BooleanField):

        def __init__(self, *args, **kwargs):
            kwargs['required'] = False
            forms.BooleanField.__init__(self, *args, **kwargs)

    def to_python(self, value):
        if value in (True, 't', 'True'):
            return True
        return False

    to_editor = to_python

class DecimalValue(Value):
    field = forms.DecimalField

    def to_python(self, value):
        return Decimal(value)

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
        return unicode(value.days * 24 * 3600 + value.seconds + float(value.microseconds) / 1000000)

class FloatValue(Value):
    field = forms.FloatField

    def to_python(self, value):
        return float(value)

class IntegerValue(Value):
    field = forms.IntegerField

    def to_python(self, value):
        return int(value)

class PercentValue(Value):

    class field(forms.DecimalField):

        def __init__(self, *args, **kwargs):
            forms.DecimalField.__init__(self, 100, 0, 5, 2, *args, **kwargs)

        class widget(forms.TextInput):
            def render(self, *args, **kwargs):
                # Place a percent sign after a smaller text field
                attrs = kwargs.pop('attrs', {})
                attrs['size'] = attrs['max_length'] = 6
                return forms.TextInput.render(self, attrs=attrs, *args, **kwargs) + '%'

    def to_python(self, value):
        return Decimal(value) / 100

class PositiveIntegerValue(IntegerValue):

    class field(forms.IntegerField):

        def __init__(self, *args, **kwargs):
            kwargs['min_value'] = 0
            forms.IntegerField.__init__(self, *args, **kwargs)

class StringValue(Value):
    unitialized_value = ''
    field = forms.CharField

class TextValue(Value):
    unitialized_value = ''
    field = forms.CharField

    def to_python(self, value):
        return unicode(value)

class EmailValue(Value):
    unitialized_value = ''
    field = forms.EmailField

    def to_python(self, value):
        return unicode(value)

class MultiSeparatorValue(TextValue):
    """Provides a way to store list-like string settings.
    e.g 'mail@test.com;*@blah.com' would be returned as
        [u'mail@test.com', u'*@blah.com']. What the method
        uses to split on can be defined by passing in a 
        separator string (default is semi-colon as above).
    """

    def __init__(self, description=None, help_text=None, separator=';', required=True, default=None):
        self.separator = separator
        if default != None:
            # convert from list to string
            default = separator.join(default)
        super(MultiSeparatorValue, self).__init__(description=description, 
                                                  help_text=help_text,
                                                  required=required,
                                                  default=default)

    class field(forms.CharField):
        
        class widget(forms.Textarea):
            pass

    def to_python(self, value):
        if value:
            value = unicode(value)
            value = value.split(self.separator)
            value = [x.strip() for x in value]
        else:
            value = []
        return value

class ImageValue(Value):
    def __init__(self, *args, **kwargs):
        if 'upload_to' in kwargs:
            self._upload_to = kwargs.pop('upload_to', '')
        super(ImageValue, self).__init__(*args, **kwargs)

    class field(forms.ImageField):
        class widget(forms.FileInput):
            "Widget with preview"
            def __init__(self, attrs={}):
                forms.FileInput.__init__(self, attrs)

            def render(self, name, value, attrs=None):
                output = []

                try:
                    if not value:
                        raise IOError('No value')

                    Image.open(value.file)
                    file_name = pjoin(settings.MEDIA_URL, value.name).replace("\\","/")
                    params = {"file_name" : file_name }
                    output.append(u'<p><img src="%(file_name)s" width="100" /></p>' % params )
                except IOError:
                    pass

                output.append(forms.FileInput.render(self, name, value, attrs))
                return mark_safe(''.join(output))

    def to_python(self, value):
        "Returns a native Python object suitable for immediate use"
        return unicode(value)

    def get_db_prep_save(self, value):
        "Returns a value suitable for storage into a CharField"
        if not value:
            return None

        hashed_name = md5(unicode(time.time())).hexdigest() + value.name[-4:]
        image_path = pjoin(self._upload_to, hashed_name)
        dest_name = pjoin(settings.MEDIA_ROOT, image_path)

        with open(dest_name, 'wb+') as dest_file:
            for chunk in value.chunks():
                dest_file.write(chunk)

        return unicode(image_path)

    def to_editor(self, value):
        "Returns a value suitable for display in a form widget"
        if not value:
            return None

        file_name = pjoin(settings.MEDIA_ROOT, value)
        try:
            with open(file_name, 'rb') as f:
                uploaded_file = SimpleUploadedFile(value, f.read(), 'image')

                # hack to retrieve path from `name` attribute
                uploaded_file.__dict__['_name'] = value
                return uploaded_file
        except IOError:
            return None

