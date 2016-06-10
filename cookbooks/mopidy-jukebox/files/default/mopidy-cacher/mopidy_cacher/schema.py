from __future__ import unicode_literals
import logging
import os
import sqlite3
import time

schema_version = 1

logger = logging.getLogger(__name__)

class Connection(sqlite3.Connection):
    def dict_factory(self, cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    def __init__(self, *args, **kwargs):
        sqlite3.Connection.__init__(self, *args, **kwargs)
        self.execute('PRAGMA foreign_keys = ON')
        self.row_factory = self.dict_factory

def load(c):
    sql_dir = os.path.join(os.path.dirname(__file__), b'sql')
    user_version = c.execute('PRAGMA user_version').fetchone()['user_version']
    while user_version != schema_version:
        if user_version:
            raise Exception, "Don't know how to upgrade from %s to %s"%(user_version, schema_version)
        else:
            logger.info('Creating SQLite database schema v%s', schema_version)
            filename = 'schema.sql'
        with open(os.path.join(sql_dir, filename)) as fh:
            c.executescript(fh.read())
        new_version = c.execute('PRAGMA user_version').fetchone()['user_version']
        assert new_version != user_version
        user_version = new_version
    return user_version

def source(c, url):
    return c.execute('SELECT * FROM sources where url = ?', (url,)).fetchall()[0]

def delete(c, url):
    c.execute('DELETE FROM sources where url = ?', (url,))

def sources(c):
    return c.execute('SELECT * FROM sources order by last_check_time asc').fetchall()

def createSource(c, url):
    c.execute('insert into sources values (?, 0, 0)', (url,))

def update_source(c, url, status):
    c.execute('update sources set successful = ?, last_check_time = ? where url = ?', (status, time.time(), url))
