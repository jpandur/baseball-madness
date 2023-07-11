from v2_inning_and_game import *

name = input("Enter team name: ")

# Get lineups and handedness of batters.
away_list, home_list, away_batting_handedness, home_batting_handedness = get_lineups(name)

# Collect information on batters.
away_batters = away_list[2:]
home_batters = home_list[2:]
away_batters_dict = get_batter_data(away_batters)
home_batters_dict = get_batter_data(home_batters)
print("ALL BATTER DATA COLLECTED")

# Collect information on pitchers.
away_pitcher = away_list[1] # initially away starter
home_pitcher = home_list[1] # initially home starter
away_bullpen, away_closer = get_bullpen(away_list[0])
for reliever in away_bullpen:
    if reliever in away_pitcher:
        away_bullpen.remove(reliever)
        break
if away_closer == '':
    away_pitchers_dict = get_pitcher_data([away_pitcher] + away_bullpen)
else:
    away_pitchers_dict = get_pitcher_data([away_pitcher, away_closer] + away_bullpen)

home_bullpen, home_closer = get_bullpen(home_list[0])
for reliever in home_bullpen:
    if reliever in home_pitcher:
        home_bullpen.remove(reliever)
        break
if home_closer == '':
    home_pitchers_dict = get_pitcher_data([home_pitcher] + home_bullpen)
else:
    home_pitchers_dict = get_pitcher_data([home_pitcher, home_closer] + home_bullpen)
print("ALL PITCHER DATA COLLECTED")

location = park_factor(home_list[0]) # Get location

away_pitcher = away_pitcher.split("(")[0][:-1] # to get rid of (L) or (R) after name and space
home_pitcher = home_pitcher.split("(")[0][:-1]
away_batters = [player.split("(")[0] for player in away_batters]
home_batters = [player.split("(")[0] for player in home_batters]

start = time.time()
# Determine which relievers are ready for today's game.
away_bullpen_go, away_bullpen_no_go = go_no_go_bullpen(away_bullpen)
home_bullpen_go, home_bullpen_no_go = go_no_go_bullpen(home_bullpen)
# Subdivide available bullpens and place in bullpen_go lists.
away_bullpen_high_leverage, away_bullpen_low_leverage = leverage_determiner(away_bullpen_go, away_pitchers_dict)
home_bullpen_high_leverage, home_bullpen_low_leverage = leverage_determiner(home_bullpen_go, home_pitchers_dict)
away_bullpen_go = [away_bullpen_high_leverage, away_bullpen_low_leverage]
home_bullpen_go = [home_bullpen_high_leverage, home_bullpen_low_leverage]
print("BULLPEN GO NO GO COMPLETED")

# Get max allowed hits, walks, IP, Runs for each pitcher (starter and bullpen)
walks_hits_innings_runs_dict = {away_pitcher: max_innings_and_walks_plus_hits_and_runs(away_pitcher, "SP", away_pitchers_dict),
        home_pitcher: max_innings_and_walks_plus_hits_and_runs(home_pitcher, "SP", home_pitchers_dict)}
for pitcher in [away_closer] + away_bullpen:
    walks_hits_innings_runs_dict[pitcher] = max_innings_and_walks_plus_hits_and_runs(pitcher, "RP", away_pitchers_dict)
for pitcher in [home_closer] + home_bullpen:
    walks_hits_innings_runs_dict[pitcher] = max_innings_and_walks_plus_hits_and_runs(pitcher, "RP", home_pitchers_dict)    
print("PITCHER DICTIONARY FILLED OUT")

score = [0, 0]
half_innings_played = 0

while half_innings_played < 18 or score[0] == score[1]:
    if half_innings_played % 2 == 0: # Top of inning, away bats and home pitches
        print("TOP OF INNING ", half_innings_played / 2 + 1)
        if half_innings_played == 16:
            if score[1] - score[0] >= 0 and score[1] - score[0] <= 3: # if tied or home team up by at most 3 runs, use closer
                score, home_bullpen_go, home_bullpen_no_go, home_pitcher, walks_hits_innings_runs_dict, away_bop = half_inning(away_batters,
                        away_batting_handedness, away_batters_dict, away_bop, home_closer, home_bullpen_go, home_bullpen_no_go, home_pitchers_dict, score, "top", location, walks_hits_innings_runs_dict)
            else:
                score, home_bullpen_go, home_bullpen_no_go, home_pitcher, walks_hits_innings_runs_dict, away_bop = half_inning(away_batters,
                        away_batting_handedness, away_batters_dict, away_bop, home_pitcher, home_bullpen_go, home_bullpen_no_go, home_pitchers_dict, score, "top", location, walks_hits_innings_runs_dict)
        else:
            score, home_bullpen_go, home_bullpen_no_go, home_pitcher, walks_hits_innings_runs_dict, away_bop = half_inning(away_batters,
                        away_batting_handedness, away_batters_dict, away_bop, home_pitcher, home_bullpen_go, home_bullpen_no_go, home_pitchers_dict, score, "top", location, walks_hits_innings_runs_dict)
    else: # Bottom of inning, home bats and away pitches
        print("BOTTOM OF INNING ", half_innings_played // 2 + 1)
        if half_innings_played == 17:
            if score[1] > score[0]: # If home team is winning following the top of the 9th, game is over
                break
            if score[0] - score[1] >= 0 and score[0] - score[1] <= 3: # if tied or away team up by at most 3 runs, use closer
                score, away_bullpen_go, away_bullpen_no_go, away_pitcher, walks_hits_innings_runs_dict, home_bop = half_inning(home_batters,
                        home_batting_handedness, home_batters_dict, home_bop, away_closer, away_bullpen_go, away_bullpen_no_go, away_pitchers_dict, score, "bottom", location, walks_hits_innings_runs_dict)
            else:
                score, away_bullpen_go, away_bullpen_no_go, away_pitcher, walks_hits_innings_runs_dict, home_bop = half_inning(home_batters,
                        home_batting_handedness, home_batters_dict, home_bop, away_pitcher, away_bullpen_go, away_bullpen_no_go, away_pitchers_dict, score, "bottom", location, walks_hits_innings_runs_dict)
        else:
            score, away_bullpen_go, away_bullpen_no_go, away_pitcher, walks_hits_innings_runs_dict, home_bop = half_inning(home_batters,
                        home_batting_handedness, home_batters_dict, home_bop, away_pitcher, away_bullpen_go, away_bullpen_no_go, away_pitchers_dict, score, "bottom", location, walks_hits_innings_runs_dict)
    half_innings_played += 1

print("HOME: ", score[0])
print("AWAY: ", score[1])
print(time.time() - start)