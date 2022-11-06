import re
import datetime

class Analyzer:
    def __init__(self, log):
        self._log = log.strip()
        self._is_complete = False
        self._match_id = None
        self._players = None
        self._nation_picks = []
        self._start_time = None
        self._end_time = None
        self._scores = None
        self.analyze()

    def analyze(self):
        log_lines = self._log.split('\n')
        if not log_lines:
            return
        self._is_complete = log_lines[-1].startswith('Game finished ')
        prev_player = None
        self._num_turns = 0
        self._num_non_duplicate_turns = 0
        for line in log_lines:
            stripped_line = line.strip()
            if self._players is not None:
                for player in self._players:
                    if stripped_line.startswith(player + ': '):
                        break
                else:
                    player = None
                if player is not None and re.match(r'\S+: [-+][0-9]', stripped_line) is None:
                    self._num_turns += 1
                    if player != prev_player:
                        self._num_non_duplicate_turns += 1
                        prev_player = player
            if self._match_id is None:
                m = re.match(r'Nations Game ID=(\d+)$', stripped_line)
                if m is not None:
                    self._match_id = int(m.group(1))
            if self._players is None:
                m = re.match(r'Players: (.*)$', stripped_line)
                if m is not None:
                    players_string = m.group(1)
                    if self._is_complete:
                        players_and_scores = re.findall(r'(\S+) (\d+) \[VP\] \([+\d]*\)', players_string)
                        self._players = [player for (player, score) in players_and_scores]
                        self._scores = {player: int(score) for (player, score) in players_and_scores}
                    else:
                        self._players = players_string.split()
            if self._players is not None and len(self._nation_picks) != len(self._players):
                m = re.match(r'(\S+): Select board {(.*)}', stripped_line)
                if m is not None:
                    player = m.group(1)
                    nation = m.group(2)
                    self._nation_picks.append((player, nation))
            if self._start_time is None:
                m = re.match(r'Nations Game ID=\d+, started (.*)$', stripped_line)
                if m is not None:
                    self._start_time = datetime.datetime.strptime(m.group(1), '%Y.%m.%d, %H:%M:%S')
        if self._is_complete:
            m = re.match(r'Game finished (.*)$', log_lines[-1])
            if m is not None:
                self._end_time = datetime.datetime.strptime(m.group(1), '%Y.%m.%d, %H:%M:%S')

    def is_complete(self):
        return self._is_complete

    def match_id(self):
        return self._match_id

    def start_time(self):
        return self._start_time

    def end_time(self):
        return self._end_time

    def players(self):
        if not self._players:
            return None
        return tuple(self._players)

    def scores(self):
        if not self._scores:
            return None
        return dict(self._scores)

    def nation_picks(self):
        if not self._nation_picks:
            return None
        return tuple(self._nation_picks)

    def num_turns(self):
        return self._num_turns

    def num_non_duplicate_turns(self):
        return self._num_non_duplicate_turns
