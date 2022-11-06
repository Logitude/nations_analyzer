import sys
import argparse
import datetime

import nations.page_parser
import nations.log_analyzer

turns_bucket_size = 10
time_bucket_size = 7
num_incomplete = 0
match_buckets = {}

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument('matches', nargs='*', help='list of HTML match files to analyze (if not specified, read the list from stdin)')
args = arg_parser.parse_args()

matches = [match.rstrip('\n\r') for match in (args.matches if args.matches else sys.stdin)]
for match in matches:
    with open(match, 'rb') as page_file:
        log = nations.page_parser.parse_page(page_file.read().decode(encoding='latin_1'))
    analyzer = nations.log_analyzer.Analyzer(log)
    if analyzer.is_complete():
        match_id = analyzer.match_id()
        num_non_duplicate_turns = analyzer.num_non_duplicate_turns()
        turns_bucket = num_non_duplicate_turns // turns_bucket_size
        match_time = analyzer.end_time() - analyzer.start_time()
        time_bucket = match_time // datetime.timedelta(days=time_bucket_size)
        match_buckets[match_id] = {'turns': turns_bucket, 'time': time_bucket}
    elif analyzer.start_time() is not None:
        num_incomplete += 1

min_turns_bucket = min(buckets['turns'] for buckets in match_buckets.values())
max_turns_bucket = max(buckets['turns'] for buckets in match_buckets.values())
min_time_bucket = min(buckets['time'] for buckets in match_buckets.values())
max_time_bucket = max(buckets['time'] for buckets in match_buckets.values())

turns_histogram = {}
time_histogram = {}
bucket_matrix = [
    [0 for time_bucket in range(min_time_bucket, max_time_bucket + 1)]
        for turns_bucket in range(min_turns_bucket, max_turns_bucket + 1)
]

for buckets in match_buckets.values():
    turns_bucket = buckets['turns']
    time_bucket = buckets['time']
    try:
        turns_histogram[turns_bucket] += 1
    except KeyError:
        turns_histogram[turns_bucket] = 1
    try:
        time_histogram[time_bucket] += 1
    except KeyError:
        time_histogram[time_bucket] = 1
    turns_bucket_index = turns_bucket - min_turns_bucket
    time_bucket_index = time_bucket - min_time_bucket
    bucket_matrix[turns_bucket_index][time_bucket_index] += 1

for turns_bucket in range(min_turns_bucket, max_turns_bucket + 1):
    try:
        count = turns_histogram[turns_bucket]
    except KeyError:
        count = 0
    print(f'{turns_bucket*turns_bucket_size:03}-{(turns_bucket+1)*turns_bucket_size-1:03}: {count:3}')
print(f'Incomplete: {num_incomplete}')

print()
for time_bucket in range(min_time_bucket, max_time_bucket + 1):
    try:
        count = time_histogram[time_bucket]
    except KeyError:
        count = 0
    print(f'{time_bucket:02}-{time_bucket+1:02}: {count:3}')
print(f'Incomplete: {num_incomplete}')

print()
print('    ', end='')
for time_bucket in range(min_time_bucket, max_time_bucket + 1):
    print(f' {time_bucket:2}', end='')
print()
for (turns_bucket_index, time_bucket_vector) in enumerate(bucket_matrix):
    turns_bucket = (min_turns_bucket + turns_bucket_index) * turns_bucket_size
    print(f'{turns_bucket}:', end='')
    for (time_bucket_index, count) in enumerate(time_bucket_vector):
        if count == 0:
            count = ''
        print(f' {count:2}', end='')
    print()
