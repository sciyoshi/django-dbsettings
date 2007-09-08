from django.db import models
from django import test
from django.utils.functional import curry

import dbsettings
from dbsettings import loading, views

# Set up some settings to test
class TestSettings(dbsettings.Group):
    boolean = dbsettings.BooleanValue()
    integer = dbsettings.IntegerValue()
    string = dbsettings.StringValue()

# This is assigned to module, rather than a model
module_settings = TestSettings()

# These will be populated by the fixture data
class Populated(models.Model):
    settings = TestSettings()

print Populated._meta.permissions

# These will be empty after startup
class Unpopulated(models.Model):
    settings = TestSettings()

class Editable(models.Model):
    settings = TestSettings()

class Combined(models.Model):
    class settings(dbsettings.Group):
        enabled = dbsettings.BooleanValue()
    settings = TestSettings() + settings()

class SettingsTestCase(test.TestCase):
    def setUp(self):
        # Standard test fixtures don't update the in-memory cache.
        # So we have to do it ourselves this time.
        loading.set_setting_value('dbsettings.tests', 'Populated', 'boolean', True)
        loading.set_setting_value('dbsettings.tests', 'Populated', 'integer', 42)
        loading.set_setting_value('dbsettings.tests', 'Populated', 'string', 'Ni!')
        loading.set_setting_value('dbsettings.tests', '', 'boolean', False)
        loading.set_setting_value('dbsettings.tests', '', 'integer', 14)
        loading.set_setting_value('dbsettings.tests', '', 'string', 'Module')
        loading.set_setting_value('dbsettings.tests', 'Combined', 'boolean', False)
        loading.set_setting_value('dbsettings.tests', 'Combined', 'integer', 1138)
        loading.set_setting_value('dbsettings.tests', 'Combined', 'string', 'THX')
        loading.set_setting_value('dbsettings.tests', 'Combined', 'enabled', True)

    def test_settings(self):
        "Make sure settings groups are initialized properly"

        # Settings already in the database are available immediately
        self.assertEqual(Populated.settings.boolean, True)
        self.assertEqual(Populated.settings.integer, 42)
        self.assertEqual(Populated.settings.string, 'Ni!')

        # Module settings are kept separate from model settings
        self.assertEqual(module_settings.boolean, False)
        self.assertEqual(module_settings.integer, 14)
        self.assertEqual(module_settings.string, 'Module')

        # Settings can be added together
        self.assertEqual(Combined.settings.boolean, False)
        self.assertEqual(Combined.settings.integer, 1138)
        self.assertEqual(Combined.settings.string, 'THX')
        self.assertEqual(Combined.settings.enabled, True)

        # Settings not in the database use empty defaults
        self.assertEqual(Unpopulated.settings.boolean, False)
        self.assertEqual(Unpopulated.settings.integer, None)
        self.assertEqual(Unpopulated.settings.string, '')

        # Settings should be retrieved in the order of definition
        self.assertEqual(Populated.settings.keys(), ['boolean', 'integer', 'string'])
        self.assertEqual(Combined.settings.keys(), ['boolean', 'integer', 'string', 'enabled'])

        # Values should be coerced to the proper Python types
        self.assert_(isinstance(Populated.settings.boolean, bool))
        self.assert_(isinstance(Populated.settings.integer, int))
        self.assert_(isinstance(Populated.settings.string, basestring))

        # Settings can not be accessed directly from models, only instances
        self.assertRaises(AttributeError, lambda: Populated().settings)
        self.assertRaises(AttributeError, lambda: Unpopulated().settings)

        # Updates are reflected in the live settings
        loading.set_setting_value('dbsettings.tests', 'Unpopulated', 'boolean', True)
        loading.set_setting_value('dbsettings.tests', 'Unpopulated', 'integer', 13)
        loading.set_setting_value('dbsettings.tests', 'Unpopulated', 'string', 'Friday')
        self.assertEqual(Unpopulated.settings.boolean, True)
        self.assertEqual(Unpopulated.settings.integer, 13)
        self.assertEqual(Unpopulated.settings.string, 'Friday')

        # But they can't be modified in-place
        self.assertRaises(AttributeError, curry(setattr, Unpopulated.settings, 'integer', 10))

    def test_declaration(self):
        "Group declarations can only contain values and a docstring"
        # This definition is fine
        attrs = {
            '__doc__': "This is a docstring",
            'test': dbsettings.IntegerValue(),
        }
        # So this should succeed
        type('GoodGroup', (dbsettings.Group,), attrs)

        # By adding an invalid attribute
        attrs['problem'] = 'not a Value'
        # This should fail
        self.assertRaises(TypeError, curry(type, 'BadGroup', (dbsettings.Group,), attrs))

        # Make sure affect models get the new permissions
        self.assert_('can_edit_populated_settings' in dict(Populated._meta.permissions))
        self.assert_('can_edit_unpopulated_settings' in dict(Unpopulated._meta.permissions))

    def test_forms(self):
        "Forms should display only the appropriate settings"
        from django.contrib.auth.models import User, Permission
        from django.core.urlresolvers import reverse
        
        site_form = reverse(views.site_settings)
        app_form = reverse(views.app_settings, kwargs={'app_label': 'dbsettings'})

        # Set up a users to test the editor forms
        user = User.objects.create_user('dbsettings', '', 'dbsettings')

        # First test without any authenticated user
        response = self.client.get(site_form)
        self.assertTemplateUsed(response, 'admin/login.html')

        # Then test a standard non-staff user
        self.client.login(username='dbsettings', password='dbsettings')
        response = self.client.get(site_form)
        self.assertTemplateUsed(response, 'admin/login.html')

        # Add staff status, but no settings permissions
        user.is_staff = True
        user.save()

        # Test the site-wide settings editor
        response = self.client.get(site_form)
        self.assertTemplateUsed(response, 'dbsettings/site_settings.html')
        self.assertEqual(response.context[0]['title'], 'Site settings')
        # No settings should show up without proper permissions
        self.assertEqual(len(response.context[0]['form'].fields), 0)

        # Add permissions so that settings will show up
        perm = Permission.objects.get(codename='can_edit_editable_settings')
        user.user_permissions.add(perm)

        # Test the app-specific settings editor, now with permissions
        response = self.client.get(app_form)
        self.assertTemplateUsed(response, 'dbsettings/app_settings.html')
        self.assertEqual(response.context[0]['title'], 'Dbsettings settings')
        # Only the Unpopulated settings should show up
        self.assertEqual(len(response.context[0]['form'].fields), 3)

        # Erroneous submissions should be caught by newforms
        data = {
            'dbsettings.tests__Editable__integer': '3.5',
            'dbsettings.tests__Editable__string': '',
        }
        response = self.client.post(site_form, data)
        self.assertFormError(response, 'form', 'dbsettings.tests__Editable__integer', 'Enter a whole number.')
        self.assertFormError(response, 'form', 'dbsettings.tests__Editable__string', 'This field is required.')

        # Successful submissions should redirect
        data = {
            'dbsettings.tests__Editable__integer': '4',
            'dbsettings.tests__Editable__string': 'Success!',
        }
        response = self.client.post(site_form, data)
        self.assertRedirects(response, site_form)

        # And the data submitted should be immediately available in Python
        self.assertEqual(Editable.settings.integer, 4)
        self.assertEqual(Editable.settings.string, 'Success!')