|

================================
Storing settings in the database
================================

Not all settings belong in ``settings.py``, as it has some particular
limitations:

    * Settings are project-wide. This not only requires apps to clutter up
      ``settings.py``, but also increases the chances of naming conflicts.

    * Settings are constant throughout an instance of Django. They cannot be
      changed without restarting the application.

    * Settings require a programmer in order to be changed. This is true even
      if the setting has no functional impact on anything else.

Many applications find need to overcome these limitations, and ``dbsettings``
provides a convenient way to do so.

The main goal in using this application is to define a set of placeholders that
will be used to represent the settings that are stored in the database. Then,
the settings may be edited at run-time using the provided editor, and all Python
code in your application that uses the setting will receive the updated value.

Requirements
============

+------------------+------------+--------------+
| Dbsettings       | Python     | Django       |
+==================+============+==============+
| ==0.9            | 3.4 - 3.5  | 1.7 - 1.9    |
|                  +------------+--------------+
|                  | 3.2 - 3.3  | 1.7 - 1.8    |
|                  +------------+--------------+
|                  | 2.7        | 1.7 - 1.9    |
+------------------+------------+--------------+
| ==0.8            | 3.2        | 1.5 - 1.8    |
|                  +------------+--------------+
|                  | 2.7        | 1.4 - 1.8    |
|                  +------------+--------------+
|                  | 2.6        | 1.4 - 1.6    |
+------------------+------------+--------------+
| ==0.7            | 3.2        | 1.5 - 1.7    |
|                  +------------+--------------+
|                  | 2.7        | 1.3 - 1.7    |
|                  +------------+--------------+
|                  | 2.6        | 1.3 - 1.6    |
+------------------+------------+--------------+
| ==0.6            | 3.2        |       1.5    |
|                  +------------+--------------+
|                  | 2.6 - 2.7  | 1.3 - 1.5    |
+------------------+------------+--------------+
| <=0.5            | 2.6 - 2.7  | 1.2\* - 1.4  |
+------------------+------------+--------------+

\* Possibly version below 1.2 will work too, but not tested.

Installation
============

To install the ``dbsettings`` package, simply place it anywhere on your
``PYTHONPATH``.

Project settings
----------------

In order to setup database storage, and to let Django know about your use of
``dbsettings``, simply add it to your ``INSTALLED_APPS`` setting, like so::

    INSTALLED_APPS = (
        ...
        'dbsettings',
        ...
    )

If your Django project utilizes ``sites`` framework, all setting would be related
to some site. If ``sites`` are not present, settings won't be connected to any site
(and ``sites`` framework is no longer required since 0.8.1).

You can force to do (not) use ``sites`` via ``DBSETTINGS_USE_SITES = True / False``
configuration variable (put it in project's ``settings.py``).

By default, values stored in database are limited to 255 characters per setting.
You can change this limit with ``DBSETTINGS_VALUE_LENGTH`` configuration variable.
If you change this value after migrations were run, you need to manually alter
the ``dbsettings_setting`` table schema.

URL Configuration
-----------------

In order to edit your settings at run-time, you'll need to configure a URL to
access the provided editors. You'll just need to add a single line, defining
the base URL for the editors, as ``dbsettings`` has its own URLconf to handle
the rest. You may choose any location you like::

    urlpatterns = patterns('',
        ...
        (r'^settings/', include('dbsettings.urls')),
        ...
    )

A note about caching
--------------------

This framework utilizes Django's built-in `cache framework`_, which is used to
minimize how often the database needs to be accessed. During development,
Django's built-in server runs in a single process, so all cache backends will
work just fine.

Most productions environments, including mod_python, FastCGI or WSGI, run multiple
processes, which some backends don't fully support. When using the ``simple``
or ``locmem`` backends, updates to your settings won't be reflected immediately
in all workers, causing your application to ignore the new changes.

No other backends exhibit this behavior, but since ``simple`` is the default,
make sure to specify a proper backend when moving to a production environment.

.. _`cache framework`: http://docs.djangoproject.com/en/dev/topics/cache/

Alternatively you can disable caching of settings by setting
``DBSETTINGS_USE_CACHE = False`` in ``settings.py``. Beware though: every
access of any setting will result in database hit.

Usage
=====

These database-backed settings can be applied to any model in any app, or even
in the app itself. All the tools necessary to do so are available within the
``dbsettings`` module. A single import provides everything you'll need::

    import dbsettings

Defining a group of settings
----------------------------

Settings are be defined in groups that allow them to be referenced together
under a single attribute. Defining a group uses a declarative syntax similar
to that of models, by declaring a new subclass of the ``Group`` class and
populating it with values.

::

    class ImageLimits(dbsettings.Group):
        maximum_width = dbsettings.PositiveIntegerValue()
        maximum_height = dbsettings.PositiveIntegerValue()

You may name your groups anything you like, and they may be defined in any
module. This allows them to be imported from common applications if applicable.

Defining individual settings
----------------------------

Within your groups, you may define any number of individual settings by simply
assigning the value types to appropriate names. The names you assign them to
will be the attribute names you'll use to reference the setting later, so be
sure to choose names accordingly.

For the editor, the default description of each setting will be retrieved from
the attribute name, similar to how the ``verbose_name`` of model fields is
retrieved. Also like model fields, however, an optional argument may be provided
to define a more fitting description. It's recommended to leave the first letter
lower-case, as it will be capitalized as necessary, automatically.

::

    class EmailOptions(dbsettings.Group):
        enabled = dbsettings.BooleanValue('whether to send emails or not')
        sender = dbsettings.StringValue('address to send emails from')
        subject = dbsettings.StringValue(default='SiteMail')

For more descriptive explanation, the ``help_text`` argument can be used. It
will be shown in the editor.

The ``default`` argument is very useful - it specify an initial value of the
setting.

In addition, settings may be supplied with a list of available options, through
the use of of the ``choices`` argument. This works exactly like the ``choices``
argument for model fields, and that of the newforms ``ChoiceField``.

A full list of value types is available later in this document, but the process
and arguments are the same for each.

Assigning settings
------------------

Once your settings are defined and grouped properly, they must be assigned to a
location where they will be referenced later. This is as simple as instantiating
the settings group in the appropriate location. This may be at the module level
or within any standard Django model.

Group instance may receive one optional argument: verbose name of the group.
This name will be displayed in the editor.

::

    email = EmailOptions()

    class Image(models.Model):
        image = models.ImageField(upload_to='/upload/path')
        caption = models.TextField()

        limits = ImageLimits('Dimension settings')

Multiple groups may be assigned to the same module or model, and they can even
be combined into a single group by using standard addition syntax::

    options = EmailOptions() + ImageLimits()

To separate and tag settings nicely in the editor, use verbose names::

    options = EmailOptions('Email') + ImageLimits('Dimesions')

Database setup
--------------

A single model is provided for database storage, and this model must be
installed in your database before you can use the included editors or the
permissions that will be automatically created. This is a simple matter of
running ``manage.py syncdb`` or ``manage.py migrate`` now that your settings
are configured.

This step need only be repeate when settings are added to a new application,
as it will create the appropriate permissions. Once those are in place, new
settings may be added to existing applications with no impact on the database.

Using your settings
===================

Once the above steps are completed, you're ready to make use of database-backed
settings.

Editing settings
----------------

When first defined, your settings will default to ``None`` (or ``False`` in
the case of ``BooleanValue``), so their values must be set using one of the
supplied editors before they can be considered useful (however, if the setting
had the ``default`` argument passed in the constructor, its value is already
useful - equal to the defined default).

The editor will be available at the URL configured earlier.
For example, if you used the prefix of ``'settings/'``, the URL ``/settings/``
will provide an editor of all available settings, while ``/settings/myapp/``
would contain a list of just the settings for ``myapp``.

URL patterns are named: ``'site_settings'`` and ``'app_settings'``, respectively.

The editors are restricted to staff members, and the particular settings that
will be available to users is based on permissions that are set for them. This
means that superusers will automatically be able to edit all settings, while
other staff members will need to have permissions set explicitly.

Accessing settings in Python
----------------------------

Once settings have been assigned to an appropriate location, they may be
referenced as standard Python attributes. The group becomes an attribute of the
location where it was assigned, and the individual values are attributes of the
group.

If any settings are referenced without being set to a particular value, they
will default to ``None`` (or ``False`` in the case of ``BooleanValue``, or
whatever was passed as ``default``). In the
following example, assume that ``EmailOptions`` were just added to the project
and the ``ImageLimits`` were added earlier and already set via editor.

::

    >>> from myproject.myapp import models

    # EmailOptions are not defined
    >>> models.email.enabled
    False
    >>> models.email.sender
    >>> models.email.subject
    'SiteMail'  # Since default was defined

    # ImageLimits are defined
    >>> models.Image.limits.maximum_width
    1024
    >>> models.Image.limits.maximum_height
    768

These settings are accessible from any Python code, making them especially
useful in model methods and views. Each time the attribute is accessed, it will
retrieve the current value, so your code doesn't need to worry about what
happens behind the scenes.

::

    def is_valid(self):
        if self.width > Image.limits.maximum_width:
            return False
        if self.height > Image.limits.maximum_height:
            return False
    return True

As mentioned, views can make use of these settings as well.

::

    from myproject.myapp.models import email

    def submit(request):

        ...
        # Deal with a form submission
        ...

        if email.enabled:
            from django.core.mail import send_mail
        send_mail(email.subject, 'message', email.sender, [request.user.email])

Settings can be not only read, but also written. The admin editor is more
user-friendly, but in case code need to change something::

    from myproject.myapp.models import Image

    def low_disk_space():
        Image.limits.maximum_width = Image.limits.maximum_height = 200

Every write is immediately commited to the database and proper cache key is deleted.

A note about model instances
----------------------------

Since settings aren't related to individual model instances, any settings that
are set on models may only be accessed by the model class itself. Attempting to
access settings on an instance will raise an ``AttributeError``.

Value types
===========

There are several various value types available for database-backed settings.
Select the one most appropriate for each individual setting, but all types use
the same set of arguments.

BooleanValue
------------

Presents a checkbox in the editor, and returns ``True`` or ``False`` in Python.

DurationValue
-------------

Presents a set of inputs suitable for specifying a length of time. This is
represented in Python as a |timedelta|_ object.

.. |timedelta| replace:: ``timedelta``
.. _timedelta: https://docs.python.org/2/library/datetime.html#timedelta-objects

FloatValue
----------

Presents a standard input field, which becomes a ``float`` in Python.

IntegerValue
------------

Presents a standard input field, which becomes an ``int`` in Python.

PercentValue
------------

Similar to ``IntegerValue``, but with a limit requiring that the value be
between 0 and 100. In addition, when accessed in Python, the value will be
divided by 100, so that it is immediately suitable for calculations.

For instance, if a ``myapp.taxes.sales_tax`` was set to 5 in the editor,
the following calculation would be valid::

    >>> 5.00 * myapp.taxes.sales_tax
    0.25

PositiveIntegerValue
--------------------

Similar to ``IntegerValue``, but limited to positive values and 0.

StringValue
-----------

Presents a standard input, accepting any text string up to 255
(or ``DBSETTINGS_VALUE_LENGTH``) characters. In
Python, the value is accessed as a standard string.

DateTimeValue
-------------

Presents a standard input field, which becomes a ``datetime`` in Python.

User input will be parsed according to ``DATETIME_INPUT_FORMATS`` setting.

In code, one can assign to field string or datetime object::

    # These two statements has the same effect
    myapp.Feed.next_feed = '2012-06-01 00:00:00'
    myapp.Feed.next_feed = datetime.datetime(2012, 6, 1, 0, 0, 0)

DateValue
---------

Presents a standard input field, which becomes a ``date`` in Python.

User input will be parsed according to ``DATE_INPUT_FORMATS`` setting.

See ``DateTimeValue`` for the remark about assigning.

TimeValue
---------

Presents a standard input field, which becomes a ``time`` in Python.

User input will be parsed according to ``TIME_INPUT_FORMATS`` setting.

See ``DateTimeValue`` for the remark about assigning.

ImageValue
----------

(requires PIL or Pillow imaging library to work)

Allows to upload image and view its preview.

ImageValue has optional ``upload_to`` keyword, which specify path
(relative to ``MEDIA_ROOT``), where uploaded images will be stored.
If keyword is not present, files will be saved directly under
``MEDIA_ROOT``.

PasswordValue
-------------

Presents a standard password input. Retain old setting value if not changed.


Setting defaults for a distributed application
==============================================

Distributed applications often have need for certain default settings that are
useful for the common case, but which may be changed to suit individual
installations. For such cases, a utility is provided to enable applications to
set any applicable defaults.

Living at ``dbsettings.utils.set_defaults``, this utility is designed to be used
within the app's ``management.py``. This way, when the application is installed
using ``syncdb``/``migrate``, the default settings will also be installed to the database.

The function requires a single positional argument, which is the ``models``
module for the application. Any additional arguments must represent the actual
settings that will be installed. Each argument is a 3-tuple, of the following
format: ``(class_name, setting_name, value)``.

If the value is intended for a module-level setting, simply set ``class_name``
to an empty string. The value for ``setting_name`` should be the name given to
the setting itself, while the name assigned to the group isn't supplied, as it
isn't used for storing the value.

For example, the following code in ``management.py`` would set defaults for
some of the settings provided earlier in this document::

    from django.conf import settings
    from dbsettings.utils import set_defaults
    from myproject.myapp import models as myapp

    set_defaults(myapp,
        ('', 'enabled', True)
        ('', 'sender', settings.ADMINS[0][1]) # Email of the first listed admin
        ('Image', 'maximum_width', 800)
        ('Image', 'maximum_height', 600)
    )

----------

Changelog
=========

**0.9.3** (02/06/2016)
    - Fixed (hopefully for good) problem with ImageValue in Python 3 (thanks rolexCoder)
**0.9.2** (01/05/2016)
    - Fixed bug when saving non-required settings
    - Fixed problem with ImageValue in Python 3 (thanks rolexCoder)
**0.9.1** (10/01/2016)
    - Fixed `Sites` app being optional (thanks rolexCoder)
**0.9.0** (25/12/2015)
    - Added compatibility with Django 1.9 (thanks Alonso)
    - Dropped compatibility with Django 1.4, 1.5, 1.6
**0.8.2** (17/09/2015)
    - Added migrations to distro
    - Add configuration option to change max length of setting values from 255 to whatever
    - Add configuration option to disable caching (thanks nwaxiomatic)
    - Fixed PercentValue rendering (thanks last-partizan)
**0.8.1** (21/06/2015)
    - Made ``django.contrib.sites`` framework dependency optional
    - Added migration for app
**0.8.0** (16/04/2015)
    - Switched to using django.utils.six instead of standalone six.
    - Added compatibility with Django 1.8
    - Dropped compatibility with Django 1.3
**0.7.4** (24/03/2015)
    - Added default values for fields.
    - Fixed Python 3.3 compatibility
    - Added creation of folders with ImageValue
**0.7.3**, **0.7.2**
    pypi problems
**0.7.1** (11/03/2015)
    - Fixed pypi distribution.
**0.7** (06/07/2014)
    - Added PasswordValue
    - Added compatibility with Django 1.6 and 1.7.
**0.6** (16/09/2013)
    - Added compatibility with Django 1.5 and python3, dropped support for Django 1.2.
    - Fixed permissions: added permission for editing non-model (module-level) settings
    - Make PIL/Pillow not required in setup.py
**0.5** (11/10/2012)
    - Fixed error occuring when test are run with ``LANGUAGE_CODE`` different than 'en'
    - Added verbose_name option for Groups
    - Cleaned code
**0.4.1** (02/10/2012)
    - Fixed Image import
**0.4** (30/09/2012)
    - Named urls
    - Added polish translation
**0.3** (04/09/2012)
    Included testrunner in distribution
**0.2** (05/07/2012)
    - Fixed errors appearing when module-level and model-level settings have
      same attribute names
    - Corrected the editor templates admin integration
    - Updated README
**0.1** (29/06/2012)
    Initial PyPI release
