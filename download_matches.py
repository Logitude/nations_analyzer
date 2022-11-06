import sys
import argparse
import re
import urllib.request

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument('urls', nargs='?', help='file containing a list of URLs to download (default=stdin)')
args = arg_parser.parse_args()

if args.urls is None:
    urls_file = sys.stdin
else:
    urls_file = open(args.urls)
for line in urls_file:
    match_url = line.rstrip('\n\r')
    m = re.search(r'\bg_id=(\d+)\b', match_url)
    if m is None:
        continue
    match_id = m.group(1)
    open(f'{match_id}.html', 'wb').write(urllib.request.urlopen(match_url).read())
