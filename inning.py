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
            if basepaths[2] == "3":
                runs_scored += 1
            basepaths = string_basepaths_converter("1" + basepaths[:2])
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
            pitcher_outs_hits_walks_runs[1] -= 1
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
            else:
                pitcher = ''
                index = 0
                for player in bullpen:
                    if player.available:
                        pitcher = bullpen.pop(index)
                        break
                    index += 1
                if not pitcher:
                    pitcher = bullpen.pop(0)
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
