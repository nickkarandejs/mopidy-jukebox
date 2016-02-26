from mopidy import commands
import os
import sqlite3
import logging
from . import schema
import subprocess
import time

logger = logging.getLogger(__name__)

class CacherCommand(commands.Command):
    help = 'Some text that will show up in --help'

    def __init__(self, ext):
        super(CacherCommand, self).__init__()
        self.ext = ext
        self.add_argument('--foo')

    def _connect(self):
        if not self._connection:
            self._connection = sqlite3.connect(
                self._dbpath,
                factory=schema.Connection,
                timeout=100,
                check_same_thread=False,
            )
        return self._connection

    def load(self):
        with self._connect() as connection:
            version = schema.load(connection)
            logger.debug('Using SQLite database schema v%s', version)
            return schema.sources(connection)

    def run(self, args, config):
        try:
            self._media_dir = config['local']['media_dir']
        except KeyError:
            raise ExtensionError('Mopidy-Local not enabled')
        self._music_store_dir = os.path.join(self._media_dir, "cacher")
        self._data_dir = self.ext.get_data_dir(config)
        self._dbpath = os.path.join(self._data_dir, b'cacher.db')
        self._connection = None
        logger.debug("DB path %s" % self._dbpath)
        logger.debug("Media dir %s" % self._media_dir)
        rows = self.load()
        now = time.time()
        for row in rows:
            diff = now - row["last_check_time"]
            logger.debug("Last check status: %r" % row["successful"])
            logger.debug("Time since last update: %d seconds" % diff)
            if row["successful"] and diff < 30 * 60: # half an hour
                continue
            url = row["url"]
            logger.info("Caching %s" % url)
            cmd = ["wget", "--mirror", url, "-P", self._music_store_dir]
            logger.debug(" ".join(cmd))
            popen = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
            (stdoutdata, stderrdata) = popen.communicate()
            with self._connect() as connection:
                logger.info("Finished caching %s with result %d" % (url, popen.returncode))
                if popen.returncode != 0:
                    logger.warning(stderrdata)
                    logger.warning(stdoutdata)
                    schema.update_source(connection, url, False)
                else:
                    schema.update_source(connection, url, True)
        return 0
