from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.text import capfirst
from django.contrib import messages

from dbsettings import loading, forms

def app_settings(request, app_label, template='dbsettings/app_settings.html'):
    # Determine what set of settings this editor is used for
    if app_label is None:
        settings = loading.get_all_settings()
        title = 'Site settings'
    else:
        settings = loading.get_app_settings(app_label)
        title = '%s settings' % capfirst(app_label)

    # Create an editor customized for the current user
    editor = forms.customized_editor(request.user, settings)

    if request.method == 'POST':
        # Populate the form with user-submitted data
        form = editor(request.POST.copy(), request.FILES)
        if form.is_valid():
            form.full_clean()

            for name, value in form.cleaned_data.items():
                key = forms.re_field_name.match(name).groups()
                setting = loading.get_setting(*key)
                try:
                    storage = loading.get_setting_storage(*key)
                    current_value = setting.to_python(storage.value)
                except:
                    current_value = None

                if current_value != setting.to_python(value):
                    args = key + (value,)
                    loading.set_setting_value(*args)

                    # Give user feedback as to which settings were changed
                    if setting.class_name:
                        location = setting.class_name
                    else:
                        location = setting.module_name
                    update_msg = u'Updated %s on %s' % (unicode(setting.description), location)
                    messages.add_message(request, messages.INFO, update_msg )

            return HttpResponseRedirect(request.path)
    else:
        # Leave the form populated with current setting values
        form = editor()

    return render_to_response(template, {
        'title': title,
        'form': form,
    }, context_instance=RequestContext(request))
app_settings = staff_member_required(app_settings)

# Site-wide setting editor is identical, but without an app_label
def site_settings(request):
    return app_settings(request, app_label=None, template='dbsettings/site_settings.html')
# staff_member_required is implied, since it calls app_settings
