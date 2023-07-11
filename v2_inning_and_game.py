from v2_at_bat import *
from v2_get_players import *
from v2_choose_reliever import *

# Represents one half-inning of play.
# BATTERS: batting lineup for away team
# BATTER_HANDEDNESS: list of batters' preferred hand
# BOP: the starting batting order position (0-8 due to indexing)
# PITCHER: describes pitcher at start of inning (may change later in inning)
# GOOD_BULLPEN: list of available bullpen pitchers in form [[high_leverage], [low_leverage]]
# BAD_BULLPEN: list of unavailable bullpen pitchers to be used if good_bullpen is empty
# SCORE: list of length two that contains two elements [away score, home score]
# TOP_OR_BOTTOM: describes whether in top or bottom of inning
# LOCATION: a single-row DataFrame containing the ballpark's influence on amount of hits, walks, and strikeouts.
# WALKS_HITS_IP_DICT: contains dictionary of pitchers and their respective IP, BB+H, and R
# Returns the number of runs scored and the new batting order position.
def half_inning(batters, batter_handedness, bop, pitcher, good_bullpen, bad_bullpen, score,
                top_or_bottom, location, walks_hits_ip_dict):
    num_outs = 0
    basepaths = "---"
    if top_or_bottom == "top": # index used to update score list accordingly
        index = 0
    else:
        index = 1
    # Account for difference in score here when changing pitchers.
    while num_outs < 3:
        at_bat_result = at_bat(batters[bop], pitcher, num_outs, top_or_bottom, location)
        print(batters[bop] + " versus " + pitcher + ": " + at_bat_result)
        if at_bat_result == "Out" or at_bat_result == "Strikeout": # Covers out scenarios.
            num_outs += 1
            # Update number of innings remaining
            new_innings = float(walks_hits_ip_dict[pitcher][0]) - 1.0 / 3.0
            walks_hits_ip_dict[pitcher][0] = round(new_innings, 3)
            if at_bat_result != "Strikeout":
                type_of_out = random.uniform(0, 1) # determine whether groundout or air out
                if type_of_out <= 0.5 and num_outs < 3: # ground out scenario
                    if basepaths[0] == "1": # assess chance of GIDP
                        if random.uniform(0, 1) <= 0.05: # GIDP rate ~5%
                            basepaths = "-" + basepaths[1:]
                            num_outs += 1
                            new_innings = float(walks_hits_ip_dict[pitcher][0]) - 1.0 / 3.0
                            walks_hits_ip_dict[pitcher][0] = round(new_innings, 3)
                else: # air out scenario
                    if basepaths[2] == "3" and num_outs < 3: # sacrifice fly scenario
                        if random.uniform(0, 1) <= 0.02: # Sac fly rate ~2%
                            basepaths = basepaths[0:2] + "-"
                            score[index] += 1
                            walks_hits_ip_dict[pitcher][2] -= 1
        else: # Covers hit, walk, hbp, roe scenarios.
            walks_hits_ip_dict[pitcher][1] -= 1
            if at_bat_result == "Single" or at_bat_result == "ROE":
                if basepaths[2] == "3":
                    score[index] += 1
                    walks_hits_ip_dict[pitcher][2] -= 1
                basepaths = "1" + basepaths[0] + basepaths[1]
                basepaths = string_basepaths_converter(basepaths)
                if at_bat_result == "ROE":
                    walks_hits_ip_dict[pitcher] += 1
            elif at_bat_result == "Double":
                added_runs = 2 - basepaths[1:].count("-") # Parenthesis term counts people on 2nd and 3rd
                score[index] += added_runs
                walks_hits_ip_dict[pitcher][2] -= added_runs
                basepaths = "-2" + basepaths[0]
                basepaths = string_basepaths_converter(basepaths)
            elif at_bat_result == "Triple":
                added_runs = 3 - basepaths.count("-") # Determines num people on base
                score[index] += added_runs
                walks_hits_ip_dict[pitcher][2] -= added_runs
                basepaths = "--3"
            elif at_bat == "Home Run":
                added_runs = 4 - basepaths.count("-")
                score[index] += added_runs
                walks_hits_ip_dict[pitcher][2] -= added_runs
                basepaths = "---"
            else: # case of HBP or Walk
                if at_bat_result == "HBP":
                    walks_hits_ip_dict[pitcher][1] += 1
                if basepaths == "123":
                    score[index] += 1
                    walks_hits_ip_dict[pitcher][2] -= 1
                elif basepaths == "-2-" or basepaths == "--3":
                    basepaths = "1" + basepaths[1:]
                elif basepaths == "1-3" or basepaths == "-23" or basepaths == "12-":
                    basepaths = "123"
                else: # case where basepaths == "1--" or "---"
                    basepaths = "1" + basepaths[0] + basepaths[1]
                    basepaths = string_basepaths_converter(basepaths)
        
        print(basepaths)
        print(walks_hits_ip_dict[pitcher])
        print("Away Team Score: ", score[0])
        print("Home Team Score: ", score[1])

        if bop == 8: # adjust batting order position after at-bat
            bop = 0
        else:
            bop += 1

        # In case pitcher needs to be replaced after having given up a certain number of runs, hits, and/or walks, or IP.
        if walks_hits_ip_dict[pitcher][0] <= 0 or walks_hits_ip_dict[pitcher][1] <= 0 or walks_hits_ip_dict[pitcher][2] <= 0:
            temp_index = bop
            next_three_batters = [batter_handedness[temp_index], batter_handedness[(temp_index + 1) % 9], batter_handedness[(temp_index + 2) % 9]]
            if good_bullpen[0] != []: # if there are still good relievers
                pitcher = replace_pitcher(good_bullpen[0], basepaths, num_outs, next_three_batters)
                good_bullpen[0].remove(pitcher)
            elif good_bullpen[0] == []: # if we have to turn to the bad available relievers
                pitcher = replace_pitcher(good_bullpen[1], basepaths, num_outs, next_three_batters)
                good_bullpen[1].remove(pitcher)
            else: # have to resort to bad bullpen (i.e. the formerly unavailable pitchers)
                pitcher = replace_pitcher(bad_bullpen, basepaths, num_outs, next_three_batters)
                bad_bullpen.remove(pitcher)
            print(pitcher + " is now the new pitcher!")
        walks_hits_ip_dict[pitcher] = max_innings_and_walks_plus_hits_and_runs(pitcher, "RP") # Add relief pitcher to dictionary

    # Return the score list, remaining members of the good and bad bullpen, the pitcher who finished the inning,
    # the walks_hits_ip_dict (also keeps track of runs), and the current batting order position for the batting team.
    return score, good_bullpen, bad_bullpen, pitcher, walks_hits_ip_dict, bop 

# Given a basepaths in the form of dashes and asterisks (e.g. *-*), convert
# asterisks to numbers 1, 2, or 3.
def string_basepaths_converter(basepaths):
    new_basepaths = ""
    if basepaths[0] != "-":
        new_basepaths += "1"
    else:
        new_basepaths += "-"

    if basepaths[1] != "-":
        new_basepaths += "2"
    else:
        new_basepaths += "-"

    if basepaths[2] != "-":
        new_basepaths += "3"
    else:
        new_basepaths += "-"

    return new_basepaths

# Runs a simulated game given two teams.
# Returns the number of runs each team scores.
def game(away_team, home_team, away_batting_handedness, home_batting_handedness):
    away_bullpen, away_closer = get_bullpen(away_team[0])
    home_bullpen, home_closer = get_bullpen(home_team[0])
    away_bullpen_go, away_bullpen_no_go = go_no_go_bullpen(away_bullpen)
    home_bullpen_go, home_bullpen_no_go = go_no_go_bullpen(home_bullpen)
    # Subdivide available bullpens and place in bullpen_go lists.
    away_bullpen_high_leverage, away_bullpen_low_leverage = leverage_determiner(away_bullpen_go)
    home_bullpen_high_leverage, home_bullpen_low_leverage = leverage_determiner(home_bullpen_go)
    away_bullpen_go = [away_bullpen_high_leverage, away_bullpen_low_leverage]
    home_bullpen_go = [home_bullpen_high_leverage, home_bullpen_low_leverage]

    away_pitcher = away_team[1] # initially set to away starter
    home_pitcher = home_team[1] # initially set to home starter

    # Keeps track of the maximum number of walks plus hits and innings for each pitcher.
    walks_hits_innings_runs_dict = {away_pitcher: max_innings_and_walks_plus_hits_and_runs(away_pitcher, "SP"),
            home_pitcher: max_innings_and_walks_plus_hits_and_runs(home_pitcher, "SP")}

    away_batting = away_team[2:]
    home_batting = home_team[2:]
    away_bop, home_bop = 0, 0 # Batting order position for each team.
    location = park_factor(home_team[0]) # Get location of ballgame
    score = [0, 0] # first element for away, second for home
    half_innings_played = 0

    while half_innings_played < 18 or score[0] == score[1]:
        if half_innings_played % 2 == 0: # Top of inning, away bats and home pitches
            print("TOP OF INNING ", half_innings_played / 2 + 1)
            if half_innings_played == 16:
                if score[1] - score[0] >= 0 and score[1] - score[0] <= 3: # if tied or home team up by at most 3 runs, use closer
                    score, home_bullpen_go, home_bullpen_no_go, home_pitcher, walks_hits_innings_runs_dict, away_bop = half_inning(away_batting,
                            away_batting_handedness, away_bop, home_closer, home_bullpen_go, home_bullpen_no_go, score, "top", location, walks_hits_innings_runs_dict)
                else:
                    score, home_bullpen_go, home_bullpen_no_go, home_pitcher, walks_hits_innings_runs_dict, away_bop = half_inning(away_batting,
                            away_batting_handedness, away_bop, home_pitcher, home_bullpen_go, home_bullpen_no_go, score, "top", location, walks_hits_innings_runs_dict)
            else:
                score, home_bullpen_go, home_bullpen_no_go, home_pitcher, walks_hits_innings_runs_dict, away_bop = half_inning(away_batting,
                            away_batting_handedness, away_bop, home_pitcher, home_bullpen_go, home_bullpen_no_go, score, "top", location, walks_hits_innings_runs_dict)
        else: # Bottom of inning, home bats and away pitches
            print("BOTTOM OF INNING ", half_innings_played // 2 + 1)
            if half_innings_played == 17:
                if score[1] > score[0]: # If home team is winning following the top of the 9th, game is over
                    break
                if score[0] - score[1] >= 0 and score[0] - score[1] <= 3: # if tied or away team up by at most 3 runs, use closer
                    score, away_bullpen_go, away_bullpen_no_go, away_pitcher, walks_hits_innings_runs_dict, home_bop = half_inning(home_batting,
                            home_batting_handedness, home_bop, away_closer, away_bullpen_go, away_bullpen_no_go, score, "bottom", location, walks_hits_innings_runs_dict)
                else:
                    score, away_bullpen_go, away_bullpen_no_go, away_pitcher, walks_hits_innings_runs_dict, home_bop = half_inning(home_batting,
                            home_batting_handedness, home_bop, away_pitcher, away_bullpen_go, away_bullpen_no_go, score, "bottom", location, walks_hits_innings_runs_dict)
            else:
                score, away_bullpen_go, away_bullpen_no_go, away_pitcher, walks_hits_innings_runs_dict, home_bop = half_inning(home_batting,
                            home_batting_handedness, home_bop, away_pitcher, away_bullpen_go, away_bullpen_no_go, score, "bottom", location, walks_hits_innings_runs_dict)
        half_innings_played += 1

    return score
