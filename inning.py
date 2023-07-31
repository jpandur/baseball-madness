from at_bat import *

# PITCHER_OUTS_HITS_WALKS_RUNS keeps track of the pitcher's remaining outs, walks plus hits, and runs.
# Return the number of runs scored, the batting order position (bop) for the next inning,
# the current pitcher, the amount of hits, walks, and runs pitcher can give up, and the bullpen.
def half_inning(score, half_inning_number, batters, bop, pitcher, pitcher_outs_hits_walks_runs,
                 bullpen, factors_list):
    num_outs, runs_scored = 0, 0
    basepaths = "---"
    walkoff = False
    if half_inning_number > 18:
        basepaths = "-2-"
    if half_inning_number >= 18 and half_inning_number % 2 == 0:
        walkoff = True

    if walkoff and score[1] > score[0]: # in case team is leading in bottom of 9th
        return score, bop, pitcher, pitcher_outs_hits_walks_runs, bullpen

    while num_outs < 3:
        if half_inning_number % 2 == 1:
            at_bat_result =  at_bat(batters[bop], pitcher, basepaths, num_outs, "top", factors_list)
        else:
            at_bat_result =  at_bat(batters[bop], pitcher, basepaths, num_outs, "bottom", factors_list)
        print(batters[bop].name + " versus " + pitcher.name + ": " + at_bat_result)

        # Adjust runs scored, basepaths, and/or number of outs based on at-bat result.
        if at_bat_result == "Single" or at_bat_result == "ROE":
            if basepaths[2] == "3":
                runs_scored += 1
            basepaths = string_basepaths_converter("1" + basepaths[:2])
            basepaths, added_run = extra_bases_taken(basepaths, 1)
            runs_scored += added_run
        elif at_bat_result == "Walk" or at_bat_result == "HBP":
            if basepaths == "123":
                runs_scored += 1
            elif basepaths == "-23" or basepaths == "1-3" or basepaths == "12-":
                basepaths = "123"
            elif basepaths == "1--" or basepaths == "-2-":
                basepaths = "12-"
            elif basepaths == "--3":
                basepaths = "1-3"
            elif basepaths == "---":
                basepaths = "1--"
        elif at_bat_result == "Double":
            if basepaths[1] == "2":
                runs_scored += 1
            if basepaths[2] == "3":
                runs_scored += 1
            basepaths = string_basepaths_converter("-2" + basepaths[2])
            basepaths, added_run = extra_bases_taken(basepaths, 2)
            runs_scored += added_run
        elif at_bat_result == "Triple":
            if basepaths[0] == "1":
                runs_scored += 1
            if basepaths[1] == "2":
                runs_scored += 1
            if basepaths[2] == "3":
                runs_scored += 1
            basepaths = "--3"
        elif at_bat_result == "Home Run":
            if basepaths[0] == "1":
                runs_scored += 1
            if basepaths[1] == "2":
                runs_scored += 1
            if basepaths[2] == "3":
                runs_scored += 1
            runs_scored += 1
            basepaths = "---"
        elif at_bat_result == "Out":
            num_outs += 1
        elif at_bat_result == "GIDP":
            num_outs += 2
            if num_outs < 3:
                if basepaths == "123" or basepaths == "1-3":
                    runs_scored += 1
                    basepaths = "--3"
                else:
                    basepaths = string_basepaths_converter("--" + basepaths[1])
            else:
                basepaths = "---"
        elif at_bat_result == "Sacrifice Fly":
            num_outs += 1
            runs_scored += 1
            basepaths = basepaths[:2] + "-"
            
        # Adjust the amount of outs, walks plus hits, runs that pitcher can give up.
        if at_bat_result == "Out" or at_bat_result == "Sacrifice Fly":
            pitcher_outs_hits_walks_runs[0] -= 1
        elif at_bat_result == "GIDP":
            pitcher_outs_hits_walks_runs[0] -= 2
        else:
            pitcher_outs_hits_walks_runs[1] -= 1 # reduce hits/walks by one
        pitcher_outs_hits_walks_runs[2] -= runs_scored
        print(pitcher_outs_hits_walks_runs)

        if half_inning_number % 2 == 1:
            score[0] += runs_scored
        else:
            score[1] += runs_scored
        if score[1] > score[0] and walkoff:
            break

        print("Basepaths", basepaths)
        if bop == 8:
            bop = 0
        else:
            bop += 1

        runs_scored = 0 # reset runs scored after each batter

        # Change pitchers if current pitcher exceeds limits.
        if pitcher_outs_hits_walks_runs[0] == 0 or pitcher_outs_hits_walks_runs[1] == 0 or pitcher_outs_hits_walks_runs[2] < 0:
            for batter in batters: # reset number of times batter has faced pitcher
                batter.times_faced_pitcher = 0
            if len(bullpen) == 0: # bring in default reliever if bullpen is empty
                pitcher = Pitcher("Average Joe", [pd.DataFrame() for _ in range(7)], "R", "RP")
            elif num_outs == 3 or (num_outs == 0 and basepaths == "---") or (half_inning_number > 18 and num_outs == 0 and basepaths == "-2-"):
                pitcher = ''
                index = 0
                for player in bullpen:
                    if player.available:
                        pitcher = bullpen.pop(index)
                        break
                    index += 1
                if not pitcher:
                    pitcher = bullpen.pop(0)
            else:
                num_next_batters = 3 - num_outs
                handedness_list = []
                for i in range(num_next_batters):
                    handedness_list += [batters[(bop + i) % 9].handedness]
                best_pitcher = pick_next_reliever(bullpen, basepaths, str(num_outs), handedness_list)
                pitcher = bullpen.pop(bullpen.index(best_pitcher))
            pitcher_outs_hits_walks_runs = pitcher.max_innings_walks_hits_runs()
            print(pitcher.name + " is the new pitcher!")

    return score, bop, pitcher, pitcher_outs_hits_walks_runs, bullpen

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

# Gives an opportunity for extra bases to be taken.
def extra_bases_taken(basepaths, start_index):
    added_runs = 0
    if basepaths[2] == "3":
        if random.uniform(0, 1) >= 0.55:
            basepaths = basepaths[:2] + "-"
            added_runs += 1
    if start_index == 1:
        if basepaths[1] == "2" and basepaths[2] == "-":
            if random.uniform(0, 1) >= 0.55:
                basepaths = basepaths[0] + "-3"
    return basepaths, added_runs

# Given the next batters' handedness, the available bullpen pitchers, the basepaths,
# and the number of outs, pick the best reliever.
def pick_next_reliever(bullpen, bases, outs, batter_handedness):
    # Determine the desired handedness of the relief pitcher based on next batter(s).
    hands_count = 0
    desired_handedness = ''
    for hand in batter_handedness:
        if hand == "R":
            hands_count += 1
        else:
            hands_count -= 1
    if hands_count > 0:
        desired_handedness = "R"
    else:
        desired_handedness = "L"

    rankings_list = [] # Create ranking system based on basepaths and outs and platoon.
    for pitcher in bullpen:
        platoon_score, basepaths_outs_score = 0, 0
        if not pitcher.platoon_table.empty:
            platoon_row = pitcher.platoon_table.loc[pitcher.platoon_table["Split"] == "vs " + desired_handedness + "HB"]
            platoon_row = platoon_row.reset_index(drop=True)
            if not platoon_row.empty:
                try:
                    platoon_score = float(platoon_row.loc[0, "PA"]) / float(platoon_row.loc[0, "OBP"])
                except:
                    platoon_score = float(platoon_row.loc[0, "PA"]) / .248
                    print(pitcher.name, platoon_score)
                    print(platoon_row)
            else:
                print(pitcher.name, "does not have a platoon row to analyze")

        if not pitcher.bases_outs_table.empty:
            basepaths_outs_row = pitcher.bases_outs_table.loc[pitcher.bases_outs_table["Split"] == outs + " out, " + bases]
            basepaths_outs_row = basepaths_outs_row.reset_index(drop=True)
            if not basepaths_outs_row.empty:
                try:
                    basepaths_outs_score = float(basepaths_outs_row.loc[0, "PA"]) / float(basepaths_outs_row.loc[0, "OBP"])
                except:
                    basepaths_outs_score = float(basepaths_outs_row.loc[0, "PA"]) / .248
                    print(pitcher.name, basepaths_outs_score)
                    print(basepaths_outs_row)
            else:
                print(pitcher.name, "does not have a row for", bases, "and", outs, "outs")       
        
        rankings_list += [(pitcher, platoon_score + basepaths_outs_score)]

    # Based on above calculations, return the best pitcher available.    
    rankings_list = sorted(rankings_list, key=lambda x: x[1], reverse=True)
    best_pitcher = ''
    for element in rankings_list:
        pitcher = element[0]
        if pitcher.available and element[1] > 0:
            best_pitcher = pitcher # pitcher has to be available, have the appropriate handedness, and must have faced this situation before
            break
    if not best_pitcher:
        best_pitcher = bullpen[0]
    return best_pitcher