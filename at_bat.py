import pandas as pd
import random
from datetime import datetime
from classes import *

YEAR = str(datetime.now().year)

# Given a Batter and Pitcher object, the basepaths and number of outs, and a list
# of factors (i.e. stadium factor, stadium weather, streak factor, pitching team's factor)
def at_bat(batter: type[Batter], pitcher: type[Pitcher], bases, outs, top_bottom, factors_list):
    stadium_factor = factors_list[0]
    batter_handedness = batter.handedness
    if batter_handedness == "S" and pitcher.handedness == "R":
        batter_handedness = "L"
    elif batter_handedness == "S" and pitcher.handedness == "L":
        batter_handedness = "R"
    # ballpark factor * weather factor * team's streak factor * pitching team's strength
    obp_adjustment = stadium_factor.loc[0, batter_handedness + "-OBP"] * factors_list[1] * factors_list[2] * factors_list[3]

    # Factor 1: last 28 days performance
    last_28_days_obp = last_28_days_factor(batter.totals_table, pitcher.totals_table)
    # Factor 2: platoon performance
    platoon_obp = platoon_factor(batter.platoon_table, batter_handedness, pitcher.platoon_table, pitcher.handedness)
    # Factor 3: home/away performance
    if top_bottom == "top":
        home_away_obp = home_away_factor(batter.home_away_table, pitcher.home_away_table, "Away")
    else:
        home_away_obp = home_away_factor(batter.home_away_table, pitcher.home_away_table, "Home")
    # Factor 4: bases and outs performance
    bases_outs_obp = bases_and_outs_factor(batter.bases_outs_table, pitcher.bases_outs_table, outs, bases)
    # Factor 5: times facing opponent performance
    times_facing_obp = times_facing_oppo_factor(batter, pitcher)

    final_obp = (last_28_days_obp + platoon_obp + home_away_obp + bases_outs_obp + times_facing_obp) / 5
    print(final_obp)
    if random.uniform(0, 1) <= final_obp:
        return safe_case(batter.totals_table, batter_handedness, stadium_factor)
    else:
        return out_case(bases, outs)

# Given the batter and pitcher tables containing performance in the last 28 days,
# determine the OBP for this factor.
def last_28_days_factor(batter_table, pitcher_table):
    if batter_table.empty or pitcher_table.empty:
        return 0.32 # In case neither player has played recently, return league OBP
    batter_28_row = batter_table.loc[batter_table["Split"] == "Last 28 days"]
    pitcher_28_row = pitcher_table.loc[pitcher_table["Split"] == "Last 28 days"]

    if batter_28_row.empty and pitcher_28_row.empty:
        return 0.32 # In case neither player has played recently, return league OBP
    elif batter_28_row.empty:
        pitcher_28_row = pitcher_28_row.reset_index(drop=True)
        pitcher_obp = pitcher_28_row.loc[0, "OBP"]
        return (pitcher_obp + 0.32) / 2
    elif pitcher_28_row.empty:
        batter_28_row = batter_28_row.reset_index(drop=True)
        batter_obp = batter_28_row.loc[0, "OBP"]
        return (batter_obp + 0.32) / 2
    else:
        return obp_calculator(batter_28_row, pitcher_28_row)
    
# Given batter and pitcher platoon stats, determine OBP for this factor.
def platoon_factor(batter_table, batter_handedness, pitcher_table, pitcher_handedness):
    if batter_table.empty or pitcher_table.empty:
        return 0.32 # In case neither player has played recently, return league OBP
    batter_platoon_row = batter_table.loc[batter_table["Split"] == "vs " + pitcher_handedness + "HP as " + batter_handedness + "HB"]
    pitcher_platoon_row = pitcher_table.loc[pitcher_table["Split"] == "vs " + batter_handedness + "HB"]
    if batter_platoon_row.empty or pitcher_platoon_row.empty:
        return 0.32 # In case neither player has played recently, return league OBP
    elif batter_platoon_row.empty:
        pitcher_platoon_row = pitcher_platoon_row.reset_index(drop=True)
        pitcher_obp = pitcher_platoon_row.loc[0, "OBP"]
        return (pitcher_obp + 0.32) / 2
    elif pitcher_platoon_row.empty:
        batter_platoon_row = batter_platoon_row.reset_index(drop=True)
        batter_obp = batter_platoon_row.loc[0, "OBP"]
        return (batter_obp + 0.32) / 2
    else:
        return obp_calculator(batter_platoon_row, pitcher_platoon_row)
    
# Given batter and pitcher home/away stats and where the batter is (home/away), determine
# OBP for this factor.
def home_away_factor(batter_table, pitcher_table, batter_loc):
    if batter_table.empty or pitcher_table.empty:
        return 0.32 # In case neither player has played recently, return league OBP
    if batter_loc == "Home":
        batter_home_away_row = batter_table.loc[batter_table["Split"] == batter_loc]
        pitcher_home_away_row = pitcher_table.loc[pitcher_table["Split"] == "Away"]
    else:
        batter_home_away_row = batter_table.loc[batter_table["Split"] == batter_loc]
        pitcher_home_away_row = pitcher_table.loc[pitcher_table["Split"] == "Home"]

    if batter_home_away_row.empty or pitcher_home_away_row.empty:
        return 0.32 # In case neither player has played recently, return league OBP
    elif batter_home_away_row.empty:
        pitcher_home_away_row = pitcher_home_away_row.reset_index(drop=True)
        pitcher_obp = pitcher_home_away_row.loc[0, "OBP"]
        return (pitcher_obp + 0.32) / 2
    elif pitcher_home_away_row.empty:
        batter_home_away_row = batter_home_away_row.reset_index(drop=True)
        batter_obp = batter_home_away_row.loc[0, "OBP"]
        return (batter_obp + 0.32) / 2
    else:
        return obp_calculator(batter_home_away_row, pitcher_home_away_row)
    
# Determine OBP given batter and pitcher table, number of outs, and basepaths.    
def bases_and_outs_factor(batter_table, pitcher_table, num_outs, basepaths):
    if batter_table.empty or pitcher_table.empty:
        return 0.32 # In case neither player has played recently, return league OBP
    batter_bases_outs_row = batter_table.loc[batter_table["Split"] == str(num_outs) + " out, " + basepaths]
    pitcher_bases_outs_row = pitcher_table.loc[pitcher_table["Split"] == str(num_outs) + " out, " + basepaths]
    if batter_bases_outs_row.empty or pitcher_bases_outs_row.empty:
        return 0.32 # In case neither player has played recently, return league OBP
    elif batter_bases_outs_row.empty:
        pitcher_bases_outs_row = pitcher_bases_outs_row.reset_index(drop=True)
        pitcher_obp = pitcher_bases_outs_row.loc[0, "OBP"]
        return (pitcher_obp + 0.32) / 2
    elif pitcher_bases_outs_row.empty:
        batter_bases_outs_row = batter_bases_outs_row.reset_index(drop=True)
        batter_obp = batter_bases_outs_row.loc[0, "OBP"]
        return (batter_obp + 0.32) / 2
    else:
        return obp_calculator(batter_bases_outs_row, pitcher_bases_outs_row)
    
# Determine OBP based on how many times batter and pitcher have faced each other.
def times_facing_oppo_factor(batter: type[Batter], pitcher: type[Pitcher]):
    if batter.times_facing_oppo_table.empty or pitcher.times_facing_oppo_table.empty:
        return 0.32 # In case neither player has played recently, return league OBP
    
    batter_table = batter.times_facing_oppo_table
    pitcher_table = pitcher.times_facing_oppo_table
    batter.times_faced_pitcher += 1 # Adjust value for current at-bat.
    # Check to see how many times pitcher has faced batter and update.
    if batter.name in pitcher.times_faced_batter_dict:
        pitcher.times_faced_batter_dict[batter.name] += 1
    else:
        pitcher.times_faced_batter_dict[batter.name] = 1
    
    batter_times_facing_row = batter_table.loc[batter_table["Split"].str.contains("vs. " + pitcher.type + ", " + str(batter.times_faced_pitcher))]
    pitcher_times_facing_row = pitcher_table.loc[pitcher_table["Split"].str.contains("as " + pitcher.type)]
    pitcher_times_facing_row = pitcher_times_facing_row.loc[pitcher_times_facing_row["Split"].str.contains(str(pitcher.times_faced_batter_dict[batter.name]))]
    if batter_times_facing_row.empty or pitcher_times_facing_row.empty:
        return 0.32 # In case neither player has played recently, return league OBP
    elif batter_times_facing_row.empty:
        pitcher_times_facing_row = pitcher_times_facing_row.reset_index(drop=True)
        pitcher_obp = pitcher_times_facing_row.loc[0, "OBP"]
        return (pitcher_obp + 0.32) / 2
    elif pitcher_times_facing_row.empty:
        batter_times_facing_row = batter_times_facing_row.reset_index(drop=True)
        batter_obp = batter_times_facing_row.loc[0, "OBP"]
        return (batter_obp + 0.32) / 2
    else:
        return obp_calculator(batter_times_facing_row, pitcher_times_facing_row)

# Given two pandas Series, calculate the OBP.
def obp_calculator(batter_row, pitcher_row):
    batter_row = batter_row.reset_index(drop=True)
    pitcher_row = pitcher_row.reset_index(drop=True)
    batter_safties = batter_row.loc[0, "H"] + batter_row.loc[0, "BB"] + batter_row.loc[0, "HBP"] + batter_row.loc[0, "ROE"]
    pitcher_safties = pitcher_row.loc[0, "H"] + pitcher_row.loc[0, "BB"] + pitcher_row.loc[0, "HBP"] + pitcher_row.loc[0, "ROE"]
    total_chances = batter_row.loc[0, "PA"] + pitcher_row.loc[0, "PA"]
    obp = (batter_safties + pitcher_safties) / total_chances
    return obp

# Determine safe result based on table, handedness, and location.
def safe_case(table, handedness, location):
    # Get rates for different safe results
    single_rate = 0.14183
    double_rate = 0.04516
    triple_rate = 0.00369
    home_run_rate = 0.03090
    walk_rate = 0.08584
    hbp_rate = 0.01135
    roe_rate = 0
    if not table.empty:
        total_row = table.loc[table["Split"] == YEAR + " Totals"]
        times_safe = int(total_row.loc[0, "H"]) + int(total_row.loc[0, "BB"]) + int(total_row.loc[0, "HBP"]) + int(total_row.loc[0, "ROE"])
        if times_safe > 0:
            single_rate = (int(total_row.loc[0, "H"]) - int(total_row.loc[0, "2B"]) - int(total_row.loc[0, "3B"]) - int(total_row.loc[0, "HR"])) / times_safe
            double_rate = int(total_row.loc[0, "2B"]) / times_safe
            triple_rate = int(total_row.loc[0, "3B"]) / times_safe
            home_run_rate = int(total_row.loc[0, "HR"]) / times_safe
            walk_rate = int(total_row.loc[0, "BB"]) / times_safe
            hbp_rate = int(total_row.loc[0, "HBP"]) / times_safe
            roe_rate = int(total_row.loc[0, "ROE"]) / times_safe

    # Adjust rates based on location and handedness.
    adjusted_single_rate = single_rate * location.loc[0, handedness + "-1B"]
    adjusted_double_rate = double_rate * location.loc[0, handedness + "-2B"]
    adjusted_triple_rate = triple_rate * location.loc[0, handedness + "-3B"]
    adjusted_home_run_rate = home_run_rate * location.loc[0, handedness + "-HR"]
    adjusted_walk_rate = walk_rate * location.loc[0, handedness + "-BB"]
    adjusted_sum = adjusted_single_rate + adjusted_double_rate + adjusted_triple_rate + adjusted_home_run_rate + adjusted_walk_rate + hbp_rate + roe_rate
    result = random.uniform(0, adjusted_sum)
    if result <= adjusted_single_rate:
        return "Single"
    elif result <= adjusted_single_rate + adjusted_double_rate:
        return "Double"
    elif result <= adjusted_single_rate + adjusted_double_rate + adjusted_triple_rate:
        return "Triple"
    elif result <= adjusted_single_rate + adjusted_double_rate + adjusted_triple_rate + adjusted_home_run_rate:
        return "Home Run"
    elif result <= adjusted_single_rate + adjusted_double_rate + adjusted_triple_rate + adjusted_home_run_rate + adjusted_walk_rate:
        return "Walk"
    elif result <= adjusted_single_rate + adjusted_double_rate + adjusted_triple_rate + adjusted_home_run_rate + adjusted_walk_rate + hbp_rate:
        return "HBP"
    else:
        return "ROE"

# Determine type of out based on basepaths and number of outs.
def out_case(basepaths, num_outs):
    if basepaths[2] == "3" and num_outs < 2:
        if random.uniform(0, 1) <= 0.02:
            return "Sacrifice Fly"
        else:
            return "Out"
        
    if basepaths[0] == "1" and num_outs < 2:
        if random.uniform(0, 1) <= 0.05:
            return "GIDP"
        else:
            return "Out"
    
    return "Out"