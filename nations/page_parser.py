import html.parser
import re

class Parser(html.parser.HTMLParser):
    STATE_OTHER = 0
    STATE_HEADER = 1
    STATE_LOG = 2

    def clean_up_entry(self):
        self.entry = re.sub(r'\s+', r' ', self.entry)
        self.entry = re.sub(r'(\S)\(', r'\1 (', self.entry)
        self.entry = re.sub(r'\)(\S)', r') \1', self.entry)
        self.entry = re.sub(r'\(\s+', r'(', self.entry)
        self.entry = re.sub(r'\s+\)', r')', self.entry)
        self.entry = re.sub(r'\s+:', r':', self.entry)
        self.entry = re.sub(r'\s+,', r',', self.entry)
        self.entry = re.sub(r'(Stability|Military) ([-+]\d+)', r'\2 [\1]', self.entry)
        self.entry = re.sub(r'([-+]\d+) (Stability|Military)', r'\1 [\2]', self.entry)
        self.entry = re.sub(r'(Progress Cards on Game Board) for Round \d+', r'\1', self.entry)
        self.entry = re.sub(r"(?:^|(?<=\W))'([-\w\s]+)(?:(?=[^-'\w\s])|$)", r'\1', self.entry)
        self.entry = re.sub(r"(?:^|(?<=\W))'([^']+(?:s' )[^']*)'(?:(?=\W)|$)", r'{\1}', self.entry)
        self.entry = re.sub(r"(?:^|(?<=\W))'([^']*(?:\S's)[^']*)'(?:(?=\W)|$)", r'{\1}', self.entry)
        self.entry = re.sub(r"(?:^|(?<=\W))'([^']+)'(?:(?=\W)|$)", r'{\1}', self.entry)
        self.entry = re.sub(r'({[^}]*})\s*\[[^]]*\]', r'\1', self.entry)
        m = re.search(r'cards\s+((?:\[[^]]*\]\s*)+)', self.entry)
        if m is not None:
            card_list = m.group(1)
            card_list = card_list.replace('[', '{')
            card_list = card_list.replace(']', '}')
            card_list = card_list.replace('_', ' ')
            card_list = card_list.replace(' s ', "'s ")
            card_list = card_list.replace('s  ', "s' ")
            before_card_list = self.entry[:m.start(0)]
            after_card_list = self.entry[m.end(0):]
            self.entry = before_card_list + card_list + after_card_list
        if self.state == self.STATE_HEADER:
            self.entry = re.sub(r'(Nations Game ID=\d+), ', r'\1\n', self.entry)
            self.entry = re.sub(r'\s*Game finished - ', r'\n', self.entry)
            self.entry = re.sub(r'\s*(Players:)', r'\n\1', self.entry)
            self.entry = re.sub(r',?\s*(round:)', r'\n\1', self.entry)

    def add_entry(self):
        if self.log and not self.log.endswith('\n'):
            self.log += '\n'
        self.clean_up_entry()
        self.log += self.entry
        if self.log and not self.log.endswith('\n'):
            self.log += '\n'
        self.entry = ''

    def handle_starttag(self, tag, attrs):
        if tag in ('div', 'li'):
            self.add_entry()
        if tag == 'div':
            for attr in attrs:
                if attr[0] == 'id':
                    div_id = attr[1]
                    if div_id == 'nations-gameheader':
                        self.state = self.STATE_HEADER
                    elif div_id == 'nations-log':
                        self.state = self.STATE_LOG
        if self.state == self.STATE_OTHER:
            return
        if tag == 'img':
            for attr in attrs:
                if attr[0] == 'src':
                    image_name = re.sub(r'^.*/([^/]*)\.[^.]*', r'\1', attr[1])
                    if image_name.startswith('Disc_'):
                        return
                    image_name = re.sub(r'^Token_', r'', image_name)
                    if image_name.startswith('Meeple'):
                        image_name = 'Worker'
                    if image_name == 'Heritage':
                        image_name = 'Books'
                    if self.entry:
                        self.entry += ' '
                    self.entry += '[' + image_name + ']'

    def handle_endtag(self, tag):
        if tag in ('div', 'li'):
            self.add_entry()
        if tag == 'div':
            self.state = self.STATE_OTHER

    def handle_data(self, data):
        if (self.state == self.STATE_OTHER or not data.strip()) and not data.startswith('Game finished'):
            return
        if self.entry:
            self.entry += ' '
        self.entry += data.strip()

    def parse_page(self, page):
        self.state = self.STATE_OTHER
        self.log = ''
        self.entry = ''
        self.feed(page)
        log = self.log
        self.state = self.STATE_OTHER
        self.log = ''
        self.entry = ''
        return log

def parse_page(page):
    return Parser().parse_page(page)
