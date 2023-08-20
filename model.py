#!/usr/bin/env python

import csv
import sys

def read_billets(filename='billets.csv'):
    ''' Reads in the given list of billets for the HR model simulation '''
    with open(filename, newline='') as csvfile:
        datareader = csv.DictReader(csvfile)
        return [row for row in datareader]

    raise OSError(f"Could not read {filename}")

def read_personnel(filename='personnel.csv'):
    ''' Reads in the given list of personnel for the HR model simulation '''
    with open(filename, newline='') as csvfile:
        datareader = csv.DictReader(csvfile)
        return [row for row in datareader]

if __name__ == '__main__':
    billets = read_billets()

    if len(billets) <= 0:
        print ("Billet file empty")
        sys.exit(1)

    pers    = read_personnel()

    if len(billets) <= 0:
        print ("Personnel file empty")
        sys.exit(1)

    print (f"Read in {len(billets)} billets")
    print (f"Read in {len(pers)} personnel")

    sys.exit(0)
