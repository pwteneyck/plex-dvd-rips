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


def full_name_from_json(data):
    date = data.get('release_date', '')
    return f"{data['original_title']} ({date[:date.find('-')]})"


def search(keywords):
	print(f'Searching TMDB for {keywords}')
	resp = requests.get(f'{TMDB_API_URL}/search/movie', headers=TMDB_AUTH_HEADERS, params={'query': keywords, 'language': 'en-US'})
	results = resp.json()['results']
	all_names = list(map(full_name_from_json, results))
	return all_names