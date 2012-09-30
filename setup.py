from setuptools import setup, find_packages

# Dynamically calculate the version based on dbsettings.VERSION
version_tuple = (0, 4, None)
if version_tuple[2] is not None:
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
    packages=find_packages(),
    include_package_data=True,
    license='BSD',
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
)
