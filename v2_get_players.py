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
    time.sleep(random.uniform(1, 5))

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

# Given a team abbreviation, return a list of bullpen pitchers for that team,
# as well as the name of the closer.
def get_bullpen(team_abbreviation):
    possible_url = web("mlb " + team_abbreviation + " depth chart").pages
    url = find_url(possible_url, "mlb.com")
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    time.sleep(random.randint(1, 5))
    html = soup.find_all("table", class_="roster__table")

    bullpen_table = pd.read_html(str(html))[1] # get bullpen roster from list of players
    bullpen_table = bullpen_table.drop(["Bullpen", "B/T", "Ht", "Wt", "DOB"], axis=1)
    bullpen_table = bullpen_table.loc[~bullpen_table["Bullpen.1"].str.contains("IL-")] # Exclude IL
    relief_pitchers = []
    closer = ''
    for item in bullpen_table["Bullpen.1"]: # Loop through each element to get name only.
        if "(CL)" in item:
            closer = item
        else:
            split_list = item.split()
            name = ''
            for item in split_list:
                if not item.isnumeric():
                    name = name + item + " "
                else:
                    name = name[:-1]
                    relief_pitchers += [name]
                    break
    return relief_pitchers, closer

# Given a list of bullpen pitchers, determine whether or not they can pitch today's
# game based on how many games they pitched in recent days.
def go_no_go_bullpen(bullpen):
    go = []
    no_go = []
    today = datetime.today().strftime('%Y-%m-%d')
    today = datetime.strptime(today, "%Y-%m-%d")

    for player in bullpen:
        possible_urls = web(player + " bref stats height weight position").pages
        url = find_url(possible_urls, "baseball-reference")
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        time.sleep(random.uniform(1, 5))
        html = soup.find_all("table", id="last5")

        if html == []:
            go += [player]
        else: # Check to see how many days have passed since each of last three outings.
            recent_games = pd.read_html(str(html))[0]
            date1 = datetime.strptime(recent_games.iloc[0]["Date"], "%Y-%m-%d")
            date2 = datetime.strptime(recent_games.iloc[1]["Date"], "%Y-%m-%d")
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
