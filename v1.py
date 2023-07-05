from v1_func import *

away_team, home_team = get_lineup() # Get names on lineup

# Convert lineup names into corresponding season stats
away_stats = player_to_stats(away_team, "2023")
home_stats = player_to_stats(home_team, "2023")

away_runs, home_runs = 0, 0
away_bop, home_bop = 0, 0

starters = get_starting_pitching("2023")
bullpen = get_bullpen(away_team[0], home_team[0], "2023")

# Simulate 10000 different games to determine which side would win.
total_away, total_home = 0, 0
for _ in range(10000):
    this_away, this_home = game(away_stats, home_stats, away_runs, home_runs,
            away_bop, home_bop, starters, bullpen)
    total_away += this_away
    total_home += this_home
print("Away Runs: " + str(round(total_away / 10000, 3)))
print("Home Runs: " + str(round(total_home / 10000, 3)))