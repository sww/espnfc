import sys
from datetime import date, datetime

import requests
from bs4 import BeautifulSoup


# League name: id.
ESPN_LEAGUES_IDS = {
    # UEFA Champion's League.
    'champs': 2,
    'champ': 2,
    'cl': 2,

    # UEFA Europa League.
    'europa': 2310,
    'el': 2310,

    # French Ligue 1.
    'ligue1': 9,
    'france': 9,

    # French Coupe de France.
    'coupe': 182,

    # Dutch Eredivisie.
    'eredivisie': 11,
    'netherlands': 11,

    # Italian Serie A.
    'seriea': 12,
    'italy': 12,

    # Italian Coppa Italia.
    'coppa': 2192,

    # German Bundesliga.
    'bundesliga': 10,
    'germany': 10,

    # German DFB Pokal.
    'pokal': 2061,
    'dfbpokal': 2061,

    # Spanish Primera Divison.
    'primeradivison': 15,
    'spain': 15,

    # Spanish Super Cup.
    'supercup': 431,

    # English Premier League.
    'premier': 24,
    'england': 24,

    # English FA Cup.
    'fa': 20,
}

# League id: displayable League name.
ESPN_LEAGUE_NAMES = {
    '2': 'UEFA Champion\'s League',
    '9': 'French Ligue 1',
    '10': 'German Bundesliga',
    '11': 'Dutch Eredivisie',
    '12': 'Italian Serie A',
    '15': 'Spanish Primera Divison',
    '24': 'English Premier League',
    '20': 'English FA Cup',
    '182': 'French Coupe de France',
    '431': 'Spanish Super Cup',
    '2061': 'German DFB Pokal',
    '2192': 'Italian Coppa Italia',
    '2310': 'UEFA Europa League',
}


class Fixture(object):

    def __init__(self,
                 teams=None,
                 scores=None,
                 league=None,
                 winner=None,
                 game_time=None,
                 game_link=None):
        self.teams = teams
        self.scores = scores
        self.league = league
        self._winner = winner

        self._game_time = game_time
        self.game_link = game_link

    @property
    def winner(self):
        if self._winner is None:
            return None

        return self.teams[self._winner]

    @property
    def game_time(self):
        try:
            return datetime.strptime(
                self._game_time, '%H:%M %p %Z')
        except ValueError:
            return self._game_time

    def pretty(self):
        """Returns a pretty fixture stats string."""
        return '%s - %s vs %s, %s - %s, %s' % (
            self.league,
            self.teams[0].name,
            self.scores[0],
            self.teams[1].name,
            self.scores[1],
            self._game_time)

    def __repr__(self):
        return '<Fixture %s vs %s>' % (
            repr(self.teams[0].name).decode('utf-8'),
            repr(self.teams[1].name).decode('utf-8'),)


class Club(object):

    def __init__(self, name='', league=None):
        self.name = name
        self.league = league

    def __repr__(self):
        return str(self.name.encode('utf-8'))

    def __unicode__(self):
        return self.name


class ESPNFC(object):

    # Base URL.
    URL = 'http://www.espnfc.us/scores?date=%s&xhr=1'

    def _retrieve(self, day):
        response = requests.get(self.URL % day)
        # TODO: Handle requests that failed.
        return response.json()

    def get_fixtures(self, league=None, day=None):
        if league is not None and league not in ESPN_LEAGUES_IDS:
            raise Exception('Could not find the league id.')

        response = self._retrieve(day)
        if not response.get('content', {}).get('html'):
            raise Exception('Unable to get content')

        soup = BeautifulSoup(
            response.get('content').get('html'), 'lxml')
        if league:
            soup = soup.find(
                'div',
                attrs={'data-league-id': ESPN_LEAGUES_IDS[league]})

            if soup is None:
                return []

        return self._parse_fixtures(soup)

    def _parse_fixtures(self, soup):
        fixtures = []
        for league_div in soup.find_all('div',
                                        attrs={'class': 'score-league'}):
            league_id = None
            if league_div.attrs:
                league_id = league_div.attrs.get('data-league-id')

            # Unknown means don't care.
            league = ESPN_LEAGUE_NAMES.get(league_id, 'Unknown')

            for fixture_div in league_div.find_all(
                    'div',
                    attrs={'class': 'score full'}):
                if 'data-gameid' not in fixture_div.attrs:
                    continue

                teams = []
                for team in fixture_div.find_all('div',
                                                 attrs={'class': 'team-name'}):
                    teams.append(Club(unicode(team.text)))

                scores = []
                winner = None
                for i, score in enumerate(
                        fixture_div.find_all('div',
                                             attrs={'class': 'team-score'})):
                    scores.append(int(score.text) if score.text else 0)
                    if 'winner' in score.attrs.get('class'):
                        winner = i

                # Time left, start time, or 'FT'.
                game_time = fixture_div.find('div',
                                             attrs={'class': 'game-info'})
                game_time = game_time.text

                game_link = fixture_div.find('a',
                                             attrs={'class': 'primary-link'})
                game_link = game_link.get('href')

                fixtures.append(
                    Fixture(
                        teams=teams,
                        scores=scores,
                        league=league,
                        winner=winner,
                        game_time=game_time,
                        game_link=game_link))

        return fixtures


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument('-l', '--league', dest='league', action='store',
                        choices=ESPN_LEAGUES_IDS.keys(), default=None,
                        help='Show fixtures for a league.')
    parser.add_argument('day', action='store', nargs='?',
                        default=date.today().strftime('%Y%m%d'),
                        help='Show fixtures for a certain day.')

    args = parser.parse_args()

    espnfc = ESPNFC()
    fixtures = espnfc.get_fixtures(league=args.league, day=args.day)

    if not fixtures:
        sys.exit('No fixtures')

    for i in fixtures:
        print i.pretty()
