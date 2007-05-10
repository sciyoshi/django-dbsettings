import re

from django.db.models import get_model
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.text import capfirst
from django import newforms as forms
from django.newforms.forms import SortedDictFromList
from django.contrib.admin.views.decorators import staff_member_required

from django.contrib import values

regex = re.compile(r'^(.+)__(.*)__(.+)$')

# This is just a placeholder for now, fields will be added dynamically on each request
class ValueEditor(forms.BaseForm):

    def __iter__(self):
        for field in super(ValueEditor, self).__iter__():
            yield self.specialize(field)

    def __getitem__(self, name):
        field = super(ValueEditor, self).__getitem__(name)
        return self.specialize(field)

    def specialize(self, field):
        "Wrapper to add module_name and class_name for regrouping"
        field.label = capfirst(field.label)
        module_name, class_name, x = regex.match(field.name).groups()

        app_label = module_name.split('.')[-2];
        field.module_name = capfirst(app_label)

        if class_name:
            if get_model(app_label, class_name):
                class_name = capfirst(get_model(app_label, class_name)._meta.verbose_name)
            else:
                class_name = capfirst(class_name)
        field.class_name = class_name

        return field

def get_fields(user):
    # Retrieves all value fields available for the given user
    fields = SortedDictFromList()
    for value in values.get_all_values():
        app_label = value.module_name.split('.')[-2]
        perm = '%s.can_edit_%s_values' % (app_label, value.class_name.lower())
        initial = ''
        if user.has_perm(perm):
            # Provide current values for initializing the form
            current = values.get_value(*value.key)
            initial = current and value.to_editor(current)

            # Add the field to the customized field list
            fields['%s__%s__%s' % value.key] = value.field(label=value.description, initial=initial)
    return fields

def editor(request):
    # Create an editor customized for the current user
    editor = type('ValueEditor', (ValueEditor,), {'base_fields': get_fields(request.user)})

    if request.method == 'POST':
        # Populate the form with user-submitted data
        form = editor(request.POST.copy())
        if form.is_valid():
            form.full_clean()
            for name, value in form.clean_data.items():
                key = regex.match(name).groups()
                descriptor = values.get_descriptor(*key)
                try:
                    current_value = descriptor.to_python(values.get_value(*key))
                except:
                    current_value = None
                if current_value != descriptor.to_python(value):
                    args = key + (value,)
                    values.set_value(*args)
                    request.user.message_set.create(message='Updated %s on %s' % (descriptor.description, descriptor.class_name))
            return HttpResponseRedirect(request.path)
    else:
        # Leave the form populated with current values
        form = editor()

    return render_to_response('admin/edit_values.html', {
        'form': form,
    }, context_instance=RequestContext(request))
editor = staff_member_required(editor)

