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
    ''' Data class to hold model state

        Billets is a table of:
            BIN  UIC  BSC  TITLE  TYPE  RATE  PAYGRD  NEC1  NEC2

            BIN is unique.  UIC/BSC combination is unique.

        Personnel is a table of:
            DODID  NAME  RATE  PGRADE  NEC1  NEC2  ADSD  EAOS  PRD  UIC  BSC  BIN  ACC

            DODID is unique.
            BIN is unique and is a foreign key relation to Billets table.
            UIC/BSC combination is unique and is an FK relation to Billets.
            BIN and UIC/BSC combo should point to the exact same row in Billets.
            NEC1 and NEC2 should not equal the other except if they are 0000.
            ADSD should always be ≤ EAOS
            PRD should always be ≤ EAOS

        Assignments is a table of:
            DODID  GAIN_BIN  LOSS_BIN  DETACH_DT  GAIN_DT

            DODID is unique.
            DETACH_DT should always be ≤ GAIN_DT
    '''
    def __init__(self, billets:list, personnel:list, assignments:list = []):
        self.billets     = billets
        self.personnel   = personnel
        self.assignments = assignments

    def get_roller_pool(self, roll_on_before: datetime.date) -> list[dict[str]]:
        strdate = roll_on_before.isoformat()
        has_orders = set([x["DODID"] for x in self.assignments])
        rollers = [x for x in self.personnel if x["PRD"] <= strdate]
        rollers = [x for x in rollers if x["DODID"] not in has_orders]
        return rollers

    def get_empty_billets(self, on_after: datetime.date) -> list[str]:
        ''' Returns the BINs of empty billets (that are or will be gapped without known replacement) '''
        # TODO: Use the on or after date?
        strdate = on_after.isoformat()

        # TODO: Turn this into a DB query to speedup
        bins_to_be_gapped = set([x["LOSS_BIN"] for x in self.assignments])
        bins_to_be_filled = set([x["GAIN_BIN"] for x in self.assignments])
        bins_now_filled   = set([x["BIN"] for x in self.personnel])
        bins_available    = set([x["BIN"] for x in self.billets])
        bin_gaps = ((bins_available - bins_now_filled) | bins_to_be_gapped) - bins_to_be_filled

        return list(bin_gaps)

    def sailor_eligible_to_rotate_to(self, roller: dict[str], billet: dict[str]) -> bool:
        # TODO NEC checks
        return roller["RATE"] == billet["RATE"] and roller["PGRADE"] == billet["PAYGRD"]

    def assign_sailor_to_billet(self, roller: dict[str], billet: dict[str], detach_on: datetime.date, report_on: datetime.date) -> None:
        orders = {
                "DODID": roller["DODID"],
                "GAIN_BIN": billet["BIN"],
                "LOSS_BIN": roller["BIN"],
                "DETACH_DT": detach_on.isoformat(),
                "GAIN_DT": report_on.isoformat(),
                }
        self.assignments.append(orders)

    def run_mna_cycle(self, m: datetime.date) -> None:
        rollers = self.get_roller_pool(m.replace(year=m.year+1))
        print (f"\t{len(rollers)} rollers slated to rotate between now and a year from now")

        bins = self.get_empty_billets(m)
        print (f"\t{len(bins)} gapped billets to fill in MNA")

        billets = [x for x in self.billets if x["BIN"] in bins]

        for billet in billets:
            # Find matching Sailor in roller pool if possible
            for roller in rollers:
                if self.sailor_eligible_to_rotate_to(roller, billet):
                    detach_dt = datetime.date.fromisoformat(roller["PRD"])
                    report_dt = next_month(detach_dt)
                    self.assign_sailor_to_billet(roller, billet, detach_dt, report_dt)
                    break

        # Look for business logic errors
        # Look for duplicate orders to same billet
        gaining_bins = [x["GAIN_BIN"] for x in self.assignments]
        gain_counts = set()
        for bin in gaining_bins:
            if bin in gain_counts:
                print(f"\tError: *** BIN {bin} IS DUPLICATED IN TABLE OF ASSIGNMENTS!")
            gain_counts.add(bin)

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
        self.run_mna_cycle(m)
        print ("\t***** ORDERS TO PERSONNEL *****")
        for orders in self.assignments:
            print(f"\t\t{orders['DODID']} will rotate to BIN {orders['GAIN_BIN']} on {orders['GAIN_DT']}")

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
