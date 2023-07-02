from v1_func import *

away_team, home_team = get_roster() # Get names on lineup

# Convert lineup names into corresponding season stats
away_stats = player_to_stats(away_team, "2023")
home_stats = player_to_stats(home_team, "2023")

away_runs, home_runs = 0, 0
away_bop, home_bop = 0, 0

# Simulate 10000 different games to determine which side would win.
away_win, home_win = 0, 0
for _ in range(10000):
    winner = game(away_stats, home_stats, away_runs, home_runs, away_bop, home_bop)
    if winner == "AWAY WIN":
        away_win += 1
    else:
        home_win += 1
print("Away Wins: " + str(away_win))
print("Home Wins: " + str(home_win))