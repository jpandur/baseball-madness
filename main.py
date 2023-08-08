from get_player_info import *
from classes import *
from performance_factors import *
from inning import *
import copy
import statistics

name = input("Enter team name: ")

start1 = time.time()
away_list, home_list, away_batting_handedness, home_batting_handedness, away_pitcher, home_pitcher = get_lineups(name)
away_team_name = away_list.pop(0)
home_team_name = home_list.pop(0) # away_list and home_list now contain only the batters

away_pitcher_handedness = away_pitcher.split("(")[1][0]
home_pitcher_handedness = home_pitcher.split("(")[1][0]
away_pitcher = away_pitcher.split("(")[0][:-1]
home_pitcher = home_pitcher.split("(")[0][:-1]

away_bullpen, away_bullpen_handedness = get_bullpen(away_team_name, away_pitcher)
home_bullpen, home_bullpen_handedness = get_bullpen(home_team_name, home_pitcher)

# Get tables for batters and use them to create Batter class objects.
for i in range(len(away_list)):
    this_away_batter_url = get_splits_link(away_list[i], "b", away_team_name)
    this_home_batter_url = get_splits_link(home_list[i], "b", home_team_name)
    this_away_batter_tables = get_batting_tables(get_splits_tables(this_away_batter_url))
    this_home_batter_tables = get_batting_tables(get_splits_tables(this_home_batter_url))
    away_list[i] = Batter(away_list[i], this_away_batter_tables, away_batting_handedness[i])
    home_list[i] = Batter(home_list[i], this_home_batter_tables, home_batting_handedness[i])

# Get tables for starting pitchers and use them to create Pitcher class objects
away_pitcher_url = get_splits_link(away_pitcher, "p", away_team_name)
away_pitcher_tables = get_pitching_tables(get_splits_tables(away_pitcher_url))
home_pitcher_url = get_splits_link(home_pitcher, "p", home_team_name)
home_pitcher_tables = get_pitching_tables(get_splits_tables(home_pitcher_url))

away_pitcher = Pitcher(away_pitcher, away_pitcher_tables, away_pitcher_handedness, "SP")
home_pitcher = Pitcher(home_pitcher, home_pitcher_tables, home_pitcher_handedness, "SP")

# Get tables for bullpen and use them to create Pitcher class objects
for i in range(len(away_bullpen)):
    url = get_splits_link(away_bullpen[i], "p", away_team_name)
    tables = get_pitching_tables(get_splits_tables(url))
    away_bullpen[i] = Pitcher(away_bullpen[i], tables, away_bullpen_handedness[i], "RP")
for i in range(len(home_bullpen)):
    url = get_splits_link(home_bullpen[i], "p", home_team_name)
    tables = get_pitching_tables(get_splits_tables(url))
    home_bullpen[i] = Pitcher(home_bullpen[i], tables, home_bullpen_handedness[i], "RP")

# Rank bullpen members based on effectiveness and determine availability.
away_bullpen = rank_bullpen(away_bullpen)
home_bullpen = rank_bullpen(home_bullpen)

# Determine values of different factors that may affect play and place in lists for away team
# and home team.
park_weather_factor = get_stadium_weather(home_team_name)
park_dimensions_factor = get_stadium_factor(home_team_name)
away_recent_performance = recent_team_performance_factor(away_team_name, "AWAY")
home_recent_performance = recent_team_performance_factor(home_team_name, "HOME")
pitching_performance(away_pitcher, home_pitcher, away_bullpen, home_bullpen)

for pitcher in away_bullpen + home_bullpen:
    pitcher.available = check_pitcher_game_log(pitcher)
    print(pitcher.name, pitcher.available)

away_factors_list = [park_dimensions_factor, park_weather_factor, away_recent_performance]
home_factors_list = [park_dimensions_factor, park_weather_factor, home_recent_performance]
print(away_factors_list)
print(home_factors_list)

end1 = time.time() - start1 # time taken to collect and sort all data
start2 = time.time()

away_pitcher_outs_hits_walks_runs = away_pitcher.max_innings_walks_hits_runs()
home_pitcher_outs_hits_walks_runs = home_pitcher.max_innings_walks_hits_runs()
away_total, home_total = 0, 0 # Tracks total number of runs scored across simulations

copy_home_pitcher = copy.deepcopy(home_pitcher)
copy_away_pitcher = copy.deepcopy(away_pitcher)
copy_away_bullpen = copy.deepcopy(away_bullpen)
copy_home_bullpen = copy.deepcopy(home_bullpen)
copy_away_pitcher_outs_hits_walks_runs = copy.deepcopy(away_pitcher_outs_hits_walks_runs)
copy_home_pitcher_outs_hits_walks_runs = copy.deepcopy(home_pitcher_outs_hits_walks_runs)

scores_list = [] # keeps track of total runs scored for each simulation
differences_list = [] # keeps track of score differences
away_wins, home_wins = 0, 0 # tracks number of wins each team gets
for _ in range(1000):
    score = [0, 0]
    away_bop, home_bop = 0, 0
    half_inning_num = 1
    # Runs a game; second and third condition is for extra innings
    while half_inning_num <= 18 or score[0] == score[1] or half_inning_num % 2 == 0:
        if half_inning_num % 2 == 1: # top of innings
            print("TOP OF INNING", half_inning_num // 2 + 1)
            score, away_bop, home_pitcher, home_pitcher_outs_hits_walks_runs, home_bullpen = half_inning(score, half_inning_num,
                    away_list, away_bop, home_pitcher, home_pitcher_outs_hits_walks_runs, home_bullpen, away_factors_list)
        else: # bottom of innings
            print("BOTTOM OF INNING", half_inning_num // 2)
            score, home_bop, away_pitcher, away_pitcher_outs_hits_walks_runs, away_bullpen = half_inning(score, half_inning_num,
                    home_list, home_bop, away_pitcher, away_pitcher_outs_hits_walks_runs, away_bullpen, home_factors_list)
        print("AWAY:", score[0])
        print("HOME:", score[1])
        half_inning_num += 1
    away_total += score[0]
    home_total += score[1]

    if score[0] > score[1]:
        away_wins += 1
    else:
        home_wins += 1

    scores_list += [score[0] + score[1]]
    differences_list += [score[0] - score[1]]

    away_pitcher = copy.deepcopy(copy_away_pitcher)
    home_pitcher = copy.deepcopy(copy_home_pitcher)
    away_bullpen = copy.deepcopy(copy_away_bullpen)
    home_bullpen = copy.deepcopy(copy_home_bullpen)
    away_pitcher_outs_hits_walks_runs = copy.deepcopy(copy_away_pitcher_outs_hits_walks_runs)
    home_pitcher_outs_hits_walks_runs = copy.deepcopy(copy_home_pitcher_outs_hits_walks_runs)

# Get average scoreline for teams and number of wins.
print("")
print(away_team_name, round(away_total / 1000, 3))
print(home_team_name, round(home_total / 1000, 3))
print(away_team_name + " Number of Wins:", away_wins)
print(home_team_name + " Number of Wins", home_wins)
print("")

scores_list = sorted(scores_list)
differences_list = sorted(differences_list)
print("TOTAL RUNS SCORED")
print("Mean Runs Scored:", round(sum(scores_list) / len(scores_list), 3))
print("Median Runs Scored:", scores_list[int(len(scores_list) / 2)])
print("Standard Deviation:", round(statistics.stdev(scores_list), 3))
print("")
print("SPREAD")
print("Mean Spread:", round(sum(differences_list) / len(differences_list), 3))
print("Median Spread:", differences_list[int(len(differences_list) / 2)])
print("Spread Standard Deviation:", round(statistics.stdev(differences_list), 3))
print("")

end2 = time.time() - start2
print(end1)
print(end2)