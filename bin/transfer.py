#! /usr/bin/python

#! /usr/bin/python

import configparser
import json
import os
import subprocess
import sys
import time

from pathlib import Path

CONFIG = configparser.ConfigParser()
CONFIG.read(f'{os.path.realpath(os.path.dirname(__file__))}/config.ini')
PLEX_USER=CONFIG['Plex']['PlexUser']
PLEX_IP=CONFIG['Plex']['DestinationIP']
PLEX_MEDIA_DIR=CONFIG['Plex']['PlexMediaDir']
INSTALL_DIR=CONFIG['Plex']['InstallDir']

ENCODED_OUTPUT_DIR = f'{INSTALL_DIR}/encoded'
TRANSFER_QUEUE_DIR = f'{INSTALL_DIR}/transfer_queue'
DONE_QUEUE = f'{INSTALL_DIR}/done_queue'
SHELL_SCRIPTS_DIR = f'{INSTALL_DIR}/bin/shell_scripts'


TRANSFER_QUEUE_DIR = f'{INSTALL_DIR}/transfer_queue'

def work(manifest_file):
	info = {}
	full_path = f'{TRANSFER_QUEUE_DIR}/{manifest_file}'
	with open(full_path, 'r') as manifest:
		info = json.load(manifest)
	name = info['name']
	preset = info['preset']
	src = info['src']
	dst = info['dst']
	is_movie = info['is_movie']
	show = info['show']
	season = info['season']

	sub_path = (f'Movies/{name}' if is_movie else f"TV Shows/{show}/Season {str(season).rjust(2,'0')}")
	location = f'{dst}/{sub_path}'
	transfer(sub_path, name)
	send_to_done_queue(manifest_file)
	os.remove(f'{location}/{name}.m4v')

def check_available_space(file_to_transfer):
	subprocess.run([
		f'{SHELL_SCRIPTS_DIR}/drive_space.sh', 
		'data2', 
		f'/{ENCODED_OUTPUT_DIR}/{sub_path}/{name}.m4v',
		PLEX_USER,
		PLEX_IP], check=True)

def transfer(sub_path, name):
	subprocess.run([
		f'{SHELL_SCRIPTS_DIR}/transfer.sh', 
		PLEX_USER,
		PLEX_IP,
		PLEX_MEDIA_DIR,
		f'{sub_path}', 
		f'{name}.m4v',
		ENCODED_OUTPUT_DIR])

def send_to_done_queue(manifest_file):
	os.rename(f'{TRANSFER_QUEUE_DIR}/{manifest_file}', f'{DONE_QUEUE}/{manifest_file}')


def spinner(tick):
	spins = [
		'/',
		'-',
		'\\',
		'|'
	]
	return spins[tick%len(spins)]


waiting = 0
while True:
	queue = os.listdir(TRANSFER_QUEUE_DIR)
	queue.remove('.gitignore')
	if 'pause' in queue:
		sys.stdout.write(f'\rTransfers paused; remove the "pause" file to continue...({spinner(waiting)})')
		waiting = waiting + 1
		time.sleep(1)
	elif queue:
		waiting = 0
		print('')
		work(queue[0])
	else:
		sys.stdout.write(f'\rNo transfer work found; polling for new items...({spinner(waiting)})')
		waiting = waiting + 1
		time.sleep(1)
