# create manifest file

import argparse
import configparser
import json

CONFIG = configparser.ConfigParser()
CONFIG.read(f'{os.path.realpath(os.path.dirname(__file__))}/config.ini')
INSTALL_DIR=CONFIG['Plex']['InstallDir']

QUEUE_DIR=f'{INSTALL_DIR}/transfer_queue'
ENCODE_OUTPUT_DIR=f'{INSTALL_DIR}/encoded'

parser = argparse.ArgumentParser()
parser.add_argument('type', choices=['movie', 'show'])
parser.add_argument('-t', '--title')
parser.add_argument('n', '--showname')
parser.add_argument('-s', '--season')
parser.add_argument('location', type=str)
args = parser.parse_args()

info = {}
info['name'] = args.title
info['is_movie'] = (args.type == 'movie')
info['show'] = args.showname
info['season'] = args.season
info['show'] = args.showname
info['dst'] = f'{ENCODE_OUTPUT_DIR}'

full_file_uri = f'{QUEUE_DIR}/{title_info.final_name}.manifest'
if os.path.exists(full_file_uri):
	print('Found expected manifest already in encode queue; skipping (will not re-queue)')
else:
	with open(f'{QUEUE_DIR}/{title_info.final_name}.manifest', 'w') as file:
		file.write(json.dumps(info))