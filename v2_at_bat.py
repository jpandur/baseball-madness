from datetime import datetime
from websearch import WebSearch as web
import requests
from bs4 import BeautifulSoup, Comment
import pandas as pd
import time
import random

from v2_other_factors import *

CURRENT_YEAR = str(datetime.now().year)

# Determines the result of an at-bat based on the situation (i.e. BASEPATHS and NUM_OUTS).
# Finds batter and pitcher data for this situation to make a prediction.
# Return value is a string describing the outcome.
# FRAME describes whether at-bat takes place during top or bottom of inning.
# LOCATION describes where the game is being played.
def at_bat(batter, pitcher, basepaths, num_outs, frame, location):
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

    # Get relevant tables for batter and pitcher if they exist.
    batter_splits_tables = get_splits_tables(batter_splits_url)
    time.sleep(random.uniform(1, 5))
    if batter_splits_tables == []:
        batter_splits_tables = [[[]] for _ in range(50)]

    pitcher_splits_tables = get_splits_tables(pitcher_splits_url)
    time.sleep(random.uniform(1, 5))
    if pitcher_splits_tables == []:
        pitcher_splits_tables = [[[]] for _ in range(50)]

    batter_game_log_table = get_game_log_tables(batter_game_log_url, "batting")
    time.sleep(random.uniform(1, 5))

    pitcher_game_log_table = get_game_log_tables(pitcher_game_log_url, "pitching")
    time.sleep(random.uniform(1, 5))

    # Item 1 for at-bat: how does batter and pitcher do with given basepaths and outs?
    item1_safe_b, item1_out_b = situational_bases_and_outs(batter_splits_tables[13][0], basepaths, num_outs)
    item1_safe_p, item1_out_p = situational_bases_and_outs(pitcher_splits_tables[14][0], basepaths, num_outs)
    b_item1, p_item1 = item_calculation(item1_safe_b, item1_out_b, item1_safe_p, item1_out_p)
    
    # Item 2 for at-bat: how does batter and pitcher do with given basepaths only?
    item2_safe_b, item2_out_b = situational_bases(batter_splits_tables[13][0], basepaths)
    item2_safe_p, item2_out_p = situational_bases(pitcher_splits_tables[14][0], basepaths)
    b_item2, p_item2 = item_calculation(item2_safe_b, item2_out_b, item2_safe_p, item2_out_p)

    # Item 3 for at-bat: how does batter and pitcher do with given outs only?
    item3_safe_b, item3_out_b = situational_outs(batter_splits_tables[12][0], num_outs)
    item3_safe_p, item3_out_p = situational_outs(pitcher_splits_tables[13][0], num_outs)
    b_item3, p_item3 = item_calculation(item3_safe_b, item3_out_b, item3_safe_p, item3_out_p)

    # Item 4 for at-bat: how has batter/pitcher been doing in last 20/5 games?
    item4_safe_b, item4_out_b = game_log_case(batter_game_log_table, 20, "b")
    item4_safe_p, item4_out_p = game_log_case(pitcher_game_log_table, 5, "p")
    b_item4, p_item4 = item_calculation(item4_safe_b, item4_out_b, item4_safe_p, item4_out_p)

    # Item 5 for at-bat: consider home/away stats for batter and pitcher.
    if frame == "top":
        item5_safe_b, item5_out_b = home_away_case(batter_splits_tables[2][0], "Away")
        item5_safe_p, item5_out_p = home_away_case(pitcher_splits_tables[2][0], "Home")
    else:
        item5_safe_b, item5_out_b = home_away_case(batter_splits_tables[2][0], "Home")
        item5_safe_p, item5_out_p = home_away_case(pitcher_splits_tables[2][0], "Away")
    b_item5, p_item5 = item_calculation(item5_safe_b, item5_out_b, item5_safe_p, item5_out_p)

    # Item 6 for at-bat: consider seasonal stats.
    item6_safe_b, item6_out_b = season_case(batter_splits_tables[0][0])
    item6_safe_p, item6_out_p = season_case(pitcher_splits_tables[0][0])
    b_item6, p_item6 = item_calculation(item6_safe_b, item6_out_b, item6_safe_p, item6_out_p)

    # Item 7 for at-bat: how batter and pitcher does against certain handedness.
    item7_safe_b, item7_out_b = handedness_case(batter_splits_tables[1][0], batter_handedness, pitcher_handedness, "b")
    item7_safe_p, item7_out_p = handedness_case(pitcher_splits_tables[1][0], batter_handedness, pitcher_handedness, "p")
    b_item7, p_item7 = item_calculation(item7_safe_b, item7_out_b, item7_safe_p, item7_out_p)
    
    # "Magic numbers" calculated based on above factors.
    batter_magic = magic_formula(b_item1, b_item2, b_item3, b_item4, b_item5, b_item6, b_item7)

    # Adjusts batter's safety rate based on where the game is being played.
    column_name = batter_handedness + "-OBP"
    obp_factor_adjustment = location[column_name]
    batter_magic *= obp_factor_adjustment

    return result(batter_magic, batter_splits_tables[0][0], pitcher_splits_tables[0][0], 
                  batter_handedness, location)

# Given a player name and a batter/pitcher classification (b/p), find relevant links to stats.
# Returns Fangraphs links to season stats, splits stats, game logs, and play logs.
def stat_links(name, classification):
    possible_urls = web(name + " baseball reference stats height weight " + CURRENT_YEAR).pages
    stats_url = find_url(possible_urls, "baseball-reference.com")
    time.sleep(random.uniform(1, 5))

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

# Given the number of times the batter reaches successfully and the pitcher records outs,
# return decimal fractions indicating the success rate for the batter and pitcher.
def item_calculation(batter_safe, batter_out, pitcher_safe, pitcher_out):
    if batter_safe + batter_out < 0 and pitcher_safe + pitcher_out < 0:
        return 0.5, 0.5
    elif batter_safe + batter_out < 0 or pitcher_safe + pitcher_out < 0:
        # In case there is no data for one player, use the number of situations that
        # the other player has been in to do the calculations.
        largest_sum = max(batter_safe + batter_out, pitcher_safe + pitcher_out)
        half = largest_sum // 2
        if batter_safe < 0:
            batter_safe, batter_out = half, half
        else:
            pitcher_safe, pitcher_out = half, half

    total = batter_safe + batter_out + pitcher_safe + pitcher_out
    return round((batter_safe + pitcher_safe) / total, 3), round((batter_out + pitcher_out) / total, 3)    

# Given a table with pertient information, the basepaths, and the number of outs,
# return the number of times safe and number of times out.
def situational_bases_and_outs(table, basepaths, num_outs):
    # Check if table is a valid table.
    if type(table) == pd.core.frame.DataFrame:
        table = table.fillna(0) # Replace NaN with 0's
        desired_row = table.loc[table["Split"] == num_outs + " out, " + basepaths]
        times_safe = (desired_row["H"].values + desired_row["BB"].values + desired_row["HBP"].values + desired_row["ROE"].values)[0]
        times_out = desired_row["PA"].values[0] - times_safe
        
        return int(times_safe), int(times_out)
    else:
        return -1, -1

# Given a table with pertient information and the basepaths, return the number
# of times safe and the number of times out.
def situational_bases(table, basepaths):
    # Check if table is a valid table.
    if type(table) == pd.core.frame.DataFrame:
        table = table.fillna(0) # Replace NaN with 0's
        desired_row = table.loc[table["Split"] == basepaths]
        times_safe = (desired_row["H"].values + desired_row["BB"].values + desired_row["HBP"].values + desired_row["ROE"].values)[0]
        times_out = desired_row["PA"].values[0] - times_safe
        
        return int(times_safe), int(times_out)
    else:
        return -1, -1

# Given a table with pertient information and the number of outs, return the number of
# times safe and the number of times out.
def situational_outs(table, num_outs):
    # Check if table is a valid table.
    if type(table) == pd.core.frame.DataFrame:
        table = table.fillna(0) # Replace NaN with 0's
        split_name = ''
        for name in table["Split"].values: # Used to find the correct row.
            if num_outs in name:
                split_name = name
                break
        desired_row = table.loc[table["Split"] == split_name]
        times_safe = (desired_row["H"].values + desired_row["BB"].values + desired_row["HBP"].values + desired_row["ROE"].values)[0]
        times_out = desired_row["PA"].values[0] - times_safe

        return int(times_safe), int(times_out)
    else:
        return -1, -1

# Given a game log table, the last number of games played, and classifier (b/p)
# return the number of times safe and the number of times out.
def game_log_case(table, num_games, classifier):
    if type(table) != pd.core.frame.DataFrame: # If table is empty
        return -1, -1
    table = table.drop(["Rk", "Gcar", "Gtm", "DFS(DK)", "DFS(FD)"], axis=1) # Drop unneeded columns
    table = table[table["Tm"] != "Tm"] # Get rid of rows that don't contain data.
    table = table[:-1] # Delete last row, which contains season data.
    table = table.fillna(0)

    considered_games = min(num_games, len(table.index)) # In case game log has less than NUM_GAMES
    start_index = len(table.index) - considered_games # Where we begin taking data
    recent_games_table = table[start_index:] # Get recent games
    recent_games_table = recent_games_table.reset_index() # Set such that first row has index 0
    times_safe = 0
    plate_appearances = 0
    for index in recent_games_table.index:
        if classifier == "b":
            plate_appearances += int(recent_games_table["PA"][index])
        else:
            plate_appearances += int(recent_games_table["BF"][index])
        times_safe = times_safe + int(recent_games_table["H"][index]) + int(recent_games_table["BB"][index]) + int(recent_games_table["HBP"][index]) + int(recent_games_table["ROE"][index])
    
    return times_safe, plate_appearances - times_safe

# Given a pertient table and whether or not player is home or away,
# return the number of times safe and the number of times out.
def home_away_case(table, location):
    if type(table) != pd.core.frame.DataFrame:
        return -1, -1
    desired_row = table.loc[table["Split"] == location]
    times_safe = (desired_row["H"].values + desired_row["BB"].values + desired_row["HBP"].values + desired_row["ROE"].values)[0]
    times_out = desired_row["PA"].values[0] - times_safe

    return int(times_safe), int(times_out)

# Given a pertient table on season stats, return the number of times safe and out.
def season_case(table):
    if type(table) != pd.core.frame.DataFrame:
        return -1, -1
    desired_row = table.loc[table["Split"] == CURRENT_YEAR + " Totals"]
    times_safe = (desired_row["H"].values + desired_row["BB"].values + desired_row["HBP"].values + desired_row["ROE"].values)[0]
    times_out = desired_row["PA"].values[0] - times_safe

    return int(times_safe), int(times_out)

# Given pertient table and handedness of batter and pitcher, return 
# the number of times safe and out.
def handedness_case(table, batter_handedness, pitcher_handedness, classifier):
    if type(table) != pd.core.frame.DataFrame:
        return -1, -1
    if classifier == "b":
        split_name = "vs " + pitcher_handedness + "HP as " + batter_handedness + "HB"
        desired_row = table.loc[table["Split"] == split_name]
    else:
        split_name = "vs " + batter_handedness + "HB as " + pitcher_handedness + "HP"
        desired_row = table.loc[table["Split"] == split_name]
    times_safe = (desired_row["H"].values + desired_row["BB"].values + desired_row["HBP"].values + desired_row["ROE"].values)[0]
    times_out = desired_row["PA"].values[0] - times_safe
    return int(times_safe), int(times_out)

# With the factors calculated in function at-bat, produce a "magic" percentage
# for player success rate.
def magic_formula(factor1, factor2, factor3, factor4, factor5, factor6, factor7):
    num = 0.25 * factor1 + 0.1 * factor2 + 0.1 * factor3 + 0.15 * factor4 + 0.1 * factor5 + 0.1 * factor6 + 0.2 * factor7
    return round(num, 3)

# Given the magic numbers of batter, return the result of the at-bat.
# Depending on who "wins", the batter's stat table or the pitcher's stat table
# will be used to determine the exact outcome.
def result(b_num, batter_table, pitcher_table, batter_handedness, location):
    result = random.uniform(0, 1)
    if result <= b_num:
        return safe_scenario(batter_table, location, batter_handedness)
    else:
        return out_scenario(pitcher_table, location, batter_handedness)

# Given batter statistics and where the game is played, determine the exact outcome.
def safe_scenario(table, location, handedness):
    if type(table) != pd.core.frame.DataFrame: # if no player data available, use league averages
        url = "https://www.baseball-reference.com/leagues/majors/bat.shtml"
        data = pd.read_html(url)[0]
        this_year = data.iloc[0]
        this_year = this_year.astype('float')
        total_safties = this_year["H"] + this_year["BB"]
        result = random.uniform(0, total_safties)
        
        if result <= this_year["1B"]:
            return "Single"
        elif result <= this_year["1B"] + this_year["2B"]:
            return "Double"
        elif result <= this_year["1B"] + this_year["2B"] + this_year["3B"]:
            return "Triple"
        elif result <= this_year["1B"] + this_year["2B"] + this_year["3B"] + this_year["HR"]:
            return "Home Run"
        else:
            return "Walk"

    desired_row = table.loc[table["Split"] == CURRENT_YEAR + " Totals"]
    times_safe = desired_row["H"][0] + desired_row["BB"][0] + desired_row["HBP"][0] + desired_row["ROE"][0]

    # Get different rates for different outcomes from batter's season data.
    singles_rate = (desired_row["H"][0] - desired_row["2B"][0] - desired_row["3B"][0] - desired_row["HR"][0]) / times_safe
    doubles_rate = desired_row["2B"][0] / times_safe
    triples_rate = desired_row["3B"][0] / times_safe
    home_run_rate = desired_row["HR"][0] / times_safe
    walk_rate = desired_row["BB"][0] / times_safe
    hbp_rate = desired_row["HBP"][0] / times_safe
    roe_rate = desired_row["ROE"][0] / times_safe

    # Adjust the hits and walk rates based on park.
    adjusted_singles = singles_rate * location[handedness + "-1B"]
    adjusted_doubles = doubles_rate * location[handedness + "-2B"]
    adjusted_triples = triples_rate * location[handedness + "-3B"]
    adjusted_home_runs = home_run_rate * location[handedness + "-HR"]
    adjusted_walks = walk_rate * location[handedness + "-BB"]

    adjusted_sum = adjusted_singles + adjusted_doubles + adjusted_triples + adjusted_home_runs + adjusted_walks + hbp_rate + roe_rate

    # Now, we can determine the final outcome with a bit of randomness.
    result = random.uniform(0, 1)
    if result <= adjusted_singles / adjusted_sum:
        return "Single"
    elif result <= (adjusted_singles + adjusted_doubles) / adjusted_sum:
        return "Double"
    elif result <= (adjusted_singles + adjusted_doubles + adjusted_triples) / adjusted_sum:
        return "Triple"
    elif result <= (adjusted_singles + adjusted_doubles + adjusted_triples + adjusted_home_runs) / adjusted_sum:
        return "Home Run"
    elif result <= (adjusted_singles + adjusted_doubles + adjusted_triples + adjusted_home_runs + adjusted_walks) / adjusted_sum:
        return "Walk"
    elif result <= (adjusted_singles + adjusted_doubles + adjusted_triples + adjusted_home_runs + adjusted_walks + hbp_rate) / adjusted_sum:
        return "HBP"
    else:
        return "ROE"

# Given pitcher statistics and where the game is played, determine the exact outcome.
def out_scenario(table, location, handedness):
    if type(table) != pd.core.frame.DataFrame:
        url = "https://www.baseball-reference.com/leagues/majors/bat.shtml"
        data = pd.read_html(url)[0]
        this_year = data.iloc[0]
        this_year = this_year.astype('float')

        strikeout_rate = this_year["SO"] / 27
        result = random.uniform(0, 1)
        if result <= strikeout_rate:
            print("SO PER GAME: ", this_year["SO"])
            return "Strikeout"
        return "Out"

    desired_row = table.loc[table["Split"] == CURRENT_YEAR + " Totals"]
    times_safe = desired_row["H"][0] + desired_row["BB"][0] + desired_row["HBP"][0] + desired_row["ROE"][0]
    times_out = desired_row["PA"][0] - times_safe

    strikeout_rate = desired_row["SO"][0] / times_out
    adjusted_strikeout_rate = strikeout_rate * location[handedness + "-SO"]

    result = random.uniform(0, 1)   
    if result <= adjusted_strikeout_rate:
        return "Strikeout"
    else:
        return "Out"

# Test Case
#print(at_bat("Fernando Tatis Jr. (R) RF", "Shohei Ohtani (R)", "---", "1", "bottom", park_factor("SDP")))