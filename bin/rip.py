#! /usr/bin/python

import argparse
import configparser
import fcntl
import json
import os
import re
import subprocess
import sys
import time

from dataclasses import replace
from pathlib import Path
from subprocess import CalledProcessError

import episode_names
import movie_name
from title_info import TitleInfo

CONFIG = configparser.ConfigParser()
CONFIG.read(f'{os.path.realpath(os.path.dirname(__file__))}/config.ini')
INSTALL_DIR=CONFIG['Plex']['InstallDir']

RAW_RIPS_DIR = f'{INSTALL_DIR}/raw'
ENCODE_OUTPUT_DIR = f'{INSTALL_DIR}/encoded'
QUEUE_DIR = f'{INSTALL_DIR}/encode_queue'
SHELL_SCRIPTS_DIR = 'shell_scripts'

DRIVE_WAIT_RETRY_COUNT = 7
DRIVE_WAIT_RETRY_TIME_SEC = 3

# https://mroach.com/2020/09/checking-cd-rom-status-with-bash/#ioctl
def wait_for_drive_ready(drive_num):
	sys.stdout.write(f'Waiting for ready status from /dev/sr{drive_num}.')
	drive = os.open(f'/dev/sr{drive_num}', os.O_NONBLOCK)
	for attempt in range(DRIVE_WAIT_RETRY_COUNT):
		drive_status = fcntl.ioctl(drive, 0x5326)
		if drive_status == 4:
			os.close(drive)
			print('') # "Waiting..." prompt doesn't end in a newline
			return
		elif drive_status == 1:
			print(f'\n')
		else:
			sys.stdout.write(f'\rWaiting for ready status from /dev/sr{drive_num}.{"."*attempt}')
			time.sleep(DRIVE_WAIT_RETRY_TIME_SEC)
	os.close(drive)
	print(f'\nTimed out waiting for CDS_DISC_OK status from /dev/sr{drive_num}')
	sys.exit(1)


def parse_all_disk_info(drive_num):
	print(f'Reading /dev/sr{drive_num}')
	output = subprocess.run([f'{SHELL_SCRIPTS_DIR}/disk_info.sh', drive_num], capture_output=True).stdout.decode()
	disk_id = ''
	disk_name = ''
	current_title = '0'
	current_length = ''
	current_size = ''
	current_name = ''
	current_v_res = ''
	current_final_name = ''
	titles = []

	for line in output.split('\n'):
		if line.startswith('disk:'):
			disk_id = line.split(':')[1]
		elif line.startswith('CINFO:2,'):
			disk_name = line.split('"')[1]
		elif line.startswith('TINFO'):
			parsed_title = line.split(':')[1].split(',')[0]
			if parsed_title != current_title:
				titles.append(TitleInfo(
					is_movie=False,
					disk=disk_id,
					disk_name=disk_name,
					title_name=current_name,
					title=current_title,
					length=current_length,
					size=current_size,
					final_name=current_final_name,
					v_resolution=int(current_v_res)))
			elif line.startswith(f'TINFO:{current_title},2,'):
				current_final_name = line.split('"')[1]
			elif line.startswith(f'TINFO:{current_title},9'):
				current_length = line.split('"')[1]
			elif line.startswith(f'TINFO:{current_title},10'):
				current_size = line.split('"')[1]
			elif line.startswith(f'TINFO:{current_title},27'):
				current_name = line.split('"')[1]
			current_title = parsed_title
		elif line.startswith(f'SINFO:{current_title},0,19'):
			current_v_res = line.split('"')[1].split('x')[1]

	titles.append(TitleInfo(
					is_movie=False,
					disk=disk_id,
					disk_name=disk_name,
					title_name=current_name,
					title=current_title,
					length=current_length,
					size=current_size,
					final_name=current_final_name,
					v_resolution=int(current_v_res)))
	return titles

def parse_range(rng):
	parts = rng.split('-')
	if 1 > len(parts) > 2:
		raise ValueError(f"Bad range: '{rng}'")
	parts = [int(i.strip()) for i in parts]
	start = parts[0]
	end = start if len(parts) == 1 else parts[1]
	if start > end:
		end, start = start, end
	return range(start, end + 1)

def select_titles(titles):
	print(f'Found {len(titles)} titles on this disk. Select the ones you want to rip by entering a comma-separated list of title IDs')
	print("i.e. '1,2,3,5' to select titles 1, 2, 3, and 5")
	print("or   '1-3,5' to select the same")
	print('Enter "all" to rip all titles')
	for index, title in enumerate(titles):
		print(f'[{index}] {title.title_name} ; {title.length} ; {title.size}')
	response = input('Titles to rip :: ')

	if response == 'all':
		return titles
	else:
		kept_titles = []
		for rng in response.split(','):
			for index in parse_range(rng):
				kept_titles.append(titles[index])
		return kept_titles

def fill_episode_names(titles):
	properly_named_title_infos = []
	names = episode_names.get_season_titles(args.showname, args.season, args.showid)[args.offset:args.offset+len(titles)]
	if args.showname == None:
		args.showname = episode_names.get_show_name(args.showid)
	if args.reverse:
		names.reverse()
	for index, title in enumerate(titles):
		properly_named_title_infos.append(replace(titles[index], final_name=f'{names[index].replace("/", "-")}'))

	print('Using the following titles. If these aren\'t correct, something needs to be fixed :)')
	for t in properly_named_title_infos:
		print('\t' + t.final_name)
	input("Press Enter to continue")
	return properly_named_title_infos


def parse_title_info(drive_num):
	titles = parse_all_disk_info(drive_num)
	longest_title = titles[0]

	for title in titles:
		if title.length > longest_title.length:
			longest_title = title

	search_term = longest_title.final_name if len(longest_title.final_name)>0 else longest_title.disk_name
	keywords = re.split(r'[ \._]', search_term)
	all_keywords = ' '.join(keywords)
	search_term.replace('_', ' ')
	return replace(longest_title, final_name=validate_title(all_keywords), is_movie=True)

def validate_title(title_name):
	# search_term = title_name.replace(' ', '+')
	results = movie_name.search(title_name)
	print(f'Found matches for {title_name}::')
	for index, title in enumerate(results):
		print(f'\t[{index}] :: {title}')

	choice = input('Enter correct title, enter a new one, or enter "skip" to skip (default=0): ') or '0'
	if choice == 'skip':
		print(f'skipping {vid_file}...')
		return None
	elif choice.isnumeric():
		title_to_use = results[int(choice)]
	else:
		title_to_use = choice
	return title_to_use

def rip_title_to_dir(title_info, directory):
	Path(directory).mkdir(exist_ok=True)
	if os.path.exists(f'{directory}/{title_info.title_name}'):
		print('Found expected file already in output directory; skipping rip')
	else:
		subprocess.run([
			'makemkvcon', 'mkv', '--progress=-stdout',
			f'disc:{title_info.disk}', str(title_info.title), directory],
			check=True)

def send_to_encode_queue(title_info, src):
	info = {}
	info['name'] = title_info.final_name
	info['preset'] = title_info.preset(args.highquality)
	info['src'] = f'{src}/{title_info.title_name}';
	info['dst'] = f'{ENCODE_OUTPUT_DIR}'
	info['is_movie'] = title_info.is_movie
	info['season'] = args.season
	info['show'] = args.showname
	print(info)
	full_file_uri = f'{QUEUE_DIR}/{title_info.final_name}.manifest'
	if not os.path.exists(info['src']):
		raise BaseException(f'Failed to rip: {title_info}')
	if os.path.exists(full_file_uri):
		print('Found expected manifest already in encode queue; skipping (will not re-queue)')
	else:
		with open(f'{QUEUE_DIR}/{title_info.final_name}.manifest', 'w') as file:
			file.write(json.dumps(info))


parser = argparse.ArgumentParser()
parser.add_argument('type', choices=['movie', 'show'])
parser.add_argument(
	'-d', '--drive', 
	help='drive number to rip from - e.g. "/dev/sr0" would be drive 0')
parser.add_argument(
	'-hq', '--highquality', 
	action='store_true', 
	help='prioritize encoding compression/quality over speed')
parser.add_argument(
	'-n', '--showname',
	help=(
		'(show only) - the name of the show - used to search TMDB for '
		'episode names'))
parser.add_argument(
	'-id', '--showid',
	help=(
		'(show only) - shownames can be ambiguous or overloaded - instead, this argument '
		'provides the unambiguous show ID used by tmdb.com to identify a '
		'specific show, e.g. Parks and Recreation is ID 8592: '
		'https://www.themoviedb.org/tv/8592-parks-and-recreation'))
parser.add_argument(
	'-s', '--season',
	help= 'the season of the show, one-indexed like you\'d expect')
parser.add_argument(
	'-o', '--offset', 
	type=int, 
	default=-1,
	help=(
		'(show only) - the zero-indexed offset of the first episode on the disk - e.g. if '
		'the first episode on a disk is episode 5, the correct offset for that '
		'disk is 4. Maybe the easier way to think about this is that "offset" '
		'should correspond to the last episode number on the previous disk.'))
parser.add_argument(
	'--reverse', 
	action='store_true', 
	help=(
		'some DVDs store episodes in reverse order - use this flag to '
		'correctly apply episode names in reverse order'))
parser.add_argument(
	'--notify', 
	action='store_true',
	help=(
		'adds a post-complete action to the rip process - use this flag '
		'to have the rip process execute the "notify.sh" script under '
		'install_dir/bin/shell_scripts.'))
args = parser.parse_args()

titles = []

subprocess.run(['eject', '-t', f'/dev/sr{args.drive}'])
wait_for_drive_ready(args.drive)

if args.type == 'show':
	if not (args.season and args.offset>=0 and (args.showname or args.showid)):
		print('Missing required args for TV show: showname, season, and offset are all required')
		sys.exit(1)
	titles = parse_all_disk_info(args.drive)
	titles = select_titles(titles)
	titles = fill_episode_names(titles)
else:
	titles.append(parse_title_info(args.drive))

errors = []
for title_info in titles:
	print(f'Ripping: {title_info.title_name} ; {title_info.final_name}')
	title_raw_dir = f'{RAW_RIPS_DIR}/{title_info.disk_name}-{args.offset}'
	title_encoded_dir = f'{ENCODE_OUTPUT_DIR}/{title_info.disk_name}-{args.offset}'
	try:
		rip_title_to_dir(title_info, title_raw_dir)
		send_to_encode_queue(title_info, title_raw_dir)
	except BaseException as err:
		errors.append((title_info, err))

if len(errors):
	print('Failed to rip the following:')
	for error in errors:
		print(f'{error[0].title_name} - {error[0].final_name}\t{error[1]}')
subprocess.run(['eject', f'/dev/sr{args.drive}'])
if args.notify:
	subprocess.run([f'{SHELL_SCRIPTS_DIR}/notify.sh', f'"Finished rip at drive {args.drive}"'])
print()