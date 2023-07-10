from websearch import WebSearch as web
import requests
from bs4 import BeautifulSoup
import pandas as pd
import random
import time

# Given a team_code (i.e. abbreviation), return a dataframe of floats detailing the
# effect on the number of hits and strikeouts there are in a particular park
def park_factor(team_code):
    name = code_to_name(team_code)
    factor_table = pd.read_csv("~/Documents/mlb_project/v2_park_factors.csv")
    for i in factor_table.index:
        if factor_table.iloc[i]["Team"] in name:
            return factor_table.iloc[i]

# Helper function to find the proper url based on the KEY_PHRASE
def find_url(possiblites, key_phrase):
    url = ''
    index = 0
    while not url:
        if key_phrase in possiblites[index]:
            url = possiblites[index]
        index += 1
    return url

# Given a team code, find the full name of the team.
def code_to_name(code):
    possible_urls = web("bref team ids").pages
    url = find_url(possible_urls, "baseball-reference")
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    time.sleep(random.uniform(1, 5))

    html = soup.find_all("table", class_="stats_table")
    table = pd.read_html(str(html))[0] # Gets all MLB teams that ever existed.

    current_teams = table.loc[table[4] == "Present"]
    current_teams = current_teams.drop([0, 3, 4], axis=1)
    current_teams = current_teams.reset_index(drop=True)

    team = current_teams.loc[current_teams[1] == code]
    team = team.reset_index(drop=True)
    name = team[2][0]
    
    return name
