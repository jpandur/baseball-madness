

from v2_at_bat import *
from v2_get_players import *

# Represents one half-inning of play. Parameters are list of batters, the pitcher,
# available and unavailable bullpen pitchers for pitching team, the current batting
# order position (0-8), whether currently in top or bottom of frame, location, and
# the number of walks and hits and runs the pitcher has given up so far.
# Returns the number of runs scored and the new batting order position.
def half_inning(batters, pitcher, good_bullpen, bad_bullpen, bop, top_or_bottom, location, walks_and_hits, runs):
    num_outs, runs_scored = 0, 0
    basepaths = "---"
    while num_outs < 3:
        at_bat_result = at_bat(batters[bop], pitcher, num_outs, top_or_bottom, location)
        if at_bat_result == "Out" or at_bat_result == "Strikeout":
            num_outs += 1
    return # runs scored. bullpen availability, number of walks and hits given up,

# Determines, on average, how many innings pitcher throws and how many walks
# and hits they give up. CLASSIFIER indicates whether pitcher is starter (SP) or reliever (RP).
def max_innings_and_walks_plus_hits(pitcher, classifier):
    innings = 0
    walks_and_hits = 0
    stats_url, splits_url, game_log_url = stat_links(pitcher, "p")
    if splits_url != '' and game_log_url != '':
        splits_data = get_splits_tables(splits_url)[0][1]
        game_log_data = get_game_log_tables(game_log_url, "pitching")
        
        # Get season averages for innings and walks + hits.
        season_data = splits_data.loc[splits_data["Split"] == CURRENT_YEAR + " Totals"]
        season_innings = str(season_data["IP"][0]).split(".")
        season_innings = round(float(season_innings[0]) + float(season_innings[1]) / 3, 3)
        season_walks_hits = season_data["H"][0] + season_data["BB"][0]
        season_games = season_data["G"][0]
        season_avg_innings = season_innings / season_games
        season_avg_walks_hits = season_walks_hits / season_games
        
        # Get recent averages for innings and walks + hits.
    else:
        if classifier == "SP":
            return 5, 8
        else:
            return 1, 4
    return innings, walks_and_hits

max_innings_and_walks_plus_hits("Nestor Cortes", "SP")

# Runs a simulated game given two teams.
# Returns the number of runs each team scores.
def game(away_team, home_team):
    away_bullpen, home_bullpen = get_bullpen(away_team[0]), get_bullpen(home_team[0])
    away_bullpen_go, away_bullpen_no_go = go_no_go_bullpen(away_bullpen)
    home_bullpen_go, home_bullpen_no_go = go_no_go_bullpen(home_bullpen)

    away_starter = away_team[1]
    home_starter = home_team[1]

    away_batting = away_team[2:]
    home_batting = home_team[2:]
    away_bop, home_bop = 0, 0 # Batting order position for each team.
    away_runs, home_runs = 0, 0
    half_innings_played = 0
    

    while half_innings_played < 18 or away_runs == home_runs:
        if half_innings_played % 2 == 0:
            print("TOP OF INNING ", half_innings_played / 2 + 1)
            runs_scored += half_inning # need runs scored, current bullpen, hits + walks pitcher gave up
        else:
            print("BOTTOM OF INNING ", half_innings_played // 2 + 1)
            runs_scored += half_inning
        half_innings_played += 1