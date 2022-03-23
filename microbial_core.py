'''
=============================================================
HEADER
=============================================================
INSTITUTION: BU-ISCIII
AUTHOR: Guillermo J. Gorines Cordero
MAIL: guillermo.gorines@urjc.es
VERSION: 0
CREATED: 15-3-2022
REVISED: 15-3-2022
DESCRIPTION: 
    Ad-hoc script to get the list of present organsims by group
INPUT:
    1. The raw counts (lvl 7)
    2. the metadata file
OUTPUT:
    -Json with all presence by level and category
    -Directory for each category
        -tsv file for each level (1-7) in that category 
'''

import pandas as pd
import json
import sys
import os

infile = sys.argv[1]
metadata_file = sys.argv[2]

def normalize_dataframe(dataframe, criteria=0):
    """
    Change the dataframe to an absence-presence matrix
    based on a criteria (by now, a number)
    """
    
    row_number, col_number = dataframe.shape
    
    for row in range(0, row_number):
        for col in range(0, col_number):
            if dataframe.iloc[row, col] >= criteria:
                dataframe.iloc[row, col] = 1
            else:
                dataframe.iloc[row, col] = 0
                
    return dataframe

def create_category_dict(metadata):
    """
    Create, from the metadata dataframe, a dict with
    key: category; val: values in that category
    if only one category, it wont be taken into account
    """
    valid_categories = dict()
    category_names_list = list(metadata.columns)

    # get all different possibilities for each metadata column
    for col_index in range(metadata.shape[1]):
        
        # list from a set to avoid repeating
        groups = (list(set(metadata[category_names_list[col_index]])))
        
        # if more than 1 different category, add it to the dict
        if len(groups) > 1:
            category_name = category_names_list[col_index]
            valid_categories[category_name] = [item for item in groups]

    return valid_categories, category_names_list

# Import the counts
counts = pd.read_csv(
    infile,
    sep='\t',
    header=0,
    index_col=0
    )

# Import the metadata file so it matches with the counts
metadata = pd.read_csv(
    metadata_file,
    sep='\t',
    header=0,
    index_col=0
    )

# Get the categories
valid_categories, category_names_list = create_category_dict(metadata)

# Generate the full dataframe
# concat metadata and counts
full_df = pd.concat([metadata, counts], axis=1)

# dict for the list of organisms for each sample
list_dict = {}

# generate a sub-df for each category
for category, values in valid_categories.items():
    # create category directory (tidier output)
    try:
        os.mkdir(category)
    except FileExistsError:
        pass
    
    # subdict for each category
    list_dict[category] = {}
        
    for value in values:
        # drop metadata columns
        sub_df = full_df[full_df[category] == value].drop(category_names_list, axis=1)        
        spp_name = list(sub_df.columns)
        
        for level in reversed(range(1,8)):
            
            # subdict for the level if it doesn't previously exist
            if level not in list_dict[category]:
                list_dict[category][level] = {}
            list_dict[category][level][value] = {}
                        
            # get the names at that level (7-species, 0-domain)
            trimmed_names = [";".join(item.split(";")[0:level]) for item in spp_name]
                       
            # find those names ending with ";__"
            # ";__" at the end means no identification at that level
            discarded_names = [item for item in trimmed_names if item.endswith(";__")]
            
            # put names on a dict to be renamed (key: former, val: trimmed)
            changename_dict = {
                full_name : trimmed_name for full_name, trimmed_name in zip(spp_name,trimmed_names)
                }
            
            # change the names in the df according to it
            leveled_df = sub_df.rename(columns=changename_dict)
            
            # drop the items in the discarded name from columns
            leveled_df.drop(discarded_names, inplace=True, axis=1)

            # Add up repeated columns
            leveled_df = leveled_df.groupby(leveled_df.columns, axis=1).sum()
            
            # normalize (0: absence, 1: presence)
            leveled_df = normalize_dataframe(leveled_df, criteria=1)
            
            leveled_df.loc["All"] = leveled_df.sum()

            # normalize it (I had to do it with a for loop, sorry viewer)
            row_number, col_number = leveled_df.shape
            
            # last row, row_number-1, is the "All" row
            for column in range(0, col_number):
                # first, get the relative abundance of each taxon on each group 
                leveled_df.iloc[row_number-1, column] = leveled_df.iloc[row_number-1, column]*100/(row_number-1) 
            

            # file will contain row: category name, columns: abundance of this taxa in the group
            filename = f"{category}_prevalence_plots/{category}_lvl{level}.tsv"

            to_write_df = leveled_df.transpose()
            to_write_df.to_csv(filename, sep="\t")
            
            for column in range(0, col_number):
                # if present in all, change it to 1 (global presence)
                # else change it to 0
                if leveled_df.iloc[row_number-1, column] < 100:                    
                    leveled_df.iloc[row_number-1, column] = 0
                else:
                    leveled_df.iloc[row_number-1, column] = 1
                    
            for sample in leveled_df.index.tolist():
                list_dict[category][level][value][sample] = leveled_df.loc[sample].index[leveled_df.loc[sample] == 1].tolist()

# save all presences to a json file
with open("organized_presence_list.json","w") as infile:
    json.dump(list_dict, infile, indent=4)
