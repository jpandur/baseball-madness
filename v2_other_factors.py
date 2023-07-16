from datetime import datetime
from websearch import WebSearch as web
import requests
from bs4 import BeautifulSoup, Comment
import pandas as pd
import time
import random

CURRENT_YEAR = str(datetime.now().year)

# Given a team_code (i.e. abbreviation), return a dataframe of floats detailing the
# effect on the number of hits and strikeouts there are in a particular park.
def park_factor(team_code):
    name = code_to_name(team_code)
    factor_table = pd.read_csv("~/Documents/mlb_project/v2_park_factors.csv")
    for i in factor_table.index:
        if factor_table.iloc[i]["Team"] in name:
            print("Game location found!")
            return factor_table.iloc[i]

# Given a team code, find the full name of the team.
def code_to_name(code):
    name_table = pd.read_csv("~/Documents/mlb_project/v2_team_names.csv")
    row = name_table.loc[name_table["Code"] == code]
    row = row.reset_index(drop=True)
    return row.loc[0, "Name"]

# Helper function to find the proper url based on the KEY_PHRASE
def find_url(possiblites, key_phrase):
    url = ''
    index = 0
    while not url:
        if key_phrase in possiblites[index]:
            url = possiblites[index]
        index += 1
        if index == len(possiblites):
            return url
    return url

# Given a player name and a batter/pitcher classification (b/p), find relevant links to stats.
# Returns Bref links to season stats, splits stats, game logs, and play logs.
def stat_links(name, classification, team_name):
    possible_urls = web(name + team_name + " baseball reference stats height weight " + CURRENT_YEAR).pages
    stats_url = find_url(possible_urls, "baseball-reference.com/players")
    time.sleep(random.uniform(3, 4))
    if not stats_url:
        return '', '', ''

    parts_of_stats_url = stats_url.split("/")
    index = 0
    general_url = ''

    # Finds the part of the URL that is the same regardless of what page is visited.
    try:
        while True:
            if "shtml" in parts_of_stats_url[index]:
                general_url = general_url[:-2] # Remove last slash and letter
                break
            general_url = general_url + parts_of_stats_url[index] + "/"
            index += 1
    except:
        return '', '', ''

    # Variable PLAYER_IDENTIFIER keeps part of the URL that contains player's "name".
    player_identifier = parts_of_stats_url[index].split(".")[0]

    # Concatenate strings to create splits URL, game log URL, and play log URL.
    splits_url = general_url + "split.fcgi?id=" + player_identifier + "&year=" + CURRENT_YEAR + "&t=" + classification
    game_log_url = general_url + "gl.fcgi?id=" + player_identifier + "&t=" + classification + "&year=" + CURRENT_YEAR

    print(splits_url)
    print(game_log_url)
    return stats_url, splits_url, game_log_url

# Used for relievers, get the last five games played on their main stats page if possible.
def get_last5_table(player_url):
    response = requests.get(player_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    time.sleep(random.uniform(3, 4))
    html = soup.find_all("table", id="last5")
    if html == []:
        return []
    else:
        return pd.read_html(str(html))[0]

# Given a url, return all tables on that page.
def get_splits_tables(player_url):
    response = requests.get(player_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    time.sleep(random.uniform(3, 4))

    comments = soup.find_all(string=lambda text: isinstance(text, Comment))
    tables = []
    for each in comments:
        if 'table' in each:
            try:
                tables.append(pd.read_html(str(each)))  
            except:
                continue
    return tables

# Given a url and identifier (batting or pitching), return game log table.
def get_game_log_tables(player_url, identifier):
    response = requests.get(player_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    html = soup.find_all("table", id=identifier + "_gamelogs")
    try:
        table = pd.read_html(str(html))[0]
        table = table[table["Date"].notna()] # Drop rows with NaN in Date column
        time.sleep(random.uniform(3, 4))
        return table
    except:
        return []
    