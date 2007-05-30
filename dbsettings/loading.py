from bisect import bisect

from django.utils.datastructures import SortedDict
from django.db import transaction

from dbsettings.models import Setting

__all__ = ['get_all_settings', 'get_setting', 'get_setting_storage',
    'register_setting', 'set_setting_value']

class SettingDict(SortedDict):
    "Sorted dict that has a bit more list-type functionality"
    def insert(self, key, index, value):
        if key not in self.keys():
            self.keyOrder.insert(index, key)
            self[key] = value

    def __iter__(self):
        for k in self.keyOrder:
            yield self[k]

    def __contains__(self, value):
        for v in self.values():
            if v == value:
                return True
        return False

_settings = SettingDict()
_storage = {}
_initialized = [False]

def get_all_settings():
    return list(_settings)

def get_app_settings(app_label):
    return [p for p in _settings if app_label == p.module_name.split('.')[-2]]

def get_setting(module_name, class_name, attribute_name):
    return _settings[module_name, class_name, attribute_name]

def get_setting_storage(module_name, class_name, attribute_name):
    return _storage.setdefault(
        (module_name, class_name, attribute_name),
        Setting(
            module_name=module_name,
            class_name=class_name,
            attribute_name=attribute_name,
        )
    )

def register_setting(setting):
    # If DB has not yet been queried, run a query
    if not _initialized[0]:
        # A transaction is necessary for backends like PostgreSQL
        transaction.enter_transaction_management()
        try:
            # Retrieve all stored setting values once during startup
            for p in Setting.objects.all():
                _storage[p.module_name, p.class_name, p.attribute_name] = p
        except:
            # Necessary in case setting values were used
            # prior to syncdb setting up data storage
            transaction.rollback()
        transaction.leave_transaction_management()
        # Make sure initialization doesn't happen again
        _initialized[0] = True

    setting.storage = get_setting_storage(*setting.key)
    if setting not in _settings:
        _settings.insert(setting.key, bisect(list(_settings), setting), setting)
    else:
        _settings[setting.key] = setting

def set_setting_value(module_name, class_name, attribute_name, value):
    setting = get_setting(module_name, class_name, attribute_name)
    setting.storage.value = setting.get_db_prep_save(value)
    setting.storage.save()