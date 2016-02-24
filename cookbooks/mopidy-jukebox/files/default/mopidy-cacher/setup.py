from __future__ import unicode_literals

import re

from setuptools import find_packages, setup
import distutils.command.install_lib
import os

def get_version(filename):
    with open(filename) as fh:
        metadata = dict(re.findall("__([a-z]+)__ = '([^']+)'", fh.read()))
        return metadata['version']

class conf_install_lib(distutils.command.install_lib.install_lib):
  def run(self):
    distutils.command.install_lib.install_lib.run(self)
    for fn in self.get_outputs():
      if fn.endswith("ext.conf"):
        mode = 0644
        distutils.log.info("changing mode of %s to %o", fn, mode)
        os.chmod(fn, mode)

setup(
    name='Mopidy-Cacher',
    version=get_version('mopidy_cacher/__init__.py'),
    url='https://github.com/palfrey/mopidy-cacher',
    license='GNU Affero General Public License, Version 3',
    author='Tom Parker',
    author_email='palfrey@tevp.net',
    description='Mopidy extension for caching',
    long_description=open('README.rst').read(),
    packages=find_packages(exclude=['tests', 'tests.*']),
    zip_safe=False,
    include_package_data=True,
    install_requires=[
        'setuptools',
        'Mopidy >= 1.0',
        'Pykka >= 1.1',
    ],
    cmdclass={'install_lib': conf_install_lib},
    entry_points={
        'mopidy.ext': [
            'cacher = mopidy_cacher:CacherExtension',
        ],
    },
    classifiers=[
        'Environment :: No Input/Output (Daemon)',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Topic :: Multimedia :: Sound/Audio :: Players',
    ],
)
