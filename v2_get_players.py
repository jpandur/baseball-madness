import requests
from bs4 import BeautifulSoup
from bs4 import Comment
from websearch import WebSearch as web
import pandas as pd
import time
import random
from v2_at_bat import *


# Finds the lineups for the game based on the team name entered.
# Returns two lists, one for the away team and one for the home team.
# The first element of each list contains the team's abbreviation.
# The second element of each list contains the team's starting pitcher.
# The other list elements contain a batter's name, handedness, and position.
def get_lineups(team):
    possible_urls = web(team + " starting lineups").pages
    url = find_url(possible_urls, "mlb.com")
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    all_away_lineups = soup.find_all("ol", class_="starting-lineups__team--away")
    all_home_lineups = soup.find_all("ol", class_="starting-lineups__team--home")
    
    # Find batting roster for away and home players and place in a list
    today_away_lineup = all_away_lineups[0].text
    today_home_lineup = all_home_lineups[0].text
    away_list = [player for player in today_away_lineup.split("\n") if player]
    home_list = [player for player in today_home_lineup.split("\n") if player]

    # Find names of teams and place them in respective lists
    away_heads = soup.find_all("div", class_="starting-lineups__teams--away-head")
    home_heads = soup.find_all("div", class_="starting-lineups__teams--home-head")
    away_name = (away_heads[0].text).split()[0]
    home_name = (home_heads[0].text).split()[0]
    
    away_list.insert(0, away_name)
    home_list.insert(0, home_name)

    # Add starting pitchers to the lists and their handedness
    pitcher_summary = soup.find_all("div", class_="starting-lineups__pitcher-summary")
    away_info = pitcher_summary[0]
    away_pitcher_name = away_info.find("div", class_="starting-lineups__pitcher-name").text.strip("\n")
    away_pitcher_handedness = away_info.find("span", class_="starting-lineups__pitcher-pitch-hand").text.strip()[0]
    
    home_info = pitcher_summary[2] # index 1 is skipped because it's empty
    home_pitcher_name = home_info.find("div", class_="starting-lineups__pitcher-name").text.strip("\n")
    home_pitcher_handedness = home_info.find("span", class_="starting-lineups__pitcher-pitch-hand").text.strip()[0]
    
    away_list.insert(1, away_pitcher_name + " (" + away_pitcher_handedness + ")")
    home_list.insert(1, home_pitcher_name + " (" + home_pitcher_handedness + ")")

    return away_list, home_list

user_input = input("Enter a team name: ")
away_lineup, home_lineup = get_lineups(user_input)
print(away_lineup)
print(home_lineup)