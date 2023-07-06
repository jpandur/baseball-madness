# Used to sum values of a column where the types are strings
def string_to_int_sum(row, type):
    sum = 0
    for i in range(len(row)):
        sum += type(row[i])
    return sum

# Calculation to determine runs allowed per inning
def starting_pitcher_calculation(recent_inn, recent_runs, season_inn, season_runs):
    weighted_runs = 0.6 * recent_runs + 0.4 * season_runs
    weighted_innings = 0.6 * recent_inn + 0.4 * season_inn
    return [round(item, 3) for item in [weighted_runs, weighted_innings]]