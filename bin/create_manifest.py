import argparse
import configparser
import json
import os
import subprocess

from pathlib import Path

CONFIG = configparser.ConfigParser()
CONFIG.read(f'{os.path.realpath(os.path.dirname(__file__))}/config.ini')
INSTALL_DIR=CONFIG['Plex']['InstallDir']

parser = argparse.ArgumentParser()
parser.add_argument('-t', '--title')
parser.add_argument('-n', '--showname')
parser.add_argument('-s', '--season', default=None)
parser.add_argument('-hq', '--high-quality', action='store_true')
parser.add_argument('-d', '--destination', default='encode_queue')
parser.add_argument('file')
args = parser.parse_args()

QUEUE_DIR = f'{INSTALL_DIR}/{args.destination}'

print(args.file)
vres = int(subprocess.run(['shell_scripts/get_vres.sh', args.file], capture_output=True).stdout.decode())
preset = f'Fast {vres}p30'

if args.high_quality:
	preset = f'HQ {vres}p30 Surround'

info = {}
info['name'] = args.title
info['preset'] = preset
info['src'] = os.path.abspath(args.file)
info['dst'] = QUEUE_DIR
info['is_movie'] = (args.season is None)
info['season'] = args.season
info['show'] = args.showname

full_file_uri = f'{QUEUE_DIR}/{args.title}.manifest'
if not os.path.exists(info['src']):
	raise BaseException(f'src not found: {title_info}')
if os.path.exists(full_file_uri):
	print(f'Found expected manifest already in {args.destination} queue; skipping (will not re-queue)')
else:
	with open(full_file_uri, 'w') as file:
		file.write(json.dumps(info))