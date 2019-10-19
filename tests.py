#!/usr/bin/env python3
from io import StringIO
import logging

# Initialize python logging
logging.basicConfig(level=logging.INFO)

from katana.manager import Manager
from katana.monitor import JsonMonitor, LoggingMonitor

class ConsoleMonitor(JsonMonitor, LoggingMonitor):
	""" A monitor which logs results to the console and also dumps results
	and also provides a results.json file """
	pass

# Default timeout per unit is 10 seconds
TIMEOUT = 10

def run_test(test):

	logger = logging.getLogger(test['name'])

	# Build our monitor
	monitor = ConsoleMonitor()

	# Build the manager
	manager = Manager(monitor = monitor)

	# Set options
	manager['manager']['flag-format'] = test['flag-format']
	manager['manager']['outdir'] = './results/' + test['name']

	logger.info(f'command line: python -m katana -m outdir=./results/{test["name"]},flag-format={test["flag-format"]} {test["target"]}')

	logger.info('starting manager')
	manager.start()

	logger.info('queueing target')
	manager.queue_target(test['target'])

	logger.info(f'waiting for completion (timeout: {TIMEOUT})')
	result = manager.join(timeout=TIMEOUT)

	if result:
		logger.info('processing completed.')
	else:
		logger.info('evaluation timed out or cancelled')

	# Ensure these are cleaned up now
	del manager
	del monitor

# Tests to run
tests = [
	{	'name': 'strings',
		'target': './tests/orchestra',
		'flag-format': 'USCGA{.*?}' },
	{	'name': 'exiftool',
		'target': './tests/woof64.jpg',
		'flag-format': 'USCGA{.*?}' },
	{	'name': 'morescode',
		'target': './tests/tamuctf_morsecode.txt',
		'flag-format': 'gigem{.*?}' },
	{	'name': 'qrcode',
		'target': './tests/qrcode.png',
		'flag-format': 'USCGA{.*?}' },
	{	'name': 'steghide-nopass',
		'target': './tests/rubber_ducky.jpg',
		'flag-format': 'USCGA{.*?}' },
	{	'name': 'steghide',
		'target': './tests/evil_ducky.jpg',
		'flag-format': 'USCGA{.*?}' },
	{	'name': 'snow',
		'target': './tests/let_it_snow.txt',
		'flag-format': 'USCGA{.*?}' },
	{	'name': 'zsteg',
		'target': './tests/pierre.png',
		'flag-format': 'USCGA{.*?}' },
	{	'name': 'robots',
		'target': 'https://johnhammond.org',
		'flag-format': 'FLAG{.*?}' },
	{	'name': 'basic-sqli',
		'target': 'http://2018shell.picoctf.com:53261/',
		'flag-format': 'picoCTF{.*?}' },
	{	'name': 'rot47',
		'target': './tests/welcome_crypto.txt',
		'flag-format': 'sun{.*?}' },
	{	'name': 'brainfuck',
		'target': './tests/brainfuck.txt',
		'flag-format': 'USCGA{.*?}' },
	{	'name': 'pdftotext',
		'target': './tests/blank_paper.pdf',
		'flag-format': 'actf{.*?}' },
	{	'name': 'malbolge',
		'target': './tests/inno.txt',
		'flag-format': 'InnoCTF{.*?}' },
	{	'name': 'differential-rsa',
		'target': './tests/weird_rsa.txt',
		'flag-format': '.*RSA' }
]

for test in tests:
	run_test(test)
