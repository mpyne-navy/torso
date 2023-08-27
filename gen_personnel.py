#!/usr/bin/env python

from faker import Faker
from collections import OrderedDict
import argparse
import datetime
import csv
import sys

def read_billets(filename='billets.csv'):
    ''' Reads in the given list of billets for the HR model simulation '''
    with open(filename, newline='') as csvfile:
        datareader = csv.DictReader(csvfile)
        return [row for row in datareader]

    raise OSError(f"Could not read {filename}")

def gen_and_write_personnel(fake: Faker, datawriter: csv.DictWriter, billets: list[dict[str, str]], fill_pct: int) -> None:
    row = dict()
    print (f"Filling {fill_pct}% of billets")
    for b in billets:
        if fill_pct < 100 and fake.random_int(min=0, max=99) >= fill_pct:
            continue

        # We will fill the billet, what kind of Sailor did we need?
        row['BIN'] = b['BIN']
        row['UIC'] = b['UIC']
        row['BSC'] = b['BSC']
        row['RATE'] = b['RATE']
        row['PGRADE'] = b['PAYGRD']
        row['NEC1'] = b['NEC1']
        row['NEC2'] = b['NEC2']
        row['ACC']  = 'A100'
        row['NAME'] = fake.name()
        row['DODID'] = fake.unique.random_int(min=10000000, max=99999999)

        # Assume PRD is <= EAOS, and that EAOS is between now and 5 years from now
        # ADSD is harder but for now assume a flat 6 years prior to EAOS
        EAOS = fake.date_between(start_date='today', end_date='+5y')
        PRD  = fake.date_between(start_date='today', end_date=EAOS)
        ADSD = fake.date_between(start_date='-20y', end_date=EAOS)

        row['EAOS'] = EAOS.isoformat()
        row['PRD']  = PRD.isoformat()
        row['ADSD'] = ADSD.isoformat()

        datawriter.writerow(row)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generates test data for the enlisted personnel file in the Navy HR model.")
    parser.add_argument('-o', '--output', default='personnel.csv', type=str,
                        help="Output file for enlisted personnel file")
    parser.add_argument('-b', '--billets', default='billets.csv', type=str,
                        help="Input file with billets to fill with generated personnel")
    parser.add_argument('-f', '--filled-pct', default=100, type=int,
                        help="Odds a billet will be currently filled (not gapped) [0-100]")
    parser.add_argument('-s', '--random-seed', default=19920813, type=int,
                        help="Number to use to seed randomness generator")

    args = parser.parse_args()

    Faker.seed(args.random_seed)
    fake = Faker()

    billets = read_billets(args.billets)

    if len(billets) <= 0:
        print ("Billet file empty")
        sys.exit(1)

    if args.filled_pct < 0 or args.filled_pct > 100:
        print (f"Invalid --filled-pct {args.filled_pct}, must be between 0-100")
        sys.exit(1)

    if args.output == args.billets:
        print (f"Do not set billet file and personnel file the same")
        sys.exit(1)

    print (f"Read in {len(billets)} billets")

    # Create CSV of billet data
    csv_fields = 'DODID NAME RATE PGRADE NEC1 NEC2 ADSD EAOS PRD UIC BSC BIN ACC'.split(' ')

    with open(args.output, 'w', newline='') as csvfile:
        datawriter = csv.DictWriter(csvfile, fieldnames=csv_fields, dialect='unix', quoting=csv.QUOTE_MINIMAL)
        datawriter.writeheader()

        gen_and_write_personnel(fake, datawriter, billets, args.filled_pct)

    sys.exit(0)
