import sys
import argparse

import nations.page_parser
import nations.log_analyzer

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument('matches', nargs='*', help='list of HTML match files to pretty-print (if not specified, read the list from stdin)')
args = arg_parser.parse_args()

matches = [match.rstrip('\n\r') for match in (args.matches if args.matches else sys.stdin)]
for match in matches:
    with open(match, 'rb') as page_file:
        log = nations.page_parser.parse_page(page_file.read().decode(encoding='latin_1'))
    print(log)
