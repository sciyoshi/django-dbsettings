def set_defaults(app, *defaults):
    "Installs a set of default values during syncdb processing"
    from django.core.exceptions import ImproperlyConfigured
    from django.db.models import signals
    from dbsettings.loading import get_setting_storage, set_setting_value

    if not defaults:
        raise ImproperlyConfigured("No defaults were supplied to set_defaults.")
    app_label = app.__name__.split('.')[-2]

    def install_settings(app, created_models, verbosity=2, **kwargs):
        printed = False

        for class_name, attribute_name, value in defaults:
            if not get_setting_storage(app.__name__, class_name, attribute_name):
                if verbosity >= 2 and not printed:
                    # Print this message only once, and only if applicable
                    print "Installing default settings for %s" % app_label
                    printed = True
                try:
                    set_setting_value(app.__name__, class_name, attribute_name, value)
                except:
                    raise ImproperlyConfigured("%s requires dbsettings." % app_label)

    signals.post_syncdb.connect(install_settings, sender=app, weak=False)
