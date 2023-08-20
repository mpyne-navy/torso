#!/usr/bin/env python

from faker import Faker
from collections import OrderedDict
import csv

Faker.seed(19920813)

fake = Faker()

print (fake.name())

# Create CSV of billet data
csv_fields = ['BIN','UIC','BSC','TITLE','TYPE','RATE','PAYGRD','NEC1','NEC2']

with open('billets.csv', 'w', newline='') as csvfile:
    datawriter = csv.DictWriter(csvfile, fieldnames=csv_fields, dialect='unix')

    datawriter.writeheader()
    row = dict()

    for _ in range(10):
        row['BIN'] = 'B%s' % fake.unique.random_int(min=10000000, max=99999999)
        row['UIC'] = 'N%s' % fake.bothify("####?", letters="0123456789A")
        row['BSC'] = 'S%s' % fake.random_int(0, max=99990, step=5)
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
