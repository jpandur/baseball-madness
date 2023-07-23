class Batter:
    def __init__(self, name, dataframes_list, handedness):
        self.name = name
        self.totals_table = dataframes_list[0].fillna(0)
        self.platoon_table = dataframes_list[1].fillna(0)
        self.home_away_table = dataframes_list[2].fillna(0)
        self.bases_outs_table = dataframes_list[3].fillna(0)
        self.times_facing_oppo_table = dataframes_list[4].fillna(0)
        self.handedness = handedness
        self.times_faced_pitcher = 0

class Pitcher:
    def __init__(self, name, dataframes_list, handedness, type):
        self.name = name
        self.totals_table = dataframes_list[0].fillna(0)
        self.totals_table_game_level = dataframes_list[1].fillna(0)
        self.platoon_table = dataframes_list[2].fillna(0)
        self.home_away_table = dataframes_list[3].fillna(0)
        self.home_away_game_level = dataframes_list[4].fillna(0)
        self.bases_outs_table = dataframes_list[5].fillna(0)
        self.times_facing_oppo_table = dataframes_list[6].fillna(0)
        self.handedness = handedness
        self.type = type # SP or RP
        self.times_faced_batter_dict = {} # each time a batter faces pitcher, add to it
        self.available = True

        if not self.totals_table_game_level.empty:
            last_7_days_row = self.totals_table_game_level.loc[self.totals_table_game_level["Split"] == "Last 7 days"]
            last_7_days_row = last_7_days_row.reset_index(drop=True)
            if last_7_days_row.empty or int(last_7_days_row.loc[0, "G"]) < 4:
                pass # determine availability of reliever
            else:
                self.available = False

    # Given a pitcher's recent outings (last 28 games) and season data, determine the
    # maximum number of outs recorded (IP * 3), walks plus hits allowed, and runs.
    # Recent outings are weighed more heavily.
    def max_innings_walks_hits_runs(self):
        if self.totals_table_game_level.empty:
            if self.type == "SP":
                return [15, 7, 3]
            else:
                return [3, 3, 2]
        
        season_innings_str = str(self.totals_table_game_level.loc[0, "IP"])
        season_outs = int(season_innings_str.split(".")[0]) * 3 + int(season_innings_str.split(".")[1])
        season_walks_hits = int(self.totals_table_game_level.loc[0, "H"]) + int(self.totals_table_game_level.loc[0, "BB"])
        season_runs = int(self.totals_table_game_level.loc[0, "R"])
        season_games = int(self.totals_table_game_level.loc[0, "G"])

        last_28_days = self.totals_table_game_level.loc[self.totals_table_game_level["Split"] == "Last 28 days"]
        if not last_28_days.empty:
            last_28_days = last_28_days.reset_index(drop=True)
            recent_innings_str = str(last_28_days.loc[0, "IP"])
            recent_outs = int(recent_innings_str.split(".")[0]) * 3 + int(recent_innings_str.split(".")[1])
            recent_walks_hits = int(last_28_days.loc[0, "H"]) + int(last_28_days.loc[0, "BB"])
            recent_runs = int(last_28_days.loc[0, "R"])
            recent_games = int(last_28_days.loc[0, "G"])
        else:
            recent_outs = season_outs
            recent_runs = season_runs
            recent_games = season_games
            recent_walks_hits = season_walks_hits

        actual_outs = round(0.6 * recent_outs / recent_games + 0.4 * season_outs / season_games)
        actual_walks_hits = round(0.6 * recent_walks_hits / recent_games + 0.4 * season_walks_hits / season_games)
        actual_runs = round(0.6 * recent_runs / recent_games + 0.4 * season_runs / season_games)
        return [actual_outs + 2, actual_walks_hits + 2, actual_runs + 1] # added constants for adjustments
    