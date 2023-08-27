#!/usr/bin/env python

import csv
import sys
import datetime
import calendar

def next_month(d: datetime.date) -> datetime.date:
    ''' Returns a date one month past the given date'''
    last_day = calendar.monthrange(d.year, d.month)[1]
    cur_date = d.replace(day=last_day) + datetime.timedelta(days=1)

    # Using 15th of month ensures we can increment year at will
    cur_date = cur_date.replace(day=15)
    return cur_date

class NavyModel:
    ''' Data class to hold model state '''
    def __init__(self, billets:list, personnel:list, assignments:list = []):
        self.billets     = billets
        self.personnel   = personnel
        self.assignments = assignments

    def get_roller_pool(self, roll_on_before: datetime.date) -> list[dict[str]]:
        strdate = roll_on_before.isoformat()
        rollers = [x for x in self.personnel if x["PRD"] <= strdate]
        return rollers

    def pers_name(self, sailor: dict[str]) -> str:
        ''' method to return printable Sailor name '''
        rate     = sailor['RATE']
        short_id = sailor['DODID'][-5:]
        name     = sailor['NAME']
        return f"{rate} {name}/{short_id}"

    def run_step(self, m: datetime.date) -> None:
        ''' Simulates Navy HR operations for the current month '''

        billets = self.billets
        pers    = self.personnel
        print (f"Simulating {m.year}-{m.month:02d} with {len(billets)} billets and {len(pers)} personnel")

        # Remove separated Sailors
        m_date = m.isoformat()
        seps = [x for x in pers if x["EAOS"] <= m_date]
        pers = [x for x in pers if x["EAOS"] > m_date]

        for sep in seps:
            print(f"\t{self.pers_name(sep)} separated this month (EAOS: {sep['EAOS']})")

        # Transfer Sailors at PRD (remove billet assignment)
        # Process gains for Sailors en route next assignment (add billet assignment)
        # Process advancements (NWAE or BBA as appropriate)
        # Process accessions under current ADP
        # Process AVAILs from students in training, LIMDU, etc.
        # Process MNA cycle (prep or billet/roller pool match as appropriate)
        rollers = self.get_roller_pool(m.replace(year=m.year+1))
        print (f"\t{len(rollers)} rollers slated to rotate between now and a year from now")

        # Process re-enlistments

        self.billets, self.personnel = billets, pers

def read_billets(filename:str = 'billets.csv') -> None:
    ''' Reads in the given list of billets for the HR model simulation '''
    with open(filename, newline='') as csvfile:
        datareader = csv.DictReader(csvfile)
        return [row for row in datareader]

    raise OSError(f"Could not read {filename}")

def read_personnel(filename:str = 'personnel.csv') -> None:
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

    m = NavyModel(billets, pers)

    cur_date = datetime.date.today().replace(day=15)

    for _ in range(20):
        m.run_step(cur_date)
        cur_date = next_month(cur_date)

    sys.exit(0)
