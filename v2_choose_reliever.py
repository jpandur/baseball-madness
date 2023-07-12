from v2_other_factors import *

# Given list of available bullpen pitchers and current situation, return the name
# of the relief pitcher best suited for the situation.
# NEXT_BATTERS_HANDEDNESS describes the handedness of next three batters in list.
def replace_pitcher(bullpen, basepaths, num_outs, next_batters_handedness, pitcher_dict):
    rankings = [] # To store "scores" for each pitcher based on scenario
    handedness = 0 # Determines majority handedness of next three batters.
    for elem in next_batters_handedness:
        if elem == "R":
            handedness += 1
        else:
            handedness -= 1
    if handedness > 0:
        handedness = "R"
    else:
        handedness = "L"
    
    # Calculate effectiveness of each pitcher and update rankings list.
    for pitcher in bullpen:
        splits_tables = pitcher_dict[pitcher][0]
        if type(splits_tables) != pd.core.frame.DataFrame:
            rankings += [(pitcher, .09)]
        else:
            # Get relevant tables for handedness, number of outs, and bases occupied.
            handedness_table = splits_tables[1][0]
            num_outs_table = splits_tables[12][0]
            bases_and_outs_table = splits_tables[13][0]
            situation_score = 0

            handedness_row = handedness_table.loc[handedness_table["Split"] == "vs " + handedness + "HB"]
            num_outs_row = num_outs_table.loc[num_outs_table["Split"].str.contains(str(num_outs) + " out")]
            bases_and_outs_row = bases_and_outs_table.loc[bases_and_outs_table["Split"] == str(num_outs) + " out, " + basepaths]
            for row in [handedness_row, num_outs_row, bases_and_outs_row]:
                row = row.reset_index(drop=True)
                try: # Do calculation for each factor: OBP / PA, if possible. If not, add 0,3 (avg OBP)
                    situation_score += round(float(row.iloc[0]["OBP"]) / float(row.iloc[0]["PA"]), 5)
                except:
                    situation_score += 0.03
            rankings += [(pitcher, round(situation_score, 5))]

    rankings = sorted(rankings, key=lambda x: x[1])
    return rankings[0][0]

# Determines, on average, how many innings (num_outs) pitcher throws and how many walks
# and hits they give up. CLASSIFIER indicates whether pitcher is starter (SP) or reliever (RP).
def max_innings_and_walks_plus_hits_and_runs(pitcher, classifier, pitcher_dict):
    print(pitcher)
    innings = 0
    walks_and_hits = 0
    splits_tables = pitcher_dict[pitcher][0]
    game_log_data = pitcher_dict[pitcher][1]
    if type(game_log_data) == pd.core.frame.DataFrame:
        splits_data = splits_tables[0][1]
        
        # Get season averages for innings, walks + hits, and runs.
        season_data = splits_data.loc[splits_data["Split"] == CURRENT_YEAR + " Totals"]
        season_innings = str(season_data["IP"][0]).split(".")
        season_innings = round(float(season_innings[0]) + float(season_innings[1]) / 3, 3)
        season_walks_hits = season_data["H"][0] + season_data["BB"][0]
        season_games = season_data["G"][0]
        season_runs = season_data["R"][0]
        season_avg_innings = season_innings / season_games
        season_avg_walks_hits = season_walks_hits / season_games
        season_avg_runs = season_runs / season_games
        
        if season_games >= 5:
            # Get recent averages for innings, walks + hits, and runs.
            game_log_data = game_log_data.loc[~(game_log_data["Tm"] == "Tm")] # Remove months separators
            game_log_data = game_log_data[:-1] # Drop last row that contains totals
            game_log_data = game_log_data.drop(["Rk", "Gcar", "Gtm", "DFS(DK)", "DFS(FD)"], axis=1)
            game_log_data = game_log_data.reset_index(drop=True)
            num_recent_games = 5 # Depends on how many games pitched. Default is last 5.
            recent_games_table = game_log_data[len(game_log_data) - num_recent_games:]

            recent_innings, recent_walks_hits, recent_runs = 0, 0, 0
            for index in recent_games_table.index:
                this_outing_innings = str(recent_games_table.loc[index]["IP"]).split(".")
                this_outing_innings = float(this_outing_innings[0]) + round(float(this_outing_innings[1]) / 3, 3)
                recent_innings += this_outing_innings
                this_outing_walks_hits = int(recent_games_table.loc[index]["H"]) + int(recent_games_table.loc[index]["BB"])
                recent_walks_hits += this_outing_walks_hits
                this_outing_runs =int(recent_games_table.loc[index]["R"])
                recent_runs += this_outing_runs
            recent_avg_innings = recent_innings / num_recent_games
            recent_avg_walks_hits = recent_walks_hits / num_recent_games
            recent_avg_runs = recent_runs / num_recent_games

            # Computation for the weighted average of recent games and season games.
            innings = 0.6 * recent_avg_innings + 0.4 * season_avg_innings
            walks_and_hits = 0.6 * recent_avg_walks_hits + 0.4 * season_avg_walks_hits
            runs = 0.6 * recent_avg_runs + 0.4 * season_avg_runs
        else:
            innings = season_avg_innings
            walks_and_hits = season_avg_walks_hits
            runs = season_avg_runs
        # Adjust maximum number of innings, walks plus hits, and runs to account for "good" game scenarios.
        if innings >= 2: # Not for one-inning relievers
            if round(innings) > innings:
                innings = round(innings) + 1
            else:
                innings = innings // 1 + 1
            if round(walks_and_hits) > walks_and_hits:
                walks_and_hits = round(walks_and_hits) + 3
            else:
                walks_and_hits = walks_and_hits // 1 + 1
            if round(runs) > runs:
                runs = round(runs) + 1
            else:
                runs = runs // 1 + 1
        else: # For one-inning relievers
            innings = max(1, round(innings))
            walks_and_hits = round(walks_and_hits) + 3
            runs = round(runs) + 2
    else:
        if classifier == "SP":
            return [15, 8, 3]
        else:
            return [3, 4, 2]
    return [int(innings) * 3, int(walks_and_hits), int(runs)]

# Classifies each pitcher as a high-leverage or low-leverage reliever.If the pitcher
# does not have any associated stats for this season (i.e. making season debut or
# pro debut), then they are automatically placed in the low_leverage list.
def leverage_determiner(bullpen, pitcher_dict):
    high_leverage = [] # for "good" pitchers
    low_leverage = [] # for "bad" pitchers
    rankings_list = [] # contains "score" for each pitcher based on ERA and IP.
    for pitcher in bullpen:
        splits_tables = pitcher_dict[pitcher][0]
        game_log_table = pitcher_dict[pitcher][1]
        if splits_tables == [] or type(game_log_table) != pd.core.frame.DataFrame:
            low_leverage += [pitcher]
        else:
            table = splits_tables[0][1]
            desired_row = table.loc[table["Split"] == CURRENT_YEAR + " Totals"]

            str_innings = str(desired_row["IP"][0]).split(".")
            num_innings = float(str_innings[0]) + round(float(str_innings[1]) / 3, 3)
            score = round(max(1, desired_row["ERA"][0]) * (50 / num_innings), 5)
            rankings_list += [(pitcher, score)]
    rankings_list = sorted(rankings_list, key=lambda x: x[1])
    max_index = min(len(rankings_list), 3)
    high_leverage += [elem[0] for elem in rankings_list[:max_index]]
    low_leverage += [elem[0] for elem in rankings_list[max_index:]]
    return high_leverage, low_leverage
