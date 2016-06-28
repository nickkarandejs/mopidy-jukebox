from mopidy import commands
import os
import sqlite3
import logging
from . import schema
import subprocess
import time
import fcntl
import time
import urllib

logger = logging.getLogger(__name__)

# From http://stackoverflow.com/a/3626858/320546
def nonBlockRead(output):
    fd = output.fileno()
    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
    try:
        res = output.read()
        print res
        return res
    except:
        return ''

def runcmd(cmdline):
    """
    Execute cmdline.
    Uses the subprocess module and subprocess.PIPE.

    Raises TimeoutInterrupt
    """

    p = subprocess.Popen(
        cmdline,
        bufsize = 0, # default value of 0 (unbuffered) is best
        shell   = False, # not really needed; it's disabled by default
        stdout  = subprocess.PIPE,
        stderr  = subprocess.PIPE
    )

    stdout = ''
    stderr = ''

    while p.poll() is None: # Monitor process
        # p.std* blocks on read(), which messes up the timeout timer.
        # To fix this, we use a nonblocking read()
        stdout += nonBlockRead(p.stdout)
        stderr += nonBlockRead(p.stderr)

    try:
        p.stdout.close()  # If they are not closed the fds will hang around until
        p.stderr.close()  # os.fdlimit is exceeded and cause a nasty exception
        p.terminate()     # Important to close the fds prior to terminating the process!
                          # NOTE: Are there any other "non-freed" resources?
    except:
        pass

    returncode = p.returncode

    return (returncode, stdout, stderr)

def decodeName(name):
    if type(name) == str: # leave unicode ones alone
        try:
            name = name.decode('utf8')
        except:
            name = name.decode('windows-1252')
    return name

class CacherCommand(commands.Command):
    help = 'Refresh local cache of remote files'

    def __init__(self, ext):
        super(CacherCommand, self).__init__()
        self.ext = ext

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
        if self._media_dir == None:
            raise ExtensionError("local/media_dir is not set")
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
            if row["successful"] and diff < config['cacher']['time_since_last']:
                continue
            url = row["url"]
            logger.info("Caching %s" % url)
            cmd = ["wget", "--recursive", "--tries=1", "--timeout=30", "--progress=bar:force", "--level=inf", "--no-parent", "-nc", url, "-P", self._music_store_dir]
            (returncode, stdout, stderr) = runcmd(cmd)
            path = decodeName(os.path.join(self._music_store_dir, urllib.unquote(url.replace("http://",""))))
            print "path", path
            try:
                for root, dirs, files in os.walk(path):
                    for f in files:
                        if f.startswith("index.html"):
                            os.remove(os.path.join(root, f))
            except UnicodeDecodeError:
                print "failed to delete *something*"
            with self._connect() as connection:
                logger.info("Finished caching %s with result %d" % (url, returncode))
                if returncode != 0:
                    try:
                        logger.warning(stdout)
                        logger.warning(stderr)
                    except UnicodeDecodeError:
                        pass
                    schema.update_source(connection, url, False)
                else:
                    schema.update_source(connection, url, True)
        return 0
