import argparse
from os import listdir
from os import replace
from os.path import isfile, join
import sys

def get_files(args):
	return [join(args.directory, f) for f in listdir(args.directory) if isfile(join(args.directory, f))]

def get_titles(args):
	with open(args.titles, 'r') as titles_file:
		return titles_file.readlines()

parser = argparse.ArgumentParser()
parser.add_argument('directory', type=str)
parser.add_argument('-s', '--start', required=True, type=int)
parser.add_argument('-o', '--output', required=True, type=str)
parser.add_argument('-t', '--titles', required=True, type=str)
parser.add_argument('--dryrun', required=False, action='store_true')
args = parser.parse_args()

files = get_files(args)
titles = get_titles(args)

for file in files:
	title = titles[args.start-1].strip()
	full_title_path = args.output + '\\' + title + '.mkv'
	print(file + ' --> ' + full_title_path)
	if not args.dryrun:
		replace(file, full_title_path)
	args.start += 1
