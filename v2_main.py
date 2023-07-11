from v2_inning_and_game import *

name = input("Enter team name: ")
away_list, home_list, away_batting_handedness, home_batting_handedness = get_lineups(name)
game = game(away_list, home_list, away_batting_handedness, home_batting_handedness)
print(away_list[0] + ": " + game[0])
print(home_list[0] + ": " + game[1])