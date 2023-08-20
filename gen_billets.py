#!/usr/bin/env python

from faker import Faker
from collections import OrderedDict
import csv
import argparse

def gen_and_write_billets(fake: Faker, datawriter: csv.DictWriter, count: int) -> None:
    row = dict()

    for _ in range(count):
        row['BIN'] = 'B%s' % fake.unique.random_int(min=10000000, max=99999999)
        row['UIC'] = 'N%s' % fake.bothify("####?", letters="0123456789A")
        row['BSC'] = 'S%05d' % fake.random_int(0, max=99990, step=5)
        row['TITLE'] = fake.job()
        row['TYPE'] = fake.random_element(elements=('SEA','SHR'))
        row['RATE'] = fake.random_elements(
                elements=OrderedDict([
                    ('HM', 0.28),
                    ('MA', 0.17),
                    ('MM', 0.10),
                    ('YN', 0.10),
                    ('OS', 0.06),
                    ('CWT', 0.03),
                    ('EMN', 0.04),
                    ('IS', 0.04),
                    ('PS', 0.02),
                    ('EN', 0.01),
                    ('CS', 0.05),
                    ('AO', 0.03),
                    ('PR', 0.02),
                    ('AT', 0.02),
                    ('STG', 0.03)
                ]), unique=False)[0]
        row['PAYGRD'] = fake.random_elements(
                elements=OrderedDict([
                    ('E-3', 0.35),
                    ('E-4', 0.30),
                    ('E-5', 0.18),
                    ('E-6', 0.10),
                    ('E-7', 0.04),
                    ('E-8', 0.02),
                    ('E-9', 0.01),
                ]), unique=False)[0]
        row['NEC1'] = 'N000'
        row['NEC2'] = 'N000'

        datawriter.writerow(row)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generates test data for the billet file in the Navy HR model.")
    parser.add_argument('-o', '--output', default='billets.csv', type=str,
                        help="Output file for billets")
    parser.add_argument('-c', '--count', default=10, type=int,
                        help="Number of billets to generate")
    parser.add_argument('-s', '--random-seed', default=19920813, type=int,
                        help="Number to use to seed randomness generator")

    args = parser.parse_args()

    Faker.seed(args.random_seed)
    fake = Faker()

    # Create CSV of billet data
    csv_fields = ['BIN','UIC','BSC','TITLE','TYPE','RATE','PAYGRD','NEC1','NEC2']

    with open(args.output, 'w', newline='') as csvfile:
        datawriter = csv.DictWriter(csvfile, fieldnames=csv_fields, dialect='unix', quoting=csv.QUOTE_MINIMAL)
        datawriter.writeheader()

        gen_and_write_billets(fake, datawriter, args.count)
