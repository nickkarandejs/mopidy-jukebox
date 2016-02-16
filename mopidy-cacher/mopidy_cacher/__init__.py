from __future__ import unicode_literals

import logging
import os

from mopidy import config, ext


__version__ = '0.1.0'

# TODO: If you need to log, use loggers named after the current Python module
logger = logging.getLogger(__name__)


class Extension(ext.Extension):
    dist_name = 'Mopidy-Cacher'
    ext_name = 'cacher'
    version = __version__

    def get_default_config(self):
        conf_file = os.path.join(os.path.dirname(__file__), 'ext.conf')
        return config.read(conf_file)

    def get_config_schema(self):
        schema = super(Extension, self).get_config_schema()
        schema['caches'] = config.String()
        return schema

    def get_command(self):
        from .cache import CacherCommand
        return CacherCommand()

    def setup(self, registry):
        pass
        #from .backend import CacherBackend
        #registry.add('backend', CacherBackend)

        # TODO: Edit or remove entirely
        #registry.add('http:static', {
        #    'name': self.ext_name,
        #    'path': os.path.join(os.path.dirname(__file__), 'static'),
        #})
