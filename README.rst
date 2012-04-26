(ImageValue included)

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
the settings may edited at run-time using the provided editor, and all Python
code in your application that uses the setting will receive the updated value.

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

Most productions environments, including mod_python and FastCGI, run multiple
processes, which some backends don't fully support. When using the ``simple``
or ``locmem`` backends, updates to your settings won't be reflected immediately,
causing your application to ignore the new changes.

No other backends exhibit this behavior, but since ``simple`` is the default,
make sure to specify a proper backend when moving to a production environment.

.. _`cache framework`: http://www.djangoproject.com/documentation/cache/

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
        subject = dbsettings.StringValue()

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

::

    email = EmailOptions()

    class Image(models.Model):
        image = models.ImageField(upload_to='/upload/path')
        caption = models.TextField()

        limits = ImageLimits()

Multiple groups may be assigned to the same module or model, and they can even
be combined into a single group by using standard addition syntax::

    options = EmailOptions() + ImageLimits()

Database setup
--------------

A single model is provided for database storage, and this model must be
installed in your database before you can use the included editors or the
permissions that will be automatically created. This is a simple matter of
running ``manage.py syncdb`` now that your settings are configured.

This step need only be repeate when settings are added to a new application,
as it will create the appropriate permissions. Once those are in place, new
settings may be added to existing applications with no impact on the database.

Using your settings
===================

Once the above steps are completed, you're ready to make use of database-backed
settings.

Editing settings
----------------

When first defined, your settings will default to ``None`` (or ``False``), so
their values must be set using one of the supplied editors before they can be
considered useful. The editor will be available at the URL configured earlier.
For example, if you used the prefix of ``'settings/'``, the URL ``/settings/``
will provide an editor of all available settings, while ``/settings/myapp/``
would contain a list of just the settings for ``myapp``.

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
will default to ``None`` (or ``False`` in the case of ``BooleanValue``). In the
following example, assume that ``EmailOptions``were added to the project after
the ``ImageLimits`` were already defined.

::

    >>> from myproject.myapp import models

    # EmailOptions are not defined
    >>> models.options.enabled
    False
    >>> models.email.sender
    >>> models.email.subject

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
represented in Python as a ``timedelta_`` object.

.. _timedelta: http://docs.python.org/lib/datetime-timedelta.html

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

For instance, if a ``myapp.taxes.sales_tax`` is set to 5, the following
calculation would be valid::

    >>> 5.00 * myapp.taxes.sales_tax
    0.25

PositiveIntegerValue
--------------------

Similar to ``IntegerValue``, but limited to positive values and 0.

StringValue
-----------

Presents a standard input, accepting any text string up to 255 characters. In
Python, the value is accessed as a standard string.

Setting defaults for a distributed application
==============================================

Distributed applications often have need for certain default settings that are
useful for the common case, but which may be changed to suit individual
installations. For such cases, a utility is provided to enable applications to
set any applicable defaults.

Living at ``dbsettings.utils.set_defaults``, this utility is designed to be used
within the app's ``management.py``. This way, when the application is installed
using ``syncdb``, the default settings will also be installed to the database.

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
