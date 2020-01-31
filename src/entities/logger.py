#! /usr/bin/env python3
"""Handles the logging."""

import logging

class MyFilter(logging.Filter):
	def filter(self, record):
		return record.name in ['detsbot', 'jstris', 'database', 'main_model']

class MyLogger(logging.Logger):
	def __init__(self, name):
		logging.Logger.__init__(self, name)
		self.addFilter(MyFilter())

logging.setLoggerClass(MyLogger)
logging.basicConfig(level=logging.DEBUG)
