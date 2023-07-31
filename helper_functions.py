import pandas as pd

# Given a team code, find the full name of the team.
def code_to_name(code):
    name_table = pd.read_csv("~/Documents/mlb_project/names_stadiums.csv")
    row = name_table.loc[name_table["Code"] == code]
    row = row.reset_index(drop=True)
    return row.loc[0, "Name"]

# Helper function to find the proper url based on the KEY_PHRASE
def find_url(possiblites, key_phrase):
    url = ''
    index = 0
    while not url:
        if key_phrase in possiblites[index]:
            url = possiblites[index]
        index += 1
        if index == len(possiblites):
            return url
    return url
