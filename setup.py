from setuptools import setup

# Dynamically calculate the version based on dbsettings.VERSION
version_tuple = (0, 9, 3)
if version_tuple[2] is not None:
    if type(version_tuple[2]) == int:
        version = "%d.%d.%s" % version_tuple
    else:
        version = "%d.%d_%s" % version_tuple
else:
    version = "%d.%d" % version_tuple[:2]

setup(
    name='django-dbsettings',
    version=version,
    description='Application settings whose values can be updated while a project is up and running.',
    long_description=open('README.rst').read(),
    author='Samuel Cormier-Iijima',
    author_email='sciyoshi@gmail.com',
    maintainer='Jacek Tomaszewski',
    maintainer_email='jacek.tomek@gmail.com',
    url='http://github.com/zlorf/django-dbsettings',
    packages=[
        'dbsettings',
        'dbsettings.migrations',
    ],
    include_package_data=True,
    license='BSD',
    install_requires=(
        'django>=1.7',
    ),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Utilities'
    ],
    zip_safe=False,
)
