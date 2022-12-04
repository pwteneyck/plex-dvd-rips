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
INSTALL_DIR=CONFIG['Plex']['InstallDir']

ENCODE_QUEUE_DIR = f'{INSTALL_DIR}/encode_queue'
TRANSFER_QUEUE_DIR = f'{INSTALL_DIR}/transfer_queue'

def work(manifest_file):
	info = {}
	full_path = f'{ENCODE_QUEUE_DIR}/{manifest_file}'
	with open(full_path, 'r') as manifest:
		print(full_path)
		info = json.load(manifest)
	name = info['name']
	preset = info['preset']
	src = info['src']
	dst = info['dst']
	is_movie = info['is_movie']
	show = info['show']
	season = info['season']
	encode(name, preset, src, dst, is_movie, show, season)
	send_to_transfer_queue(manifest_file)
	os.remove(src)


def encode(name, preset, src, dst, is_movie, show, season):
	dst_dir = dst + '/' + (f'Movies/{name}' if is_movie else f"TV Shows/{show}/Season {str(season).rjust(2,'0')}")
	Path(dst_dir).mkdir(parents=True,exist_ok=True)
	
	# Experimenting with encoder-preset shows significant differences
	# in filesize between GPU (nvenc) and CPU encoding.
	# Anecdotally, people say that CPU encoding yields better
	# quality as well...
	# The Office S04E01-02 - Fun Run (41:16 @ 480p)
	# All encodes done with h.265 codec
	#    encoder settings | encoding time | output size | size reduction
	#    -----------------|---------------|-------------|---------------
	#     (original)      |         0 (s) |     1.83 GB | 0%    
	# nvenc,q=15,s=medium |       135 (s) |     1.54 GB | 16%
	# nvenc,q=20,s=fast   |       136 (s) |      950 MB | 48%
	#  x265,q=15,s=fast   |      1018 (s) |     1.01 GB | 45%
	#  x265,q=20,s=fast   |       787 (s) |      450 MB | 75%
	#  x265,q=20,s=medium |       976 (s) |      507 MB | 72%
	#  x265,q=20,s=slow   |      2374 (s) |      563 MB | 69%
	quality = '20'
	speed = 'fast'
	if preset.startswith('HQ'):
		quality = '15'
		speed = 'slow'

	# all the extra encoder configs are necessary. This behavior isn't
	# documented, but if you leave them out HandBrakeCLI will segfault :(
	#
	# Run via 'nice -n 19' for better backgrounding - '19' will make the 
	# encoding process minimal priority, so other processes won't suffer
	# in case you want to play a video game or something without pausing 
	# the queue
	subprocess.run(['nice', '-n', '19', 'HandBrakeCLI', 
		'--preset', preset, 
		'--encoder', 'x265', 
		'--encoder-level', 'auto', 
		'--encoder-preset', speed, 
		'--encoder-profile', 'auto', 
		'--quality', quality,
		'--two-pass', 
		'--turbo', 
		'-i', src, 
		'-o', f'{dst_dir}/{name}.m4v'])

def send_to_transfer_queue(manifest_file):
	os.rename(f'{ENCODE_QUEUE_DIR}/{manifest_file}', f'{TRANSFER_QUEUE_DIR}/{manifest_file}')

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
	queue = os.listdir(ENCODE_QUEUE_DIR)
	queue.remove('.gitignore')
	if 'pause' in queue:
		sys.stdout.write(f'\rEncoding paused; remove the "pause" file to continue...({spinner(waiting)})')
		waiting = waiting + 1
		time.sleep(1)
	elif queue:
		waiting = 0
		print('')
		work(queue[0])
	else:
		sys.stdout.write(f'\rNo encode work found; polling for new items...({spinner(waiting)})')
		waiting = waiting + 1
		time.sleep(1)
