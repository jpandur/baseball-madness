import requests
from bs4 import BeautifulSoup
from websearch import WebSearch as web
import pandas as pd
import time
import random

def get_roster():
    url = 'https://www.mlb.com/angels/roster/starting-lineups'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    data = soup.find_all('div', class_="starting-lineups__teams starting-lineups__teams--xs starting-lineups__teams--md starting-lineups__teams--lg")

    lineup = data[0].text # Gets today's lineup only when index is 0
    lineup = lineup.split("\n")

    # Delete empty string elements and remove excess whitespace
    lineup = [item for item in lineup if item]
    lineup.pop(3)
    lineup.pop(1)
    lineup = [item.strip(' ') for item in lineup]

    # Establish away team and home team lineup
    awayTeam = [lineup[0][:3]]
    homeTeam = [lineup[1][:3]]
    lineup = lineup[2:]

    # Add players to respsective teams, delete info on position and handedness
    for i in range(len(lineup)):
        if i < 9:
            awayTeam.append(lineup[i][:-6].rstrip())
        else:
            homeTeam.append(lineup[i][:-6].rstrip())
    
    return awayTeam, homeTeam

# Given a player name and the player's team, extract batting information for current season
# All arguments are strings
def extract_player_data_batting(player, team, year):
    # Find part of page that contains batting data
    print(player + " " + team + " bref stats, height, weight, position")
    url = web(player + " " + team + " bref stats, height, weight, position").pages[0]
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'lxml')
    table1 = soup.find('table', id="batting_standard")

    # Record all the column names (i.e. G, PA, AB)
    headers = []
    for i in table1.find_all('th'):
        title = i.text
        headers.append(title)
    headers = headers[1:30]
    
    # Get all data for current season
    body = table1.find('tr', id="batting_standard." + year)
    body = body.find_all('td')
    items = []
    for j in body:
        items += [j.text]
    data = pd.DataFrame(columns=headers, index=[year])
    
    # Combine column names and current season stats into one table
    for i in range(len(items)):
        data.iloc[0][i] = items[i]

    return data

# Convert a lineup to stats
def player_to_stats(team, year):
    stats = []
    for player in team[1:]:
        stats += [extract_player_data_batting(player, team[0], year)]
        time.sleep(1)
    return stats

# Determines result of a single batter.
# TEAM is either home or away, BOP is batter order position (0-8).
def batter(team, bop):
    player = team[bop]
    obp = float(player["OBP"][0])
    if obp < round(random.uniform(0, 1), 3):
        return "Out"
    else:
        times_on_base = int(player["H"][0]) + int(player["BB"][0]) + int(player["HBP"][0])
        base_result = round(random.uniform(1, times_on_base)) # Generates hit, walk, HBP

        if base_result <= int(player["H"][0]):
            if base_result <= int(player["H"][0]) - int(player["2B"][0]) - int(player["3B"][0]) - int(player["HR"][0]):
                return "Single"
            elif base_result <= int(player["H"][0]) - int(player["3B"][0]) - int(player["HR"][0]):
                return "Double"
            elif base_result <= int(player["H"][0]) - int(player["HR"][0]):
                return "Triple"
            else:
                return "Home Run"
        elif base_result <= int(player["H"][0]) + int(player["BB"][0]):
            return "Walk"
        else:
            return "HBP"
        
# Simulates an inning and returns the number of runs batting team has and the next BOP
def inning(runs, bop, stats):
    outs_left = 3
    runners_position = "---"

    while outs_left > 0:
        result = batter(stats, bop)
        if result == "Out":
            outs_left -= 1
        elif result == "Double":
            runs += runners_position[1:].count("*")
            runners_position = "-*" + runners_position[0]
        elif result == "Triple":
            runs += runners_position.count("*")
            runners_position = "--*"
        elif result == "Home Run":
            runs = runs + runners_position.count("*") + 1
            runners_position = "---"
        else:
            runs += runners_position[2:].count("*")
            runners_position = "*" + runners_position[:2]

        if bop == 8: # i.e. if at end of lineup, go back to top of order
            bop = 0
        else:
            bop += 1

    return runs, bop

# Simulates a game
def game(away_stats, home_stats, away_runs, home_runs, away_bop, home_bop):
    num_half_innings = 18
    for half_inning in range(num_half_innings):
        if half_inning % 2 == 0: # i.e. away team is batting
            away_runs, away_bop = inning(away_runs, away_bop, away_stats)
        else:
            home_runs, home_bop = inning(home_runs, home_bop, home_stats)
    
    while away_runs == home_runs:
        away_runs, away_bop = inning(away_runs, away_bop, away_stats)
        home_runs, home_bop = inning(home_runs, home_bop, home_stats)
    
    if away_runs > home_runs:
        return "AWAY WIN"
    else:
        return "HOME WIN"
