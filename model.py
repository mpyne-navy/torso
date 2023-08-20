#!/usr/bin/env python

import csv
import sys
import datetime
import calendar

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

def run_model_step(m: datetime.date, billets: list[dict[str, str]], pers: list[dict[str, str]]):
    print (f"Simulating {m.year}-{m.month:02d} with {len(billets)} billets and {len(pers)} personnel")

    # Remove separated Sailors
    m_date = m.isoformat()
    seps = [x for x in pers if x["EAOS"] <= m_date]
    pers = [x for x in pers if x["EAOS"] > m_date]

    for sep in seps:
        print(f"\tSailor {sep['DODID']} separated this month (EAOS: {sep['EAOS']})")

    # Transfer Sailors at PRD (remove billet assignment)
    # Process gains for Sailors en route next assignment (add billet assignment)
    # Process advancements (NWAE or BBA as appropriate)
    # Process accessions under current ADP
    # Process AVAILs from students in training, LIMDU, etc.
    # Process MNA cycle (prep or billet/roller pool match as appropriate)
    # Process re-enlistments

    return billets, pers

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

    today = datetime.date.today()
    last_day = calendar.monthrange(today.year, today.month)[1]
    cur_date = today.replace(day=last_day)

    for _ in range(10):
        billets, pers = run_model_step(cur_date, billets, pers)

        # Python datetime has easy no way to say "the next month" so calculate
        # it manually.  Relies on cur_date already being the last day of the
        # month
        cur_date = cur_date + datetime.timedelta(days=1)
        last_day = calendar.monthrange(cur_date.year, cur_date.month)[1]
        cur_date = cur_date.replace(day=last_day)

    sys.exit(0)
