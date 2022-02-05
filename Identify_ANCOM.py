'''
=============================================================
HEADER
=============================================================
INSTITUTION: BU-ISCIII
AUTHOR: Guillermo J. Gorines Cordero
MAIL: guillermo.gorines@urjc.es
VERSION: 0
CREATED: 02-02-2022
REVISED: 
DESCRIPTION: 
    Ad-hoc script to identify the differentially abundant taxa 
INPUT:
    1. multiqc_data.json generated by multiqc data
OUTPUT:
    D
'''
import os
import sys
import argparse

parser=argparse.ArgumentParser(description="")
parser.add_argument("--taxonomy", required=True, dest="taxfile", help="Taxonomy file")
parser.add_argument("--data", required=True, dest="datafile", help="")
parser.add_argument("--ancom", required = True, dest="ancomfile", help="")
parser.add_argument("--percent-abundances", required = True, dest="abundances", help="")

args = parser.parse_args()

def create_taxonomy_dict(taxfile):
    # Create a dictionary with the hash as key, the identification as value

    taxdict = dict()

    with open(taxfile) as taxfile:
        taxfile = taxfile.readlines().replace("\n","").split("\t")

    for line in taxfile:
        for code, identification in taxfile:
            taxdict[code] = identification

    return taxdict

def join_files(abundances_file, datafile, ancomfile):
    # join abundances.tsv, data.tsv & ancom.tsv files into a single list

    with open(abundances_file) as abundances_file:
        abundances_file = abundances_file.readlines().replace("\n","").split("\t")

    # headers first
    joined_list = [abundances_file[0].extend(["-","-","-"]), abundances_file[1].extend(["clr","W","Reject null Hypothesis"])]
    datadict = dict()

    for line in abundances_file[2:]:
        datadict[0] = line

        
    with open(datafile) as datafile:
        datafile = datafile.readlines().replace("\n","").split("\t")
        for line in datafile:
            datadict[line[0]].extend(line[1:])

    with open(ancomfile) as ancomfile:
        ancomfile = ancomfile.readlines().replace("\n","").split("\t")
        for line in ancomfile:
            datadict[line[0]].extend(line[2])
    
    joined_list.append(datadict.values())

    return joined_list

def identify_taxa(in_list, taxdict):
    # changes hashes with their identified taxa

    for position, item in enumerate(in_list[2:]):
        item[position+2][0] = taxdict[item[position+2][0]]
        
    return in_list

def tsv_from_list(inserted_list, filename):

    with open(filename) as outfile:
        for line in inserted_list:
            for column in line:
                outfile.write(column)
                
                if line.index(column) != len(line) -1:
                    outfile.write("\t")
            outfile.write("\n")
    return 


# taxonomy dict from taxonomy file
taxonomy_dict = create_taxonomy_dict(args.taxfile)

# generate filename
joined_list_filename = str(args.datafile).split("/")[0].replace("ancom_","").replace("_dir","") + "_ancom_result_identified.tsv"


joined_list = join_files(args.abundances, args.datafile, args.ancomfile)
join_list_identified = identify_taxa(joined_list, taxonomy_dict)
tsv_from_list(join_list_identified,joined_list_filename)