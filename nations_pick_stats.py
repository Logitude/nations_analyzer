import sys
import argparse
import itertools
import functools
import operator
import statistics

import nations.page_parser
import nations.log_analyzer

num_matches = 0
pick_histogram = {}
pick_position_sums = {}
pick_league_points = {}
nation_occurrences = {}
nation_pick_numbers = {}
nation_position_sums = {}
nation_pairings = {}

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument('matches', nargs='*', help='list of HTML match files to analyze (if not specified, read the list from stdin)')
args = arg_parser.parse_args()

matches = [match.rstrip('\n\r') for match in (args.matches if args.matches else sys.stdin)]
for match in matches:
    with open(match, 'rb') as page_file:
        log = nations.page_parser.parse_page(page_file.read().decode(encoding='latin_1'))
    analyzer = nations.log_analyzer.Analyzer(log)
    if analyzer.is_complete():
        num_matches += 1
        match_id = analyzer.match_id()
        players = analyzer.players()
        scores = analyzer.scores()
        def player_scores_sort_key(player_score):
            (player, score) = player_score
            return (-score, players.index(player))
        player_scores = sorted(scores.items(), key=player_scores_sort_key)
        winner = player_scores[0][0]
        nation_picks = analyzer.nation_picks()
        nation_positions = {}
        for (i, (player, nation)) in enumerate(nation_picks):
            pick_number = i + 1
            if player == winner:
                try:
                    pick_histogram[pick_number] += 1
                except KeyError:
                    pick_histogram[pick_number] = 1
            position = [j for (j, (p, score)) in enumerate(player_scores) if p == player][0] + 1
            nation_positions[nation] = position
            try:
                pick_position_sums[pick_number] += position
            except KeyError:
                pick_position_sums[pick_number] = position
            league_points = (6, 3, 1, 0)[position - 1]
            try:
                pick_league_points[pick_number] += league_points
            except KeyError:
                pick_league_points[pick_number] = league_points
            try:
                nation_occurrences[nation] += 1
            except KeyError:
                nation_occurrences[nation] = 1
            try:
                nation_pick_numbers[nation] += pick_number
            except KeyError:
                nation_pick_numbers[nation] = pick_number
            try:
                nation_position_sums[nation] += position
            except KeyError:
                nation_position_sums[nation] = position
        for (nation_a, nation_b) in itertools.combinations(nation_positions.keys(), 2):
            position_a = nation_positions[nation_a]
            position_b = nation_positions[nation_b]
            if position_a < position_b:
                nation_pair = (nation_a, nation_b)
            else:
                nation_pair = (nation_b, nation_a)
            try:
                nation_pairings[nation_pair] += 1
            except KeyError:
                nation_pairings[nation_pair] = 1

def nation_averages_sort_key(nation_average):
    (nation, position_average) = nation_average
    return (position_average, -nation_occurrences[nation], nation)

nation_pick_averages = {}
nation_position_averages = {}
for (nation, position_sum) in nation_position_sums.items():
    nation_pick_averages[nation] = nation_pick_numbers[nation] / nation_occurrences[nation]
    nation_position_averages[nation] = position_sum / nation_occurrences[nation]
nation_position_averages = sorted(nation_position_averages.items(), key=nation_averages_sort_key)

nation_list = list(nation_occurrences.keys())
nation_scores = {nation: 1.0 for nation in nation_list}
for i in range(100):
    nation_ratios = {nation: [] for nation in nation_list}
    for (nation_a, nation_b) in itertools.combinations(nation_list, 2):
        nation_a_wins = nation_pairings.get((nation_a, nation_b), 0)
        nation_b_wins = nation_pairings.get((nation_b, nation_a), 0)
        nation_a_score = nation_scores[nation_a]
        nation_b_score = nation_scores[nation_b]
        nation_a_probability = max(0.1, min(0.9, 0.5 + nation_a_score - nation_b_score))
        nation_b_probability = max(0.1, min(0.9, 0.5 + nation_b_score - nation_a_score))
        nation_a_part = (1.05 + nation_b_probability / 5) ** nation_a_wins
        nation_b_part = (1.05 + nation_a_probability / 5) ** nation_b_wins
        nation_a_ratio = nation_a_part / nation_b_part
        nation_b_ratio = nation_b_part / nation_a_part
        nation_ratios[nation_a].append(nation_a_ratio)
        nation_ratios[nation_b].append(nation_b_ratio)
    for nation in nation_list:
        ratio_product = functools.reduce(operator.mul, nation_ratios[nation], 1.0)
        nation_scores[nation] = ratio_product ** (1.0 / len(nation_ratios[nation]))

if num_matches == 0:
    print('No complete matches!')
else:
    print('\n'.join(f'{pick_number}: {100*count/num_matches:.0f}%' for (pick_number, count) in sorted(pick_histogram.items())))
    print()
    print('\n'.join(f'{pick_number}: {position_sum/num_matches:.2f}' for (pick_number, position_sum) in sorted(pick_position_sums.items())))
    print()
    print('\n'.join(f'{pick_number}: {league_points/num_matches:.2f}' for (pick_number, league_points) in sorted(pick_league_points.items())))
    print()
    for (nation, position_average) in nation_position_averages:
        occurrences = nation_occurrences[nation]
        nation_colon = nation + ':'
        print(f'[{occurrences:2}] {nation_colon:<10} {position_average:.2f} ({nation_pick_averages[nation]:.2f})')
    print()
    for (score, nation) in sorted(((score, nation) for (nation, score) in nation_scores.items()), reverse=True):
        nation_colon = nation + ':'
        print(f'{nation_colon:<10} {score-1.0: .3f}')
