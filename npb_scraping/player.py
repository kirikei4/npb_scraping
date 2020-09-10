from bs4 import BeautifulSoup
import requests
import pandas as pd
from bs4 import Comment

ROOT_URL = 'https://www.baseball-reference.com'

C_TEAM_NAMES = [
    'Chunichi Dragons', 'Hanshin Tigers', 'Hiroshima Carp', 'Yakult Swallows', 
    'Yokohama Bay Stars', 'Yomiuri Giants'
]

P_TEAM_NAMES = [
    'Chiba Lotte Marines', 'Fukuoka Softbank Hawks', 'Hokkaido Nippon Ham Fighters', 
    'Orix Buffaloes', 'Saitama Seibu Lions', 'Tohoku Rakuten Golden Eagles'
]

class ScrapingNPB(object):
    """抽象規定クラス
    """
    
    def __init__(self, year_list=[], league=None, **kwargs):
        
        if len(year_list) < 1:
            raise ValueError('year_list is blank! Please set year_list.')
        
        self._year_list = year_list
        self._league = league
    
    def get_table(self):
        raise NotImplimentedError
        
class ScrapingNPBTeam(ScrapingNPB):
    """チームの情報を取ってくるクラス
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        if self._league:
            raise ValueError(
                    f'Please set JPCL or JPPL')
        
    def get_table(self):
        soup = get_nbp_league_soup(self._league)
        links = get_league_team_stats_links(soup)
        
        
class ScrapingNPBPlayer(ScrapingNPB):
    """選手を取ってくる抽象規定クラス
    """
    
    def __init__(self, team=None, **kwargs):
        super().__init__(**kwargs)
        
        self._team = team

        if not team is None:
            if team in C_TEAM_NAMES:
                self._league = 'JPCL'
            elif team in P_TEAM_NAMES:
                self._league = 'JPPL'
            else:
                raise ValueError(
                    f'Invalid team names! please select from {C_TEAM_NAMES} or {P_TEAM_NAMES}')
        
    def get_table(self):
        """ある年からある年までの選手の成績を取ってくる関数
    
        Args:
            year_list (List(int)): データを持ってくる年
            league (str): データを持ってくるリーグ名， セリーグ or パリーグ (JPCL or JPPL)，Noneの場合は全て
            team (str): チーム名，Noneの場合は全てのチーム
        """

        league_soups = []
        
        if self._league is None:
            league_soups.append(get_nbp_league_soup('JPCL'))
            league_soups.append(get_nbp_league_soup('JPPL'))
        else:
            league_soups.append(get_nbp_league_soup(self._league))
    
        league_table = []
        # リーグ毎
        for soup in league_soups:
            team_links = get_team_player_links(soup) 
            league_table.append(self._get_tables_from_team_links(team_links))
            
        return pd.concat(league_table, axis=0)
    
    def _get_tables_from_team_links(self, team_links):
        """soup毎の指定された年，チームのDataFrameを返す関数
        """
        
        tables = []
        
        for year in self._year_list:
            print(f'scraping {year}...')
            year_link = team_links[str(year)]

            if self._team is None:
                for t, link in year_link.items():
                    team_soup = self._get_team_soup(link)
                    df = self._get_team_table_from_team_soup(team_soup)
                    df['team'] = t
                    df['year'] = year
                    
                    tables.append(df)
            
            else:
                team_link = year_link[self._team]
                team_soup = self._get_team_soup(team_link)
                df = self._get_team_table_from_team_soup(team_soup)
                df['team'] = self._team
                df['year'] = year
                
                tables.append(df)
                
        tables = pd.concat(tables, axis=0)
        tables = tables.set_index(['team', 'year', 'Name'])
        
        return tables
    
    def _get_team_table_from_team_soup(self, team_links):
        raise NotImplementedError()
        
    def _get_team_soup(self, link):
        """チームのページのsoupを取ってくる
        """
        
        url = f'{ROOT_URL}{link}'
        s = requests.get(url).content
        return BeautifulSoup(s, "lxml")
    
    def _scraping_from_table(self, table):
        
        data = []
        
        headings = [th.get_text() for th in table.find("tr").find_all("th")][1:]
        data.append(headings)
        # 表のbodyを取得
        table_body = table.find('tbody')
        # bodyから各行を取得
        rows = table_body.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            # タグを外して文字だけ取り出す，空白文字は無視してリスト化
            cols = [ele.text.strip() for ele in cols]
            data.append([ele for ele in cols])
        data = pd.DataFrame(data)
        # １行目にカラム名が入っているのでカラム名を書き換えて１行目を削除
        data = data.rename(columns=data.iloc[0])
        data = data.reindex(data.index.drop(0))
        
        data = self._insert_dominant_hand(data)
        
        return data
    
    def _insert_dominant_hand(self, data):
        left_hands = data['Name'].str.endswith('*')
        data.loc[left_hands, 'Hand'] = 'Left'
        data.loc[left_hands, 'Name'] = data.loc[left_hands, 'Name'].str.replace('*', '')
        double_hands = data['Name'].str.endswith('#')
        data.loc[double_hands, 'Hand'] = 'Double'
        
        # 残ったNaNは全て右利き
        data['Hand'].fillna('Right', inplace=True)
        # 名前から余分な記号を外す
        data['Name'] = data['Name'].str.rstrip('# *')
        return data

    
class ScrapingNPBPitcher(ScrapingNPBPlayer):
    
    def _get_team_table_from_team_soup(self, soup):
        """指定されたチームのリンクからチーム内の選手の成績表を返す関数

            Args:
                soup (bs4): チームのページのsoup

            Return:
                pandas.DataFrame
        """

        # ピッチャーの場合コメントアウトされているので特殊処理
        table = self._extract_pitcher_table(soup)
            
        return self._scraping_from_table(table)
    
    def _extract_pitcher_table(self, soup):
        """ピッチャーはコメントアウトされているのでコメントを取り出してタグ抽出
        """
        comment = soup.find_all(string=lambda text: isinstance(text, Comment))
        for c in comment:
            c_soup = BeautifulSoup(c, "lxml")
            c_table = c_soup.find_all('table')
            if len(c_table) > 0:
                return c_table[0]
    
    
class ScrapingNPBBatter(ScrapingNPBPlayer):
        
    def _get_team_table_from_team_soup(self, soup):
        """指定されたチームのリンクからチーム内の選手の成績表を返す関数

            Args:
                soup (bs4): チームのページのsoup

            Return:
                pandas.DataFrame
        """
        
        table = soup.find_all('table', attrs={'id':'team_batting'})[0]
            
        return self._scraping_from_table(table)
    
    
    
    
# 汎用関数
def get_nbp_league_soup(league):
    """NPBのリーグ毎の表を取得する関数
        e.g. https://www.baseball-reference.com/register/league.cgi?code={league}&class=Fgn
    
        Args:
            league(str): セリーグ or パリーグ (JPCL or JPPL)
            
        Return:
            soup: リーグの一覧表
    """
    
    leagues_list = ['JPCL', 'JPPL']
    
    if not league in leagues_list:
        raise ValueError(f'Valid league are {leagues_list}')
    
    url = f'https://www.baseball-reference.com/register/league.cgi?code={league}&class=Fgn'
    s = requests.get(url).content
    return BeautifulSoup(s, "lxml")
    
def get_team_player_links(league_soup):
    """NPBのsoupを解いてリンク集を取り出す関数
    
        Args:
            league_soup(BeautifulSoup): NPB leagueの一覧表
            
        Return:
            Dict: 
                {
                    2019:{
                        chunichi dragons: URL,
                        yokohama baystars: URL,
                        ...
                    },
                    2018:{
                        ...
                    }
                }
    """
    
    table = league_soup.find_all('table')[0]
    year_links = dict()
    # 表のbodyを取得
    table_body = table.find('tbody')
    # bodyから各行を取得
    rows = table_body.find_all('tr')
    for row in rows:
        # 年の取得
        year = row.find('th').text
        col = row.find_all('td')[0]
        # 各チームのリンクの取得
        links = col.find_all('a')
        links = dict((ele.text, ele.get('href')) for ele in links)
        # チーム名:リンクのリスト
        year_links[year] = links
        
    return year_links

def get_league_team_stats_links(league_soup):
    """NPBのsoupを解いて年度のチームのサマリのリンク集を取り出す関数
    
        Args:
            league_soup(BeautifulSoup): NPB leagueの一覧表
            
        Return:
            Dict: 
                {
                    2019:https://2019-no-team-seiseki/,
                    2018:...
                }
    """
    
    table = league_soup.find_all('table')[0]
    year_links = dict()
    # 表のbodyを取得
    table_body = table.find('tbody')
    # bodyから各行を取得
    rows = table_body.find_all('tr')
    for row in rows:
        # 年の取得
        year_part = row.find('th')
        year = year_part.text
        link = year_part.find('a')
        
        year_links[year] = link
        
    return year_links