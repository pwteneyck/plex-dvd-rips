import argparse
import configparser
import json
import os
import re
import requests

CONFIG = configparser.ConfigParser()
CONFIG.read(f'{os.path.realpath(os.path.dirname(__file__))}/config.ini')
TMDB_BEARER_TOKEN = CONFIG['Plex']['TMDBToken']
TMDB_AUTH_HEADERS = { 'Authorization': f'Bearer {TMDB_BEARER_TOKEN}'}
TMDB_API_URL = 'https://api.themoviedb.org/3'

def get_show_id(name):
	resp = requests.get(f'{TMDB_API_URL}/search/tv', headers=TMDB_AUTH_HEADERS, params={'query':name, 'language': 'en-US'})
	results = resp.json()['results']
	first_result = results[0]
	return first_result['id']

def get_show_name(id):
	resp = requests.get(f'{TMDB_API_URL}/tv/{id}', headers=TMDB_AUTH_HEADERS)
	return resp.json()['name']

def get_season_titles(name, season, id):
	if id:
		show_id = id
	else:
		show_id = get_show_id(name)
	resp = requests.get(f'{TMDB_API_URL}/tv/{show_id}/season/{season}', headers=TMDB_AUTH_HEADERS, params={'query':name, 'language': 'en-US'})
	episodes = resp.json()['episodes']
	ep_names = []
	for ep_info in episodes:
		title = 'S' + str(season).rjust(2,'0') + 'E'
		ep_num = str(ep_info['episode_number'])
		title += ep_num.rjust(2,'0') + ' - '
		ep_title = ep_info['name']
		title += ep_title
		ep_names.append(title)
	return ep_names


# parser = argparse.ArgumentParser()
# parser.add_argument('wiki_url', type=str)
# parser.add_argument('-s', '--season', required=True, type=int)
# parser.add_argument('-o', '--output', required=False, type=str)
# args = parser.parse_args()

# titles = scrape_wiki(args.wiki_url, args.season)

# if args.output is None:
# 	for t in titles:
# 		print(t)
# else:
# 	with open(args.output, 'w') as file:
# 		for t in titles:
# 			file.write(t + '\n')

		