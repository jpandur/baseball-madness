from v2_at_bat import *
from v2_get_players import *
from v2_choose_reliever import *

# Represents one half-inning of play.
# BATTERS: batting lineup for away team
# BATTER_HANDEDNESS: list of batters' preferred hand
# BATTERS_DICT: dictionary of all batter data tables
# BOP: the starting batting order position (0-8 due to indexing)
# PITCHER: describes pitcher at start of inning (may change later in inning)
# GOOD_BULLPEN: list of available bullpen pitchers in form [[high_leverage], [low_leverage]]
# BAD_BULLPEN: list of unavailable bullpen pitchers to be used if good_bullpen is empty
# PITCHERS_DICT: dictionary of all pitcher data tables
# SCORE: list of length two that contains two elements [away score, home score]
# TOP_OR_BOTTOM: describes whether in top or bottom of inning
# LOCATION: a single-row DataFrame containing the ballpark's influence on amount of hits, walks, and strikeouts.
# WALKS_HITS_IP_DICT: contains dictionary of pitchers and their respective IP, BB+H, and R
# Returns the number of runs scored and the new batting order position.
def half_inning(batters, batter_handedness, batters_dict, bop, pitcher, good_bullpen, bad_bullpen, pitchers_dict,
                score, top_or_bottom, location, walks_hits_ip_dict):
    num_outs, added_runs, index = 0, 0, 0
    basepaths = "---"
    if top_or_bottom == "bottom": # index used to update score list accordingly
        index = 1
    # Account for difference in score here when changing pitchers.
    while num_outs < 3:
        at_bat_result = at_bat(batters[bop], batter_handedness[bop], batters_dict, pitcher, pitchers_dict, basepaths, str(num_outs), top_or_bottom, location)
        print(batters[bop] + " versus " + pitcher + ": " + at_bat_result)
        if at_bat_result == "Out" or at_bat_result == "Strikeout": # Covers out scenarios.
            num_outs += 1
            # Update number of innings remaining
            walks_hits_ip_dict[pitcher][0] -= 1
            if at_bat_result != "Strikeout":
                type_of_out = random.uniform(0, 1) # determine whether groundout or air out
                if type_of_out <= 0.5 and num_outs < 3: # ground out scenario
                    if basepaths[0] == "1": # assess chance of GIDP
                        if random.uniform(0, 1) <= 0.05: # GIDP rate ~5%
                            basepaths = "-" + basepaths[1:]
                            num_outs += 1
                            walks_hits_ip_dict[pitcher][0] -= 1
                else: # air out scenario
                    if basepaths[2] == "3" and num_outs < 3: # sacrifice fly scenario
                        if random.uniform(0, 1) <= 0.02: # Sac fly rate ~2%
                            basepaths = basepaths[0:2] + "-"
                            added_runs += 1
                            walks_hits_ip_dict[pitcher][2] -= 1
        else: # Covers hit, walk, hbp, roe scenarios.
            walks_hits_ip_dict[pitcher][1] -= 1
            if at_bat_result == "Single" or at_bat_result == "ROE":
                if basepaths[2] == "3":
                    added_runs += 1
                    walks_hits_ip_dict[pitcher][2] -= 1
                basepaths = "1" + basepaths[0] + basepaths[1]
                basepaths = string_basepaths_converter(basepaths)
                if at_bat_result == "ROE":
                    walks_hits_ip_dict[pitcher][1] += 1
            elif at_bat_result == "Double":
                more_runs = men_on_base_counter(basepaths, 1) # Parenthesis term counts people on 2nd and 3rd
                added_runs += more_runs
                walks_hits_ip_dict[pitcher][2] -= more_runs
                basepaths = "-2" + basepaths[0]
                basepaths = string_basepaths_converter(basepaths)
            elif at_bat_result == "Triple":
                more_runs = men_on_base_counter(basepaths, 0) # Determines num people on base
                added_runs += more_runs
                walks_hits_ip_dict[pitcher][2] -= more_runs
                basepaths = "--3"
            elif at_bat_result == "Home Run":
                more_runs = 1 + men_on_base_counter(basepaths, 0)
                added_runs += more_runs
                walks_hits_ip_dict[pitcher][2] -= more_runs
                basepaths = "---"
            else: # case of HBP or Walk
                if at_bat_result == "HBP":
                    walks_hits_ip_dict[pitcher][1] += 1
                if basepaths == "123":
                    added_runs += 1
                    walks_hits_ip_dict[pitcher][2] -= 1
                elif basepaths == "-2-" or basepaths == "--3":
                    basepaths = "1" + basepaths[1:]
                elif basepaths == "1-3" or basepaths == "-23" or basepaths == "12-":
                    basepaths = "123"
                else: # case where basepaths == "1--" or "---"
                    basepaths = "1" + basepaths[0] + basepaths[1]
                    basepaths = string_basepaths_converter(basepaths)
        
        print("Basepaths", basepaths)
        print(walks_hits_ip_dict[pitcher])
        print("Added Runs:", added_runs)

        if bop == 8: # adjust batting order position after at-bat
            bop = 0
        else:
            bop += 1

        # In case pitcher needs to be replaced after having given up a certain number of runs, hits, and/or walks, or IP.
        if (walks_hits_ip_dict[pitcher][0] < 0 and walks_hits_ip_dict[pitcher][1] < 0) or (walks_hits_ip_dict[pitcher][1] < 0 and walks_hits_ip_dict[pitcher][2] < 0):
            temp_index = bop
            next_three_batters = [batter_handedness[temp_index], batter_handedness[(temp_index + 1) % 9], batter_handedness[(temp_index + 2) % 9]]
            if good_bullpen[0] != []: # if there are still good relievers
                pitcher = replace_pitcher(good_bullpen[0], basepaths, num_outs, next_three_batters, pitchers_dict)
                good_bullpen[0].remove(pitcher)
            elif good_bullpen[0] == []: # if we have to turn to the bad available relievers
                pitcher = replace_pitcher(good_bullpen[1], basepaths, num_outs, next_three_batters, pitchers_dict)
                good_bullpen[1].remove(pitcher)
            else: # have to resort to bad bullpen (i.e. the formerly unavailable pitchers)
                pitcher = replace_pitcher(bad_bullpen, basepaths, num_outs, next_three_batters, pitchers_dict)
                bad_bullpen.remove(pitcher)
            print(pitcher + " is now the new pitcher!")

    score[index] += added_runs
    print("Runs Scored:", added_runs)
    print("Away Team Score: ", score[0])
    print("Home Team Score: ", score[1])
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

# Counts number of people on base.
def men_on_base_counter(basepaths, start_index):
    num = 0
    while start_index < 3:
        if basepaths[start_index] == str(start_index + 1):
            num += 1
        start_index += 1
    return num