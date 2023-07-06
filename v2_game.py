from datetime import datetime
from websearch import WebSearch as web

# Determines the result of an at-bat based on the situation (i.e. BASEPATHS and NUM_OUTS)
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
    
    current_year = str(datetime.now().year)

    # Stat check the batter
    print(batter_name + " batting stats fangraphs " + current_year)
    possible_urls = web(batter_name + " batting stats fangraphs " + current_year).pages
    url = find_url(possible_urls, "fangraphs.com")
    # TODO: Fix modification of the url to get the splits url
    splits_url = url + "splits?position=" + batter_position + "&season=" + current_year
    print(splits_url)

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

at_bat("Mike Trout (R) CF", "Lance Lynn (R)", "___", 1)
