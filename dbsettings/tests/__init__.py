import datetime

from django.db import models
from django import test
from django.utils.functional import curry
from django.utils.translation import activate, deactivate

import dbsettings
from dbsettings import loading, views

# Set up some settings to test
class TestSettings(dbsettings.Group):
    boolean = dbsettings.BooleanValue()
    integer = dbsettings.IntegerValue()
    string = dbsettings.StringValue()
    list_semi_colon = dbsettings.MultiSeparatorValue()
    list_comma = dbsettings.MultiSeparatorValue(separator=',')
    date = dbsettings.DateValue()
    time = dbsettings.TimeValue()
    datetime = dbsettings.DateTimeValue()

# This is assigned to module, rather than a model
module_settings = TestSettings()

class Defaults(models.Model):
    class settings(dbsettings.Group):
        boolean = dbsettings.BooleanValue(default=True)
        boolean_false = dbsettings.BooleanValue(default=False)
        integer = dbsettings.IntegerValue(default=1)
        string = dbsettings.StringValue(default="default")
        list_semi_colon = dbsettings.MultiSeparatorValue(default=['one','two'])
        list_comma = dbsettings.MultiSeparatorValue(separator=',',default=('one','two'))
        date = dbsettings.DateValue(default=datetime.date(2012, 3, 14))
        time = dbsettings.TimeValue(default=datetime.time(12, 3, 14))
        datetime = dbsettings.DateTimeValue(default=datetime.datetime(2012, 3, 14, 12, 3, 14))
    settings = settings()

# These will be populated by the fixture data
class Populated(models.Model):
    settings = TestSettings()

# These will be empty after startup
class Unpopulated(models.Model):
    settings = TestSettings()

# These will allow blank values
class Blankable(models.Model):
    settings = TestSettings()

class Editable(models.Model):
    settings = TestSettings('Verbose name')

class Combined(models.Model):
    class settings(dbsettings.Group):
        enabled = dbsettings.BooleanValue()
    settings = TestSettings() + settings()

# For registration testing
class ClashSettings1(dbsettings.Group):
    clash1 = dbsettings.BooleanValue()

class ClashSettings2(dbsettings.Group):
    clash2 = dbsettings.BooleanValue()

class ClashSettings1_2(dbsettings.Group):
    clash1 = dbsettings.IntegerValue()
    clash2 = dbsettings.IntegerValue()

module_clash1 = ClashSettings1()

class ModelClash(models.Model):
    settings = ClashSettings1_2()

module_clash2 = ClashSettings2()


class SettingsTestCase(test.TestCase):
    urls = 'dbsettings.tests.test_urls'

    @classmethod
    def setUpClass(cls):
        # Since some text assertions are performed, make sure that no translation interrupts.
        activate('en')

    @classmethod
    def tearDownClass(cls):
        deactivate()

    def setUp(self):
        # Standard test fixtures don't update the in-memory cache.
        # So we have to do it ourselves this time.
        loading.set_setting_value('dbsettings.tests', 'Populated', 'boolean', True)
        loading.set_setting_value('dbsettings.tests', 'Populated', 'integer', 42)
        loading.set_setting_value('dbsettings.tests', 'Populated', 'string', 'Ni!')
        loading.set_setting_value('dbsettings.tests', 'Populated', 'list_semi_colon', 'a@b.com;c@d.com;e@f.com')
        loading.set_setting_value('dbsettings.tests', 'Populated', 'list_comma', 'a@b.com,c@d.com,e@f.com')
        loading.set_setting_value('dbsettings.tests', 'Populated', 'date', '2012-06-28')
        loading.set_setting_value('dbsettings.tests', 'Populated', 'time', '16:19:17')
        loading.set_setting_value('dbsettings.tests', 'Populated', 'datetime', '2012-06-28 16:19:17')
        loading.set_setting_value('dbsettings.tests', '', 'boolean', False)
        loading.set_setting_value('dbsettings.tests', '', 'integer', 14)
        loading.set_setting_value('dbsettings.tests', '', 'string', 'Module')
        loading.set_setting_value('dbsettings.tests', '', 'list_semi_colon', 'g@h.com;i@j.com;k@l.com')
        loading.set_setting_value('dbsettings.tests', '', 'list_comma', 'g@h.com,i@j.com,k@l.com')
        loading.set_setting_value('dbsettings.tests', '', 'date', '2011-05-27')
        loading.set_setting_value('dbsettings.tests', '', 'time', '15:18:16')
        loading.set_setting_value('dbsettings.tests', '', 'datetime', '2011-05-27 15:18:16')
        loading.set_setting_value('dbsettings.tests', 'Combined', 'boolean', False)
        loading.set_setting_value('dbsettings.tests', 'Combined', 'integer', 1138)
        loading.set_setting_value('dbsettings.tests', 'Combined', 'string', 'THX')
        loading.set_setting_value('dbsettings.tests', 'Combined', 'list_semi_colon', 'm@n.com;o@p.com;q@r.com')
        loading.set_setting_value('dbsettings.tests', 'Combined', 'list_comma', 'm@n.com,o@p.com,q@r.com')
        loading.set_setting_value('dbsettings.tests', 'Combined', 'date', '2010-04-26')
        loading.set_setting_value('dbsettings.tests', 'Combined', 'time', '14:17:15')
        loading.set_setting_value('dbsettings.tests', 'Combined', 'datetime', '2010-04-26 14:17:15')
        loading.set_setting_value('dbsettings.tests', 'Combined', 'enabled', True)

    def test_settings(self):
        "Make sure settings groups are initialized properly"

        # Settings already in the database are available immediately
        self.assertEqual(Populated.settings.boolean, True)
        self.assertEqual(Populated.settings.integer, 42)
        self.assertEqual(Populated.settings.string, 'Ni!')
        self.assertEqual(Populated.settings.list_semi_colon, ['a@b.com', 'c@d.com', 'e@f.com'])
        self.assertEqual(Populated.settings.list_comma, ['a@b.com', 'c@d.com', 'e@f.com'])
        self.assertEqual(Populated.settings.date, datetime.date(2012, 6, 28))
        self.assertEqual(Populated.settings.time, datetime.time(16, 19, 17))
        self.assertEqual(Populated.settings.datetime, datetime.datetime(2012, 6, 28, 16, 19, 17))

        # Module settings are kept separate from model settings
        self.assertEqual(module_settings.boolean, False)
        self.assertEqual(module_settings.integer, 14)
        self.assertEqual(module_settings.string, 'Module')
        self.assertEqual(module_settings.list_semi_colon, ['g@h.com', 'i@j.com', 'k@l.com'])
        self.assertEqual(module_settings.list_comma, ['g@h.com', 'i@j.com', 'k@l.com'])
        self.assertEqual(module_settings.date, datetime.date(2011, 5, 27))
        self.assertEqual(module_settings.time, datetime.time(15, 18, 16))
        self.assertEqual(module_settings.datetime, datetime.datetime(2011, 5, 27, 15, 18, 16))

        # Settings can be added together
        self.assertEqual(Combined.settings.boolean, False)
        self.assertEqual(Combined.settings.integer, 1138)
        self.assertEqual(Combined.settings.string, 'THX')
        self.assertEqual(Combined.settings.enabled, True)
        self.assertEqual(Combined.settings.list_semi_colon, ['m@n.com', 'o@p.com', 'q@r.com'])
        self.assertEqual(Combined.settings.list_comma, ['m@n.com', 'o@p.com', 'q@r.com'])
        self.assertEqual(Combined.settings.date, datetime.date(2010, 4, 26))
        self.assertEqual(Combined.settings.time, datetime.time(14, 17, 15))
        self.assertEqual(Combined.settings.datetime, datetime.datetime(2010, 4, 26, 14, 17, 15))

        # Settings not in the database use empty defaults
        self.assertEqual(Unpopulated.settings.boolean, False)
        self.assertEqual(Unpopulated.settings.integer, None)
        self.assertEqual(Unpopulated.settings.string, '')
        self.assertEqual(Unpopulated.settings.list_semi_colon, [])
        self.assertEqual(Unpopulated.settings.list_comma, [])

        # ...Unless a default paramter was specified, then they use that
        self.assertEqual(Defaults.settings.boolean, True)
        self.assertEqual(Defaults.settings.boolean_false, False)
        self.assertEqual(Defaults.settings.integer, 1)
        self.assertEqual(Defaults.settings.string, 'default')
        self.assertEqual(Defaults.settings.list_semi_colon, ['one','two'])
        self.assertEqual(Defaults.settings.list_comma, ['one','two'])
        self.assertEqual(Defaults.settings.date, datetime.date(2012, 3, 14))
        self.assertEqual(Defaults.settings.time, datetime.time(12, 3, 14))
        self.assertEqual(Defaults.settings.datetime, datetime.datetime(2012, 3, 14, 12, 3, 14))


        # Settings should be retrieved in the order of definition
        self.assertEqual(Populated.settings.keys(),
                         ['boolean', 'integer', 'string', 'list_semi_colon',
                          'list_comma', 'date', 'time', 'datetime'])
        self.assertEqual(Combined.settings.keys(),
                         ['boolean', 'integer', 'string', 'list_semi_colon',
                          'list_comma', 'date', 'time', 'datetime', 'enabled'])

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
        loading.set_setting_value('dbsettings.tests', 'Unpopulated', 'list_semi_colon', 'aa@bb.com;cc@dd.com')
        loading.set_setting_value('dbsettings.tests', 'Unpopulated', 'list_comma', 'aa@bb.com,cc@dd.com')
        # for date/time you can specify string (as above) or proper object
        loading.set_setting_value('dbsettings.tests', 'Unpopulated', 'date', datetime.date(1912, 6, 23))
        loading.set_setting_value('dbsettings.tests', 'Unpopulated', 'time', datetime.time(1, 2, 3))
        loading.set_setting_value('dbsettings.tests', 'Unpopulated', 'datetime', datetime.datetime(1912, 6, 23, 1, 2, 3))

        self.assertEqual(Unpopulated.settings.boolean, True)
        self.assertEqual(Unpopulated.settings.integer, 13)
        self.assertEqual(Unpopulated.settings.string, 'Friday')
        self.assertEqual(Unpopulated.settings.list_semi_colon, ['aa@bb.com', 'cc@dd.com'])
        self.assertEqual(Unpopulated.settings.list_comma, ['aa@bb.com', 'cc@dd.com'])
        self.assertEqual(Unpopulated.settings.date, datetime.date(1912, 6, 23))
        self.assertEqual(Unpopulated.settings.time, datetime.time(1, 2, 3))
        self.assertEqual(Unpopulated.settings.datetime, datetime.datetime(1912, 6, 23, 1, 2, 3))

        # Updating settings with defaults
        loading.set_setting_value('dbsettings.tests', 'Defaults', 'boolean', False)
        self.assertEqual(Defaults.settings.boolean, False)
        loading.set_setting_value('dbsettings.tests', 'Defaults', 'boolean_false', True)
        self.assertEqual(Defaults.settings.boolean_false, True)


        # Updating blankable settings
        self.assertEqual(Blankable.settings.string, '')
        loading.set_setting_value('dbsettings.tests', 'Blankable', 'string', 'Eli')
        self.assertEqual(Blankable.settings.string, 'Eli')
        loading.set_setting_value('dbsettings.tests', 'Blankable', 'string', '')
        self.assertEqual(Blankable.settings.string, '')

        # And they can be modified in-place
        Unpopulated.settings.boolean = False
        Unpopulated.settings.integer = 42
        Unpopulated.settings.string = 'Caturday'
        Unpopulated.settings.date = datetime.date(1939, 9, 1)
        Unpopulated.settings.time = '03:47:00'
        Unpopulated.settings.datetime = datetime.datetime(1939, 9, 1, 3, 47, 0)
        # Test correct stripping while we're at it.
        Unpopulated.settings.list_semi_colon = 'ee@ff.com; gg@hh.com'
        Unpopulated.settings.list_comma = 'ee@ff.com ,gg@hh.com'
        self.assertEqual(Unpopulated.settings.boolean, False)
        self.assertEqual(Unpopulated.settings.integer, 42)
        self.assertEqual(Unpopulated.settings.string, 'Caturday')
        self.assertEqual(Unpopulated.settings.list_semi_colon, ['ee@ff.com', 'gg@hh.com'])
        self.assertEqual(Unpopulated.settings.list_comma, ['ee@ff.com', 'gg@hh.com'])
        self.assertEqual(Unpopulated.settings.date, datetime.date(1939, 9, 1))
        self.assertEqual(Unpopulated.settings.time, datetime.time(3, 47, 0))
        self.assertEqual(Unpopulated.settings.datetime, datetime.datetime(1939, 9, 1, 3, 47, 0))

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

    def assertCorrectSetting(self, value_class, *key):
        from dbsettings import loading
        setting = loading.get_setting(*key)
        self.assertEqual(key, setting.key)  # Check if setting is registered with proper key
        self.assertTrue(isinstance(setting, value_class))

    def test_registration(self):
        "Module and class settings can be mixed up"
        from dbsettings import BooleanValue, IntegerValue
        self.assertCorrectSetting(BooleanValue, 'dbsettings.tests', '', 'clash1')
        self.assertCorrectSetting(IntegerValue, 'dbsettings.tests', 'ModelClash', 'clash1')
        self.assertCorrectSetting(IntegerValue, 'dbsettings.tests', 'ModelClash', 'clash2')
        self.assertCorrectSetting(BooleanValue, 'dbsettings.tests', '', 'clash2')

    def test_forms(self):
        "Forms should display only the appropriate settings"
        from django.contrib.auth.models import User, Permission
        from django.core.urlresolvers import reverse

        site_form = reverse(views.site_settings)

        # Set up a users to test the editor forms
        user = User.objects.create_user('dbsettings', '', 'dbsettings')

        # Check named url
        site_form = reverse('site_settings')

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

        # Check if verbose_name appears
        response = self.client.get(site_form)
        self.assertContains(response, 'Verbose name')

        # Erroneous submissions should be caught by newforms
        data = {
            'dbsettings.tests__Editable__integer': '3.5',
            'dbsettings.tests__Editable__string': '',
            'dbsettings.tests__Editable__list_semi_colon': '',
            'dbsettings.tests__Editable__list_comma': '',
            'dbsettings.tests__Editable__date': '3-77-99',
            'dbsettings.tests__Editable__time': 'abc',
            'dbsettings.tests__Editable__datetime': '',
        }
        response = self.client.post(site_form, data)
        self.assertFormError(response, 'form', 'dbsettings.tests__Editable__integer', 'Enter a whole number.')
        self.assertFormError(response, 'form', 'dbsettings.tests__Editable__string', 'This field is required.')
        self.assertFormError(response, 'form', 'dbsettings.tests__Editable__list_semi_colon', 'This field is required.')
        self.assertFormError(response, 'form', 'dbsettings.tests__Editable__list_comma', 'This field is required.')
        self.assertFormError(response, 'form', 'dbsettings.tests__Editable__date', 'Enter a valid date.')
        self.assertFormError(response, 'form', 'dbsettings.tests__Editable__time', 'Enter a valid time.')
        self.assertFormError(response, 'form', 'dbsettings.tests__Editable__datetime', 'This field is required.')

        # Successful submissions should redirect
        data = {
            'dbsettings.tests__Editable__integer': '4',
            'dbsettings.tests__Editable__string': 'Success!',
            'dbsettings.tests__Editable__list_semi_colon': 'jj@kk.com;ll@mm.com',
            'dbsettings.tests__Editable__list_comma': 'jj@kk.com,ll@mm.com',
            'dbsettings.tests__Editable__date': '2012-06-28',
            'dbsettings.tests__Editable__time': '16:37:45',
            'dbsettings.tests__Editable__datetime': '2012-06-28 16:37:45',
        }
        response = self.client.post(site_form, data)
        self.assertRedirects(response, site_form)

        # And the data submitted should be immediately available in Python
        self.assertEqual(Editable.settings.integer, 4)
        self.assertEqual(Editable.settings.string, 'Success!')
        self.assertEqual(Editable.settings.list_semi_colon, ['jj@kk.com', 'll@mm.com'])
        self.assertEqual(Editable.settings.list_comma, ['jj@kk.com', 'll@mm.com'])
        self.assertEqual(Editable.settings.date, datetime.date(2012, 6, 28))
        self.assertEqual(Editable.settings.time, datetime.time(16, 37, 45))
        self.assertEqual(Editable.settings.datetime, datetime.datetime(2012, 6, 28, 16, 37, 45))

        # Check if module / class settings show properly
        #perm = Permission.objects.get(codename='can_edit__settings')  # module-level settings
        #user.user_permissions.add(perm)

        #response = self.client.get(site_form)
        #self.assertTemplateUsed(response, 'dbsettings/site_settings.html')
        #self.assertEqual(len(response.context[0]['form'].fields), 14)
