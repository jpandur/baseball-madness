from datetime import datetime
from websearch import WebSearch as web
import requests
from bs4 import BeautifulSoup, Comment
import pandas as pd

CURRENT_YEAR = str(datetime.now().year)

# Determines the result of an at-bat based on the situation (i.e. BASEPATHS and NUM_OUTS).
# Finds batter and pitcher data for this situation to make a prediction.
# Return value is a string describing the outcome.
def at_bat(batter, pitcher, basepaths, num_outs):
    batter_name = batter.split("(")[0] # Gets part before the open parenthesis
    batter_handedness = batter.split("(")[1][0]
    batter_position = batter.split()[-1]
    pitcher_name = pitcher.split("(")[0]
    pitcher_handedness = pitcher.split("(")[1][0]

    if batter_handedness == "S":
        if pitcher_handedness == "R":
            batter_handedness = "L"
        else:
            batter_handedness = "R"

    # Get relevant links for batter and pitcher.
    batter_stats_url, batter_splits_url, batter_game_log_url = stat_links(batter_name, "b")
    pitcher_stats_url, pitcher_splits_url, pitcher_game_log_url = stat_links(pitcher_name, "p")

    # Get relevant tables for batter and pitcher.
    batter_splits_tables = get_splits_tables(batter_splits_url)
    pitcher_splits_tables = get_splits_tables(pitcher_splits_url)
    batter_game_log_table = get_game_log_tables(batter_game_log_url, "batting")
    pitcher_game_log_table = get_game_log_tables(pitcher_game_log_url, "pitching")


    situational_bases_and_outs(batter_splits_tables[13][0], basepaths, num_outs)

    return

def inning():
    return

# Runs a simulated game given two teams.
# Returns the number of runs each team scores.
def game(away_team, home_team):
    away_starter = away_team[1]
    home_starter = home_team[1]
    away_batting = away_team[2:]
    home_batting = home_team[2:]
    away_bop, home_bop = 0, 0 # Batting order position for each team.

    for _ in range(9):
        inning()


# Helper function to find the proper url based on the KEY_PHRASE
def find_url(possiblites, key_phrase):
    url = ''
    index = 0
    while not url:
        if key_phrase in possiblites[index]:
            url = possiblites[index]
        index += 1
    return url

# Given a player name and a batter/pitcher classification, find relevant links to stats.
# Returns Fangraphs links to season stats, splits stats, game logs, and play logs.
def stat_links(name, classification):
    possible_urls = web(name + " baseball reference stats height weight " + CURRENT_YEAR).pages
    stats_url = find_url(possible_urls, "baseball-reference.com")

    parts_of_stats_url = stats_url.split("/")
    index = 0
    general_url = ''

    # Finds the part of the URL that is the same regardless of what page is visited.
    while True:
        if "shtml" in parts_of_stats_url[index]:
            general_url = general_url[:-2] # Remove last slash and letter
            break
        general_url = general_url + parts_of_stats_url[index] + "/"
        index += 1

    # Variable PLAYER_IDENTIFIER keeps part of the URL that contains player's "name".
    player_identifier = parts_of_stats_url[index].split(".")[0]

    # Concatenate strings to create splits URL, game log URL, and play log URL.
    splits_url = general_url + "split.fcgi?id=" + player_identifier + "&year=" + CURRENT_YEAR + "&t=" + classification
    game_log_url = general_url + "gl.fcgi?id=" + player_identifier + "&t=" + classification + "&year=" + CURRENT_YEAR

    return stats_url, splits_url, game_log_url

# Given a url, return all tables on that page.
def get_splits_tables(player_url):
    response = requests.get(player_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    comments = soup.find_all(string=lambda text: isinstance(text, Comment))
    tables = []
    for each in comments:
        if 'table' in each:
            try:
                tables.append((pd.read_html(str(each))))
            except:
                continue
    
    return tables

# Given a url and identifier (batting or pitching), return game log table.
def get_game_log_tables(player_url, identifier):
    response = requests.get(player_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    html = soup.find_all("table", id=identifier + "_gamelogs")
    table = pd.read_html(str(html))[0]
    return table

# Given a table with pertient information, the basepaths, and the number of outs,
# return the number of times safe and number of times out.
def situational_bases_and_outs (table, basepaths, num_outs):
    return

# Test Case
at_bat("Fernando Tatis Jr. (R) RF", "Lance Lynn (R)", "___", 1)