from v2_inning_and_game import *
import copy

name = input("Enter team name: ")

start1 = time.time()
# Get lineups and handedness of batters.
away_list, home_list, away_batting_handedness, home_batting_handedness = get_lineups(name)
away_team_name = code_to_name(away_list[0])
home_team_name = code_to_name(home_list[0])

# Collect information on batters.
away_batters = away_list[2:]
home_batters = home_list[2:]
away_batters = [player.split("(")[0][:-1] for player in away_batters] # Only keep name portion
home_batters = [player.split("(")[0][:-1] for player in home_batters]
away_batters_dict = get_batter_data(away_batters, away_team_name)
home_batters_dict = get_batter_data(home_batters, home_team_name)
print("ALL BATTER DATA COLLECTED")

# Collect information on pitchers.
away_pitcher = away_list[1] # initially away starter
home_pitcher = home_list[1] # initially home starter
away_bullpen, away_closer = get_bullpen(away_team_name)
for reliever in away_bullpen:
    if away_pitcher in reliever:
        away_bullpen.remove(reliever)
        break
if away_closer == '':
    away_pitchers_dict = get_pitcher_data([away_pitcher] + away_bullpen, away_team_name)
else:
    away_pitchers_dict = get_pitcher_data([away_pitcher, away_closer] + away_bullpen, away_team_name)
print("Away Bullpen Complete")

home_bullpen, home_closer = get_bullpen(home_team_name)
for reliever in home_bullpen:
    if home_pitcher in reliever:
        home_bullpen.remove(reliever)
        break
if home_closer == '':
    home_pitchers_dict = get_pitcher_data([home_pitcher] + home_bullpen, home_team_name)
else:
    home_pitchers_dict = get_pitcher_data([home_pitcher, home_closer] + home_bullpen, home_team_name)
print("Home Bullpen Complete")
print("ALL PITCHER DATA COLLECTED")

location = park_factor(home_list[0]) # Get location

# Determine which relievers are ready for today's game.
away_bullpen_go, away_bullpen_no_go = go_no_go_bullpen(away_bullpen, away_pitchers_dict)
home_bullpen_go, home_bullpen_no_go = go_no_go_bullpen(home_bullpen, home_pitchers_dict)
print("BULLPEN GO NO GO COMPLETED")
# Subdivide available bullpens and place in bullpen_go lists.
away_bullpen_high_leverage, away_bullpen_low_leverage = leverage_determiner(away_bullpen_go, away_pitchers_dict)
home_bullpen_high_leverage, home_bullpen_low_leverage = leverage_determiner(home_bullpen_go, home_pitchers_dict)
away_bullpen_go = [away_bullpen_high_leverage, away_bullpen_low_leverage]
home_bullpen_go = [home_bullpen_high_leverage, home_bullpen_low_leverage]
print("BULLPEN LEVERAGE DETERMINATION COMPLETED")
print(away_bullpen_go)
print(away_bullpen_high_leverage)
print(away_bullpen_low_leverage)
print(home_bullpen_go)
print(home_bullpen_high_leverage)
print(home_bullpen_low_leverage)

# Get max allowed hits, walks, IP, Runs for each pitcher (starter and bullpen)
walks_hits_innings_runs_dict = {away_pitcher: max_innings_and_walks_plus_hits_and_runs(away_pitcher, "SP", away_pitchers_dict),
        home_pitcher: max_innings_and_walks_plus_hits_and_runs(home_pitcher, "SP", home_pitchers_dict)}
for pitcher in [elem for elem in [away_closer] + away_bullpen if elem]: # filters out empty closer
    walks_hits_innings_runs_dict[pitcher] = max_innings_and_walks_plus_hits_and_runs(pitcher, "RP", away_pitchers_dict)
for pitcher in [elem for elem in [home_closer] + home_bullpen if elem]:
    walks_hits_innings_runs_dict[pitcher] = max_innings_and_walks_plus_hits_and_runs(pitcher, "RP", home_pitchers_dict)    
print("PITCHER DICTIONARY FILLED OUT")
print(walks_hits_innings_runs_dict)

end1 = time.time() - start1
start2 = time.time()

away_total, home_total = 0, 0
copy_walks_hits_innings_run_dict = copy.deepcopy(walks_hits_innings_runs_dict)
copy_away_bullpen_go = copy.deepcopy(away_bullpen_go)
copy_away_bullpen_no_go = copy.deepcopy(away_bullpen_no_go)
copy_home_bullpen_go = copy.deepcopy(home_bullpen_go)
copy_home_bullpen_no_go = copy.deepcopy(home_bullpen_no_go)
away_total_35, home_total_35 = 0, 0
for i in range(100):
    score = [0, 0]
    away_bop, home_bop = 0, 0
    half_innings_played = 0
    while half_innings_played < 18 or score[0] == score[1] or half_innings_played % 2 == 1:
        if half_innings_played % 2 == 0: # Top of inning, away bats and home pitches
            print("TOP OF INNING", half_innings_played / 2 + 1)
            if half_innings_played == 16:
                if score[1] - score[0] >= 0 and score[1] - score[0] <= 3 and home_closer != '': # if tied or home team up by at most 3 runs, use closer
                    score, home_bullpen_go, home_bullpen_no_go, home_pitcher, walks_hits_innings_runs_dict, away_bop = half_inning(away_batters,
                            away_batting_handedness, away_batters_dict, away_bop, home_closer, home_bullpen_go, home_bullpen_no_go, home_pitchers_dict, score, "top", location, walks_hits_innings_runs_dict)
                else:
                    score, home_bullpen_go, home_bullpen_no_go, home_pitcher, walks_hits_innings_runs_dict, away_bop = half_inning(away_batters,
                            away_batting_handedness, away_batters_dict, away_bop, home_pitcher, home_bullpen_go, home_bullpen_no_go, home_pitchers_dict, score, "top", location, walks_hits_innings_runs_dict)
            else:
                score, home_bullpen_go, home_bullpen_no_go, home_pitcher, walks_hits_innings_runs_dict, away_bop = half_inning(away_batters,
                            away_batting_handedness, away_batters_dict, away_bop, home_pitcher, home_bullpen_go, home_bullpen_no_go, home_pitchers_dict, score, "top", location, walks_hits_innings_runs_dict)
        else: # Bottom of inning, home bats and away pitches
            print("BOTTOM OF INNING", half_innings_played // 2 + 1)
            if half_innings_played == 17:
                if score[1] > score[0]: # If home team is winning following the top of the 9th, game is over
                    break
                if score[0] - score[1] >= 0 and score[0] - score[1] <= 3 and away_closer != '': # if tied or away team up by at most 3 runs, use closer
                    score, away_bullpen_go, away_bullpen_no_go, away_pitcher, walks_hits_innings_runs_dict, home_bop = half_inning(home_batters,
                            home_batting_handedness, home_batters_dict, home_bop, away_closer, away_bullpen_go, away_bullpen_no_go, away_pitchers_dict, score, "bottom", location, walks_hits_innings_runs_dict)
                else:
                    score, away_bullpen_go, away_bullpen_no_go, away_pitcher, walks_hits_innings_runs_dict, home_bop = half_inning(home_batters,
                            home_batting_handedness, home_batters_dict, home_bop, away_pitcher, away_bullpen_go, away_bullpen_no_go, away_pitchers_dict, score, "bottom", location, walks_hits_innings_runs_dict)
            else:
                score, away_bullpen_go, away_bullpen_no_go, away_pitcher, walks_hits_innings_runs_dict, home_bop = half_inning(home_batters,
                            home_batting_handedness, home_batters_dict, home_bop, away_pitcher, away_bullpen_go, away_bullpen_no_go, away_pitchers_dict, score, "bottom", location, walks_hits_innings_runs_dict)
        half_innings_played += 1
        print(half_innings_played)
        if half_innings_played == 24:
            break
    print("AWAY: ", score[0])
    print("HOME: ", score[1])
    away_total += score[0]
    home_total += score[1]

    if i < 35:
        away_total_35 += score[0]
        home_total_35 += score[1]


    walks_hits_innings_runs_dict = copy.deepcopy(copy_walks_hits_innings_run_dict)
    away_bullpen_go = copy.deepcopy(copy_away_bullpen_go)
    away_bullpen_no_go = copy.deepcopy(copy_away_bullpen_no_go)
    home_bullpen_go = copy.deepcopy(copy_home_bullpen_go)
    home_bullpen_no_go = copy.deepcopy(copy_home_bullpen_no_go)
    away_pitcher = away_list[1] # initially away starter
    home_pitcher = home_list[1] # initially home starter

end2 = time.time() - start2    
print(end1) # Time to collect data
print(end2) # Time to run game.
print("Away Average:", away_total / 100)
print("Home Average:", home_total / 100)
print("Away Average 35:", away_total_35 / 35)
print("Home Average 35:", home_total_35 / 35)
