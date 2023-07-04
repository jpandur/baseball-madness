import requests
from bs4 import BeautifulSoup
from websearch import WebSearch as web
import pandas as pd
import time
import random
from v1_mini_func import *

AVERAGE_RUNS_PER_INNING = 0.444

def get_lineup():
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

def get_starting_pitching(year):
    url = 'https://www.mlb.com/angels/roster/starting-lineups'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    data = soup.find_all('div', class_="starting-lineups__pitcher-overview")
    starting_pitching = (data[0].text).split("\n")
    starting_pitching = [item.strip(' ') for item in starting_pitching]
    starting_pitching = [item for item in starting_pitching if item]
    starters = [starting_pitching[0], starting_pitching[3]] # away starter, home starter
    starters_run_per_inn = []

    for pitcher in starters:
        print(pitcher + " bref stats, height, weight, position")
        url = web(pitcher + " bref stats, height, weight, position").pages[0]
        page = requests.get(url)
        soup = BeautifulSoup(page.text, 'lxml')
        recent_starts_table = soup.find('table', id="last5")

        # Get pitcher data for last five starts
        headers = find_headers(recent_starts_table)
        headers = headers[:-5]
        headers = headers[1:]

        data = pd.DataFrame(columns=headers)
        for j in recent_starts_table.find_all('tr')[1:]:
            row_data = j.find_all('td')
            row = [i.text for i in row_data]
            length = len(data)
            data.loc[length] = row
        
        recent_innings = string_to_int_sum(data["IP"], float)
        recent_runs_allowed = string_to_int_sum(data["R"], int)
        recent_avg_start_length = round(recent_innings / 5.0, 3)
        recent_runs_per_inning = round(recent_runs_allowed / recent_innings, 3)

        # Get entire season peformance
        season_table = soup.find('table', id="pitching_standard")
        headers = find_headers(season_table)
        headers = headers[1:35]

        body = season_table.find('tr', id="pitching_standard." + year)
        body = body.find_all('td')
        stats = []
        for j in body:
            stats += [j.text]

        season_data = dict(zip(headers, stats))
        season_innings = float(season_data["IP"])
        season_runs = int(season_data["R"])
        num_games = int(season_data["G"])

        avg_start_length = round(season_innings / num_games, 3)
        avg_runs_per_inning = round(season_runs / season_innings, 3)

        starters_run_per_inn += [starting_pitcher_calculation(recent_avg_start_length,
                recent_runs_per_inning, avg_start_length, avg_runs_per_inning)]
        
    return starters_run_per_inn


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
    headers = find_headers(table1)
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
# TEAM is either home or away, BOP is batter order position (0-8), BASEPATHS shows occupied bases.
def batter(team, bop, basepaths):
    player = team[bop]
    obp = float(player["OBP"][0])
    times_on_base = int(player["H"][0]) + int(player["BB"][0]) + int(player["HBP"][0])
    if obp < round(random.uniform(0, 1), 3):
        times_out = int(player["PA"][0]) - times_on_base
        out_result = round(random.uniform(1, times_out)) # Generates GDP, SH, SF, or regular out

        if out_result <= int(player["GDP"][0]) and basepaths[0] == "*":
            return "GDP"
        elif out_result <= int(player["GDP"][0]) + int(player["SH"][0]) and basepaths.count("*") > 0:
            return "SH"
        elif out_result <= int(player["GDP"][0]) + int(player["SH"][0]) + int(player["SF"][0]) and basepaths[2] == "*":
            return "SF"
        else:
            return "Out"
    else:
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
        result = batter(stats, bop, runners_position)
        if result == "Out":
            outs_left -= 1
        elif result == "GDP":
            outs_left -= 2
            if outs_left > 0 and runners_position[2] == "*":
                runs += 1
            runners_position = "--" + runners_position[1]
        elif result == "SH":
            outs_left -= 1
            if outs_left > 0 and runners_position[2] == "*":
                runs += 1
            runners_position = "-" + runners_position[0:2]
        elif result == "SF":
            outs_left -= 1
            if outs_left > 0 and runners_position[2] == "*":
                runs += 1
            runners_position = runners_position[0:2] + "-"
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
def game(away_stats, home_stats, away_runs, home_runs, away_bop, home_bop, starters):
    num_half_innings = 18
    for half_inning in range(num_half_innings):
        if half_inning % 2 == 0: # i.e. away team is batting
            away_runs, away_bop = inning(away_runs, away_bop, away_stats)
        else:
            home_runs, home_bop = inning(home_runs, home_bop, home_stats)
    
    # Factor impact of starting pitcher
    away_starting_pitcher_difference = (AVERAGE_RUNS_PER_INNING - starters[0][0]) * starters[0][1]
    home_starting_pitcher_difference = (AVERAGE_RUNS_PER_INNING - starters[1][0]) * starters[1][1]
    away_runs += away_starting_pitcher_difference
    home_runs += home_starting_pitcher_difference

    while away_runs == home_runs:
        away_runs, away_bop = inning(away_runs, away_bop, away_stats)
        home_runs, home_bop = inning(home_runs, home_bop, home_stats)
    
    if away_runs > home_runs:
        return "AWAY WIN"
    else:
        return "HOME WIN"
