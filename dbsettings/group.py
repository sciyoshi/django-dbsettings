import sys
from django.utils import six

from dbsettings.values import Value
from dbsettings.loading import register_setting, unregister_setting
from dbsettings.management import mk_permissions

__all__ = ['Group']


class GroupBase(type):
    def __init__(mcs, name, bases, attrs):
        if not bases or bases == (object,):
            return
        attrs.pop('__module__', None)
        attrs.pop('__doc__', None)
        attrs.pop('__qualname__', None)
        for attribute_name, attr in attrs.items():
            if not isinstance(attr, Value):
                raise TypeError('The type of %s (%s) is not a valid Value.' %
                                (attribute_name, attr.__class__.__name__))
            mcs.add_to_class(attribute_name, attr)
        super(GroupBase, mcs).__init__(name, bases, attrs)


class GroupDescriptor(object):
    def __init__(self, group, attribute_name):
        self.group = group
        self.attribute_name = attribute_name

    def __get__(self, instance=None, cls=None):
        if instance is not None:
            raise AttributeError("%r is not accessible from %s instances." %
                                 (self.attribute_name, cls.__name__))
        return self.group


@six.add_metaclass(GroupBase)
class Group(object):

    def __new__(cls, verbose_name=None, copy=True, app_label=None):
        # If not otherwise provided, set the module to where it was executed
        if '__module__' in cls.__dict__:
            module_name = cls.__dict__['__module__']
        else:
            module_name = sys._getframe(1).f_globals['__name__']

        attrs = [(k, v) for (k, v) in cls.__dict__.items() if isinstance(v, Value)]
        if copy:
            attrs = [(k, v.copy()) for (k, v) in attrs]
        attrs.sort(key=lambda a: a[1])

        for _, attr in attrs:
            attr.creation_counter = Value.creation_counter
            Value.creation_counter += 1
            if not hasattr(attr, 'verbose_name'):
                attr.verbose_name = verbose_name
            if app_label:
                attr._app = app_label
            register_setting(attr)

        attr_dict = dict(attrs + [('__module__', module_name)])

        # A new class is created so descriptors work properly
        # object.__new__ is necessary here to avoid recursion
        group = object.__new__(type('Group', (cls,), attr_dict))
        group._settings = attrs

        return group

    def contribute_to_class(self, cls, name):
        # Override module_name and class_name of all registered settings
        for attr in self.__class__.__dict__.values():
            if isinstance(attr, Value):
                unregister_setting(attr)
                attr.module_name = cls.__module__
                attr.class_name = cls.__name__
                attr._app = cls._meta.app_label
                register_setting(attr)

        # Create permission for editing settings on the model
        permission = (
            'can_edit_%s_settings' % cls.__name__.lower(),
            'Can edit %s settings' % cls._meta.verbose_name_raw,
        )
        if permission not in cls._meta.permissions:
            # Add a permission for the setting editor
            try:
                cls._meta.permissions.append(permission)
            except AttributeError:
                # Permissions were supplied as a tuple, so preserve that
                cls._meta.permissions = tuple(cls._meta.permissions + (permission,))
        # Django migrations runner cache properties
        if hasattr(cls._meta, 'original_attrs'):
            cls._meta.original_attrs['permissions'] = cls._meta.permissions

        # Finally, place the attribute on the class
        setattr(cls, name, GroupDescriptor(self, name))

    @classmethod
    def add_to_class(cls, attribute_name, value):
        value.contribute_to_class(cls, attribute_name)

    def __add__(self, other):
        if not isinstance(other, Group):
            raise NotImplementedError('Groups may only be added to other groups.')

        attrs = dict(self._settings + other._settings)
        attrs['__module__'] = sys._getframe(1).f_globals['__name__']
        return type('Group', (Group,), attrs)(copy=False)

    def __iter__(self):
        for attribute_name, _ in self._settings:
            yield attribute_name, getattr(self, attribute_name)

    def keys(self):
        return [k for (k, _) in self]

    def values(self):
        return [v for (_, v) in self]
