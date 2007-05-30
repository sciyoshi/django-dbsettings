import re

from django.db.models import get_model
#FIXME: from django import newforms as forms
from vgmix3 import newforms as forms
from django.utils.datastructures import SortedDict
from django.utils.text import capfirst

re_field_name = re.compile(r'^(.+)__(.*)__(.+)$')

#FIXME: Remove once working on a recent SVN
class SortedDict(SortedDict):
    def copy(self):
        "Returns a copy of this object."
        # This way of initializing the copy means it works for subclasses, too.
        obj = self.__class__(self)
        obj.keyOrder = self.keyOrder
        return obj

class SettingsEditor(forms.BaseForm):
    "Base editor, from which customized forms are created"

    def __iter__(self):
        for field in super(SettingsEditor, self).__iter__():
            yield self.specialize(field)

    def __getitem__(self, name):
        field = super(SettingsEditor, self).__getitem__(name)
        return self.specialize(field)

    def specialize(self, field):
        "Wrapper to add module_name and class_name for regrouping"
        field.label = capfirst(field.label)
        module_name, class_name, x = re_field_name.match(field.name).groups()

        app_label = module_name.split('.')[-2];
        field.module_name = app_label

        if class_name:
            model = get_model(app_label, class_name)
            if model:
                class_name = model._meta.verbose_name
        field.class_name = class_name

        return field

    def apps(self):
        if self.fields:
            app_list, fields, app_label = [], [], None
            for field in self:
                if app_label and app_label != field.app_label:
                    app_list.append({
                        'app_label': app_label,
                        'fields': fields,
                    })
                    fields = []
                app_label = field.app_label
                fields.append(field)
            return app_list

def customized_editor(user, settings):
    "Customize the setting editor based on the current user and setting list"
    base_fields = SortedDict()
    for setting in settings:
        perm = '%s.can_edit_%s_settings' % (
            setting.module_name.split('.')[-2],
            setting.class_name.lower()
        )
        if user.has_perm(perm):
            # Add the field to the customized field list
            kwargs = {
                'label': setting.description,
                # Provide current setting values for initializing the form
                'initial': setting.to_editor(setting.storage.value),
            }
            if setting.choices:
                field = forms.ChoiceField(choices=setting.choices, **kwargs)
            else:
                field = setting.field(**kwargs)
            base_fields['%s__%s__%s' % setting.key] = field
    return type('SettingsEditor', (SettingsEditor,), {'base_fields': base_fields})