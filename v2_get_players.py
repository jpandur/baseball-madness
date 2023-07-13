from v2_at_bat import *
from v2_other_factors import *

# Finds the lineups for the game based on the team name entered.
# Returns two lists, one for the away team and one for the home team.
# The first element of each list contains the team's abbreviation.
# The second element of each list contains the team's starting pitcher.
# The other list elements contain a batter's name, handedness, and position.
# Also returns two more lists that contain the handedness of batters.
def get_lineups(team):
    possible_urls = web(team + " starting lineups").pages
    url = find_url(possible_urls, "mlb.com")
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    time.sleep(random.uniform(2, 3))

    all_away_lineups = soup.find_all("ol", class_="starting-lineups__team--away")
    all_home_lineups = soup.find_all("ol", class_="starting-lineups__team--home")
    
    # Find batting roster for away and home players and place in a list
    today_away_lineup = all_away_lineups[0].text
    today_home_lineup = all_home_lineups[0].text
    away_list = [player for player in today_away_lineup.split("\n") if player]
    home_list = [player for player in today_home_lineup.split("\n") if player]

    # Get handedness of player lineup.
    away_batting_handedness, home_batting_handedness = [], []
    for player in away_list:
        away_batting_handedness += [player.split("(")[1][0]]
    for player in home_list:
        home_batting_handedness += [player.split("(")[1][0]]

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

    return away_list, home_list, away_batting_handedness, home_batting_handedness

# Given a team name, return a list of bullpen pitchers for that team,
# as well as the name of the closer.
def get_bullpen(team_name):
    possible_url = web("mlb " + team_name + " depth chart").pages
    url = find_url(possible_url, "mlb.com")
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    time.sleep(random.uniform(2, 3))
    html = soup.find_all("table", class_="roster__table")

    bullpen_table = pd.read_html(str(html))[1] # get bullpen roster from list of players
    bullpen_table = bullpen_table.drop(["Bullpen", "Ht", "Wt", "DOB"], axis=1)
    bullpen_table = bullpen_table.loc[~bullpen_table["Bullpen.1"].str.contains("IL-")] # Exclude IL
    bullpen_table = bullpen_table.loc[~bullpen_table["Bullpen.1"].str.contains("Minors")] # Exclude Minors
    bullpen_table = bullpen_table.reset_index(drop=True)
    relief_pitchers = []
    closer = ''
    is_closer = False

    for index in bullpen_table.index:
        if "(CL)" in bullpen_table.iloc[index]["Bullpen.1"]:
            is_closer = True
        split_list = bullpen_table.iloc[index]["Bullpen.1"].split()
        name = ''
        for item in split_list:
            if not item.isnumeric():
                name = name + item + " "
            else:
                name = name + "(" + bullpen_table.iloc[index]["B/T"][-1] + ")"
                if is_closer or name == closer:
                    closer = name
                    is_closer = False
                else:
                    relief_pitchers += [name]
                break
    return relief_pitchers, closer

# Given a list of bullpen pitchers, determine whether or not they can pitch today's
# game based on how many games they pitched in recent days.
def go_no_go_bullpen(bullpen, pitcher_dict): # FIX THIS BY GETTING DICT
    go = []
    no_go = []
    today = datetime.today().strftime('%Y-%m-%d')
    today = datetime.strptime(today, "%Y-%m-%d")

    for player in bullpen:
        recent_games = pitcher_dict[player][2] # Get last 5 game played log.
        if type(recent_games) != pd.core.frame.DataFrame:
            go += [player]
        # Check to see how many days have passed since each of last three outings.
        else:
            recent_games = recent_games[recent_games["Date"].notna()]
            date1 = datetime.strptime(recent_games.iloc[0]["Date"], "%Y-%m-%d")
            date2 = datetime.strptime(recent_games.iloc[-1]["Date"], "%Y-%m-%d")
            date3 = datetime.strptime(recent_games.iloc[2]["Date"], "%Y-%m-%d")
            
            diff1 = abs((today - date1).days)
            diff2 = abs((today - date2).days)
            diff3 = abs((today - date3).days)

            # Count number of games in last three days
            num_days = [diff1, diff2, diff3]
            if (1 in num_days and 2 in num_days) or [1, 2, 3] == num_days:
                no_go += [player]
            else:
                go += [player]

    return go, no_go

# Gets relevant tables for each player in batting lineup. Returns a dictionary
# where the key is the player name and the values are the tables in order of 
# [SPLITS, GAME LOG]. If no tables are found, value will be [[], []].
def get_batter_data(lineup, team_name):
    player_dictionary = {}
    for batter in lineup:
        stats_url, splits_url, game_log_url = stat_links(batter, "b", team_name)
        if splits_url == '' and game_log_url == '': # if no data on batter, give empty list
            player_dictionary[batter] = [[], []]
        else:
            splits_tables = get_splits_tables(splits_url)
            game_log_table = get_game_log_tables(game_log_url, "batting")
            player_dictionary[batter] = [splits_tables, game_log_table]
        print(batter + " added to batter dictionary.")
    return player_dictionary

# Get relevant tables for each pitcher. Returns a dictionary where key is pitcher
# name and values are the tables. If no tables are found, value will be [[], []].
# Index 0: splits tables  Index 1: game log table  Index 2: last 5 games table  Index 3: handedness
def get_pitcher_data(pitchers, team_name):
    player_dictionary = {}
    for pitcher_entry in pitchers:
        pitcher = pitcher_entry.split("(")[0][:-1] # Gets part before the open parenthesis
        handedness = pitcher_entry.split("(")[1][0]
        stats_url, splits_url, game_log_url = stat_links(pitcher, "p", team_name)
        if splits_url == '' or game_log_url == '': # if no data on pitcher, give empty lists plus handedness
            player_dictionary[pitcher_entry] = [[], [], [], handedness]
        else:
            splits_tables = get_splits_tables(splits_url)
            game_log_table = get_game_log_tables(game_log_url, "pitching")
            last_5_table = get_last5_table(stats_url)
            player_dictionary[pitcher_entry] = [splits_tables, game_log_table, last_5_table, handedness]
        print(pitcher_entry + " added to pitcher dictionary.")
    return player_dictionary
