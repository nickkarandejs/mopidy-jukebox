from __future__ import absolute_import, unicode_literals

import os
import sqlite3

import tornado.web
import tornado.wsgi
from tornado.escape import json_encode

from .schema import *
from .extension import CacherExtension

def get_db_path(config):
	_data_dir = CacherExtension.get_data_dir(config)
	return os.path.join(_data_dir, b'cacher.db')

def connect(db_path):
	return sqlite3.connect(
		db_path,
		factory=Connection,
		timeout=100,
		check_same_thread=False,
	)

class BaseRequestHandler(tornado.web.RequestHandler):
	def initialize(self, core, config):
		self.core = core
		self.config = config
		self.db_path = get_db_path(config)
		self._connection = None

	def _connect(self):
		if not self._connection:
			self._connection = connect(self.db_path)
		return self._connection

	def set_default_headers(self):
		self.set_header('Content-Type', 'application/json')

class RootRequestHandler(BaseRequestHandler):
	def get(self):
		with self._connect() as connection:
			items = sources(connection)
			self.write(json_encode(items))

	def post(self):
		url = self.get_body_argument("url")
		with self._connect() as connection:
			try:
				createSource(connection, url)
			except sqlite3.IntegrityError:
				self.set_status(400, "duplicate URL")
				return
		self.set_status(201)

class ItemRequestHandler(BaseRequestHandler):
	def get(self, url):
		with self._connect() as connection:
			try:
				item = source(connection, url)
				self.write(json_encode(item))
			except IndexError:
				self.set_status(404, "Can't find '%s'" % url)

	def delete(self, url):
		with self._connect() as connection:
			delete(connection, url)
			self.set_status(204)

def cacher_app_factory(config, core):
	db_path = get_db_path(config)
	with connect(db_path) as connection:
		load(connection)

	return [
		('/', RootRequestHandler, {'core': core, 'config': config}),
		('/(.*)', ItemRequestHandler, {'core': core, 'config': config})
	]

if __name__ == "__main__":
	import logging
	logging.basicConfig(level=logging.DEBUG)

	import wsgiref.simple_server

	config = {"core": {"data_dir": "."}}
	core = None

	application = tornado.web.Application(cacher_app_factory(config, core))
	wsgi_app = tornado.wsgi.WSGIAdapter(application)
	server = wsgiref.simple_server.make_server('', 8888, wsgi_app)
	server.serve_forever()
