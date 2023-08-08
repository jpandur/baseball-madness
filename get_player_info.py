from websearch import WebSearch as web
import requests
from bs4 import BeautifulSoup, Comment
import time
import random
from datetime import datetime
from helper_functions import *

YEAR = str(datetime.now().year)

# Finds the lineups for the game and batters' handedness.
def get_lineups(team):
    possible_urls = web(team + " starting lineups").pages
    url = find_url(possible_urls, "mlb.com")
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    time.sleep(random.uniform(3, 4))

    all_away_lineups = soup.find_all("ol", class_="starting-lineups__team--away")
    all_home_lineups = soup.find_all("ol", class_="starting-lineups__team--home")
    
    # Find batting roster for away and home players and place in a list
    today_away_lineup = all_away_lineups[0].text
    today_home_lineup = all_home_lineups[0].text
    away_list = [player for player in today_away_lineup.split("\n") if player]
    home_list = [player for player in today_home_lineup.split("\n") if player]

    # Get handedness of player lineup and remove from away list and home list.
    away_batting_handedness, home_batting_handedness = [], []
    for player in away_list:
        away_batting_handedness += [player.split("(")[1][0]]
    for player in home_list:
        home_batting_handedness += [player.split("(")[1][0]]

    for i in range(len(away_list)):
        away_list[i] = away_list[i].split("(")[0][:-1]
    for i in range(len(home_list)):
        home_list[i] = home_list[i].split("(")[0][:-1]

    # Find team codes and place team names in respective lists
    away_heads = soup.find_all("div", class_="starting-lineups__teams--away-head")
    home_heads = soup.find_all("div", class_="starting-lineups__teams--home-head")
    away_code = (away_heads[0].text).split()[0]
    home_code = (home_heads[0].text).split()[0]
    away_list.insert(0, code_to_name(away_code))
    home_list.insert(0, code_to_name(home_code))

    # Add starting pitchers to the lists and their handedness
    pitcher_summary = soup.find_all("div", class_="starting-lineups__pitcher-summary")
    away_info = pitcher_summary[0]
    away_pitcher_name = away_info.find("div", class_="starting-lineups__pitcher-name").text.strip("\n")
    away_pitcher_handedness = away_info.find("span", class_="starting-lineups__pitcher-pitch-hand").text.strip()[0]
    away_pitcher = away_pitcher_name + " (" + away_pitcher_handedness + ")"
    
    home_info = pitcher_summary[2] # index 1 is skipped because it's empty
    home_pitcher_name = home_info.find("div", class_="starting-lineups__pitcher-name").text.strip("\n")
    home_pitcher_handedness = home_info.find("span", class_="starting-lineups__pitcher-pitch-hand").text.strip()[0]
    home_pitcher = home_pitcher_name + " (" + home_pitcher_handedness + ")"

    print(away_list)
    print(home_list)
    print(away_batting_handedness)
    print(home_batting_handedness)
    print(away_pitcher_name)
    print(home_pitcher_name)
    return away_list, home_list, away_batting_handedness, home_batting_handedness, away_pitcher, home_pitcher

# Given a team name, return a list of bullpen pitchers for that team, in the form
# PITCHER (HANDEDNESS), along with their handedness.
def get_bullpen(team_name, starter):
    possible_url = web("mlb " + team_name + " depth chart").pages
    url = find_url(possible_url, "mlb.com")
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    time.sleep(random.uniform(3, 4))
    html = soup.find_all("table", class_="roster__table")

    bullpen_table = pd.read_html(str(html))[1] # get bullpen roster from list of players
    bullpen_table = bullpen_table.drop(["Bullpen", "Ht", "Wt", "DOB"], axis=1)
    bullpen_table = bullpen_table.loc[~bullpen_table["Bullpen.1"].str.contains("IL-")] # Exclude IL
    bullpen_table = bullpen_table.loc[~bullpen_table["Bullpen.1"].str.contains("Minors")] # Exclude Minors
    bullpen_table = bullpen_table.reset_index(drop=True)
    relief_pitchers = []
    handedness = []

    for index in bullpen_table.index:
        split_list = bullpen_table.iloc[index]["Bullpen.1"].split()
        name = ''
        for item in split_list:
            if not item.isnumeric():
                name = name + item + " "
            else:
                handedness += [bullpen_table.iloc[index]["B/T"][-1]]
                this_pitcher = name[:-1]
                if this_pitcher not in relief_pitchers and this_pitcher != starter:
                    relief_pitchers += [this_pitcher]
                break
    print(relief_pitchers)
    return relief_pitchers, handedness

# Determine whether a pitcher is available today based on how much he has pitched recently.
def check_pitcher_game_log(pitcher):
    possible_urls = web(pitcher.name + " game logs").pages
    time.sleep(random.uniform(1.9, 2.9))
    game_log_url = find_url(possible_urls, "espn")
    print(pitcher.name, game_log_url)
    if not game_log_url: # if pitcher does not have game log
        return True
    tables = pd.read_html(game_log_url)
    print("Length of game log tables for", pitcher.name, len(tables))

    try:
        this_month = tables[0]
        this_month = clean_game_log_tables(this_month)
        last_month = tables[1]
        last_month = clean_game_log_tables(last_month)

        games_this_month = min(5, len(this_month)) # in case there are less than five games for the month
        games_last_month = min(5 - games_this_month, len(last_month)) # get remaining necessary games from last month, if needed
        today = datetime.today()

        days_pitched_outs_recorded = []

        index = 0
        while index < games_this_month: # looking at recent games played this month
            this_date_str = this_month.loc[index, "Date"].split()[1] + "/" + YEAR
            this_date = datetime.strptime(this_date_str, '%m/%d/%Y')
            days_ago = abs((today - this_date).days)
            outs_recorded_str = str(this_month.loc[index, "IP"]).split(".")
            outs_recorded = 3 * int(outs_recorded_str[0]) + int(outs_recorded_str[1])
            pitches_thrown = int(this_month.loc[index, "P"])
            days_pitched_outs_recorded += [(days_ago, outs_recorded, pitches_thrown)]
            index += 1

        index = 0
        while index < games_last_month: # looking at recent games played last month
            this_date_str = last_month.loc[index, "Date"].split()[1] + "/" + YEAR
            this_date = datetime.strptime(this_date_str, '%m/%d/%Y')
            days_ago = abs((today - this_date).days)
            outs_recorded_str = str(last_month.loc[index, "IP"]).split(".")
            outs_recorded = 3 * int(outs_recorded_str[0]) + int(outs_recorded_str[1])
            pitches_thrown = int(last_month.loc[index, "P"])
            days_pitched_outs_recorded += [(days_ago, outs_recorded, pitches_thrown)]
            index += 1

        # Adjust pitcher OBP ratio based on number of days rest.
        days_rest = days_pitched_outs_recorded[0][0] - 1
        print(pitcher.name, days_rest, "days rest")
        days_rest_table = pitcher.days_rest_table
        print(days_rest_table)
        print(pitcher.name, pitcher.obp_ratio, "Before Adjustment")
        if not days_rest_table.empty:
            if days_rest == 1:
                days_rest_row = days_rest_table.loc[days_rest_table["Split"] == "1 Day,GR"]
            elif days_rest >= 6:
                days_rest_row = days_rest_table.loc[days_rest_table["Split"] == "6+ Days,GR"]
            else:
                days_rest_row = days_rest_table.loc[days_rest_table["Split"] == str(days_rest) + " Days,GR"]
            
            if not days_rest_row.empty:
                days_rest_row = days_rest_row.reset_index(drop=True)
                games = days_rest_row.loc[0, "G"]
                print(games, "games played on this much rest")
                adjustment_factor = int(days_rest_row.loc[0, "tOPS+"]) / 100
                if adjustment_factor < 0: # in case sOPS+ is negative
                    adjustment_factor = 0.25
                if adjustment_factor > 1: # max adjustment will be 25%
                    if games < 10:
                        adjustment_factor = min(1.25, adjustment_factor)
                elif adjustment_factor < 1:
                    if games < 10:
                        adjustment_factor = max(0.75, adjustment_factor)
                pitcher.obp_ratio = round(pitcher.obp_ratio * adjustment_factor, 5)
        print(pitcher.name, pitcher.obp_ratio, "After Adjustment")

        last_three_days_outs = 0 # tracks number of outs recorded in last three days
        last_three_days_pitches = 0 # tracks number of pitches in last three days
        last_week_outs = 0 # tracks number of outs recorded in last week
        last_week_times_pitched = 0 # tracks number of appearances in last week
        for element in days_pitched_outs_recorded:
            if element[0] <= 3:
                last_three_days_outs += element[1]
                last_three_days_pitches += element[2]
                last_week_times_pitched += 1
            elif element[0] <= 7:
                last_week_outs += element[1]
                last_week_times_pitched += 1
            else:
                break

        if (days_pitched_outs_recorded[0][0] == 1 or days_pitched_outs_recorded[0][0] == 2) and days_pitched_outs_recorded[0][1] > 3:
            # case where reliever pitched more than one inning yesterday or day before
            return False
        elif days_pitched_outs_recorded[0][0] == 1 and days_pitched_outs_recorded[1][0] == 2:
            # case where reliever pitched two days in a row
            return False
        elif last_three_days_outs >= 9 or last_week_times_pitched >= 4:
            # case where reliever has thrown 3+ innings in last three days or has pitched four times in last week
            return False
        elif last_week_outs >= 12:
            # case where reliever has thrown 4+ innings in last week
            return False
        elif days_pitched_outs_recorded[0][0] == 1 and days_pitched_outs_recorded[0][2] >= 25:
            # case where reliever threw more than 25 pitches yesterday
            return False
        elif last_three_days_pitches >= 50:
            # case where reliever threw more than 50 pitches last three days
            return False
        else:
            return True
    except:
        print(pitcher.name, "does not have any game logs!")
        return True    
    
# Helper function for check_pitcher_game_log
def clean_game_log_tables(table):
    index_to_remove = []
    table = table[:-1] # get rid of last row, which contains totals
    for i in table.index:
        if "acquired" in table.loc[i, "Date"]:
            index_to_remove += [i]
    index_to_remove.reverse()
    table = table.drop(index=index_to_remove)
    table = table.reset_index(drop=True)
    return table

# Given a player name, a batter/pitcher classification (b/p), and team name, find
# relevant link to player's splits page.
def get_splits_link(name, classification, team_name):
    possible_urls = web(name + team_name + " baseball reference stats height weight " + YEAR).pages
    time.sleep(random.uniform(1.9, 2.9))
    stats_url = find_url(possible_urls, "baseball-reference.com/players")
    if not stats_url:
        print(name)
        return ''

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
        print(name)
        return ''

    # Variable PLAYER_IDENTIFIER keeps part of the URL that contains player's "name".
    player_identifier = parts_of_stats_url[index].split(".")[0]
    splits_url = general_url + "split.fcgi?id=" + player_identifier + "&year=" + YEAR + "&t=" + classification

    print(name, splits_url)
    return splits_url

# Given a player's splits tables URL, return all tables on the page.
def get_splits_tables(url):
    if not url:
        return []
    response = requests.get(url)
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
    if not tables:
        return []
    return tables

# Given a list of all Dataframes from a batter's splits page, return the tables needed.
# Order: totals_table, platoon_table, home_away_table, bases_outs_table, times_facing_oppo_table
def get_batting_tables(all_tables):
    totals_table = pd.DataFrame()
    platoon_table = pd.DataFrame()
    home_away_table = pd.DataFrame()
    bases_outs_table = pd.DataFrame()
    times_facing_oppo_table = pd.DataFrame()

    for table in all_tables:
        actual_table = table[0] # Dataframes are placed in lists of length one.
        # Create filters for potential tables.
        possible_totals = actual_table.loc[actual_table["Split"] == YEAR + " Totals"]
        possible_platoon_rhp = actual_table.loc[actual_table["Split"] == "vs RHP"]
        possible_platoon_lhp = actual_table.loc[actual_table["Split"] == "vs LHP"]
        possible_home = actual_table.loc[actual_table["Split"] == "Home"]
        possible_away = actual_table.loc[actual_table["Split"] == "Away"]
        possible_bases_occupied_empty = actual_table.loc[actual_table["Split"] == "---"]
        possible_bases_occupied_men_on = actual_table.loc[actual_table["Split"] == "Men On"]
        possible_times_facing_sp = actual_table.loc[actual_table["Split"] == "vs. SP"]
        possible_times_facing_rp = actual_table.loc[actual_table["Split"] == "vs. RP"]
        # Check to see whether those tables are what is needed.
        if not possible_totals.empty:
            totals_table = actual_table
        elif not possible_platoon_rhp.empty or not possible_platoon_lhp.empty:
            platoon_table = actual_table
        elif not possible_home.empty or not possible_away.empty:
            home_away_table = actual_table
        elif not possible_bases_occupied_empty.empty or not possible_bases_occupied_men_on.empty:
            bases_outs_table = actual_table
        elif not possible_times_facing_sp.empty or not possible_times_facing_rp.empty:
            times_facing_oppo_table = actual_table

    return [totals_table, platoon_table, home_away_table, bases_outs_table, times_facing_oppo_table]

# Given a list of all Dataframes from a pitcher's splits page, return the tables needed.
# Order: totals_table, totals_table_game_level, platoon_table, home_away_table,
# home_away_game_level, bases_outs_table, times_facing_oppo_table
def get_pitching_tables(all_tables):
    totals_table = pd.DataFrame()
    totals_table_game_level = pd.DataFrame()
    platoon_table = pd.DataFrame()
    home_away_table = pd.DataFrame()
    home_away_table_game_level = pd.DataFrame()
    bases_outs_table = pd.DataFrame()
    times_facing_oppo_table = pd.DataFrame()
    days_rest_table = pd.DataFrame()
    for table in all_tables:
        actual_table = table[0] # Dataframes are placed in lists of length one.
        # Create filters for potential tables.
        possible_totals = actual_table.loc[actual_table["Split"] == YEAR + " Totals"]
        possible_platoon_rhp = actual_table.loc[actual_table["Split"] == "vs RHB"]
        possible_platoon_lhp = actual_table.loc[actual_table["Split"] == "vs LHB"]
        possible_home = actual_table.loc[actual_table["Split"] == "Home"]
        possible_away = actual_table.loc[actual_table["Split"] == "Away"]
        possible_bases_occupied_empty = actual_table.loc[actual_table["Split"] == "---"]
        possible_bases_occupied_men_on = actual_table.loc[actual_table["Split"] == "Men On"]
        possible_times_sp = actual_table.loc[actual_table["Split"] == "1st PA in G, as SP"]
        possible_times_rp = actual_table.loc[actual_table["Split"] == "1st PA in G, as RP"]
        possible_days_rest_table = actual_table.loc[actual_table["Split"] == "2 Days,GR"]
        temp_num = 3
        while temp_num < 6:
            possible_days_rest_table = actual_table.loc[actual_table["Split"] == str(temp_num) + " Days,GR"]
            temp_num += 1
            if not possible_days_rest_table.empty:
                break
        # Check to see whether those tables are what is needed.
        if not possible_totals.empty:
            totals_table = actual_table
            totals_table_game_level = table[1]
        elif not possible_platoon_rhp.empty or not possible_platoon_lhp.empty:
            platoon_table = actual_table
        elif not possible_home.empty or not possible_away.empty:
            home_away_table = actual_table
            home_away_table_game_level = table[1]
        elif not possible_bases_occupied_empty.empty or not possible_bases_occupied_men_on.empty:
            bases_outs_table = actual_table
        elif not possible_times_sp.empty or not possible_times_rp.empty:
            times_facing_oppo_table = actual_table
        elif not possible_days_rest_table.empty:
            days_rest_table = actual_table

    return [totals_table, totals_table_game_level, platoon_table, home_away_table,
            home_away_table_game_level, bases_outs_table, times_facing_oppo_table,
            days_rest_table]
