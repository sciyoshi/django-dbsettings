import re

from django.db import models
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.text import capfirst
from django import newforms as forms
from django.contrib.admin.views.decorators import staff_member_required

from django.contrib import values

regex = re.compile(r'^(.+)__(.+)__(.+)$')
value_list = []

def editor(request):

    # This is just a placeholder for now, fields will be added dynamically below
    class ValueEditor(forms.Form):

        def __iter__(self):
            for field in super(ValueEditor, self).__iter__():
                yield self.specialize(field)

        def __getitem__(self, name):
            field = super(ValueEditor, self).__getitem__(name)
            return self.specialize(field)

        def specialize(self, field):
            " Wrapper to add app_label and model_name for regrouping"
            field.label = capfirst(field.label)
            field.app_label, field.model_name, dummy = regex.match(field.name).groups()
            return field

    # Cycle through all apps and models, adding value fields to the form
    for app in models.get_apps():
        for model in models.get_models(app):
            app_label, model_name = model._meta.app_label, model.__name__.lower()
            try:
                for value in values.get_values_by_model(app_label, model_name):
                    if request.user.has_perm('%s.can_edit_%s_values' % (app_label, model_name)):
                        value_list.append((model, value.name))
                        key = '%s__%s__%s' % (app_label, model_name, value.name)
                        field = value.field(label=value.description)
                        ValueEditor.base_fields[key] = field
            except KeyError:
                continue
    
    if request.method == 'POST':
        # Populate the form with user-submitted data
        form = ValueEditor(request.POST.copy())
        if form.is_valid():
            form.full_clean()
            for name, value in form.clean_data.items():
                key = regex.match(name).groups()
                descriptor = values.get_descriptor(*key)
                try:
                    current_value = descriptor.to_python(values.get_value(*key))
                except ValueError:
                    current_value = None
                if current_value != descriptor.to_python(value):
                    args = key + (value,)
                    values.set_value(*args)
                    request.user.message_set.create(message='Updated %s' % descriptor.description)
            return HttpResponseRedirect(request.path)
    else:
        # Populate the form with values currently in use
        value_dict = {}
        for name in ValueEditor.base_fields:
            key = regex.match(name).groups()
            descriptor = values.get_descriptor(*key)
            value_dict[name] = descriptor.to_editor(values.get_value(*key))
        form = ValueEditor(value_dict)

    return render_to_response('admin/edit_values.html', {
        'form': form,
    }, context_instance=RequestContext(request))
editor = staff_member_required(editor)

