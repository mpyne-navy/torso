#!/usr/bin/env python

import csv
import sys
import datetime
import calendar
import argparse

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
        self.detail      = True

        # Map BINs to billets and DODIDs to personnel
        self.by_bins = {x["BIN"]: x for x in self.billets}
        self.by_id   = {x["DODID"]: x for x in self.personnel}

    def show_detail(self, more_detail: bool = True) -> None:
        self.detail = more_detail
        pass

    def billet(self, bin: str) -> dict[str]:
        return self.by_bins[bin]

    def sailor(self, id: str) -> dict[str]:
        return self.by_id[id]

    def get_roller_pool(self, roll_on_before: datetime.date) -> list[dict[str]]:
        strdate = roll_on_before.isoformat()
        has_orders = set([x["DODID"] for x in self.assignments])

        def can_roll(s: dict[str]) -> bool:
            return s["ACC"] != 'A400' and s["PRD"] <= strdate and s["DODID"] not in has_orders

        return [x for x in self.personnel if can_roll(x)]

    def get_empty_billets(self, on_after: datetime.date) -> list[str]:
        ''' Returns the BINs of empty billets (that are or will be gapped without known replacement) '''
        strdate = on_after.isoformat()

        # TODO: Turn this into a DB query to speedup
        bins_to_be_gapped = set([x["LOSS_BIN"] for x in self.assignments if x["DETACH_DT"] >= strdate])
        bins_to_be_filled = set([x["GAIN_BIN"] for x in self.assignments if x["GAIN_DT"] >= strdate])
        bins_now_filled   = set([x["BIN"] for x in self.personnel])
        bins_available    = set([x["BIN"] for x in self.billets])
        bin_gaps = ((bins_available - bins_now_filled) | bins_to_be_gapped) - bins_to_be_filled

        return list(bin_gaps)

    def sailor_eligible_to_rotate_to(self, roller: dict[str], billet: dict[str]) -> bool:
        # TODO NEC checks
        pers_id = roller["DODID"]

        # Can't give them orders twice!
        if any(filter(lambda x: x["DODID"] == pers_id, self.assignments)):
            return False
        return roller["RATE"] == billet["RATE"] and roller["PGRADE"] == billet["PAYGRD"]

    def assign_sailor_to_billet(self, roller: dict[str], billet: dict[str],
                                m: datetime.date,
                                detach_on: datetime.date,
                                report_on: datetime.date) -> None:
        orders = {
                "DODID": roller["DODID"],
                "GAIN_BIN": billet["BIN"],
                "LOSS_BIN": roller["BIN"],
                "STATUS": "PENDING",
                "ORDERS_DT": m.isoformat(),
                "DETACH_DT": detach_on.isoformat(),
                "GAIN_DT": report_on.isoformat(),
                }
        self.assignments.append(orders)

    def detach_sailors_at_PRD(self, m: datetime.date) -> None:
        cur_date = m.isoformat()
        transients = [x for x in self.assignments if x["DETACH_DT"] <= cur_date and x['STATUS'] == 'PENDING']

        print (f"\t***** DETACHING {len(transients)} PERSONNEL ON ORDERS *****")

        for act_loss in transients:
            s = self.sailor(act_loss['DODID'])
            b = self.billet(act_loss['LOSS_BIN'])

            if self.detail:
                print (f"\t\tDetached {self.pers_name(s)} from {b['BIN']}")

            act_loss['STATUS'] = 'I/P'
            s['ACC'] = 'A400' # in transit
            s['PRD'] = ''
            s['UIC'] = ''
            s['BSC'] = '99990'
            s['BIN'] = ''

    def gain_sailors_at_EDA(self, m: datetime.date) -> None:
        cur_date = m.isoformat()
        transients = [x for x in self.assignments if cur_date >= x["GAIN_DT"] and x['STATUS'] == 'I/P']

        print (f"\t***** CHECKING-IN {len(transients)} ARRIVING PERSONNEL *****")

        for act_gain in transients:
            s = self.sailor(act_gain['DODID'])
            b = self.billet(act_gain['GAIN_BIN'])

            if self.detail:
                print (f"\t\tGained {self.pers_name(s)} to {b['BIN']}")

            act_gain['STATUS'] = 'GAINED'
            s['ACC'] = 'A100' # On board for duty
            s['PRD'] = m.replace(year=m.year + 3).isoformat()
            s['UIC'] = b['UIC']
            s['BSC'] = b['BSC']
            s['BIN'] = b['BIN']

        # Remove gained personnel from list of active orders
        self.assignments = [x for x in self.assignments if x["STATUS"] != 'GAINED']

    def run_mna_cycle(self, m: datetime.date) -> None:
        rollers = self.get_roller_pool(m.replace(year=m.year+1))
        bins = self.get_empty_billets(m)

        print (f"\t{len(rollers)} rollers slated to rotate to fill {len(bins)} gapped billets in MNA")

        num_matches = 0
        num_gaps    = 0

        billets = [self.billet(x) for x in bins]
        for billet in billets:
            # Find matching Sailor in roller pool if possible
            matched = False
            for roller in rollers:
                if self.sailor_eligible_to_rotate_to(roller, billet):
                    detach_dt = datetime.date.fromisoformat(roller["PRD"])
                    report_dt = next_month(detach_dt)
                    self.assign_sailor_to_billet(roller, billet, m, detach_dt, report_dt)
                    matched = True
                    num_matches = num_matches + 1
                    break

            if not matched:
                num_gaps = num_gaps + 1
                if self.detail:
                    print (f"\t\t*** UNABLE TO FIND ROLLER FOR BILLET {billet['BIN']} needing {billet['RATE']}")

        print (f"\t\t{num_matches} rollers assigned to billets, {num_gaps} billets left unfilled")

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
        return f"{rate:3} {name[:18]:18}/{short_id}"

    def separate_sailors_at_eaos(self, m: datetime.date) -> None:
        m_date = m.isoformat()
        pers = self.personnel
        seps = [x for x in pers if x["EAOS"] <= m_date]
        pers = [x for x in pers if x["EAOS"] > m_date]

        for s in seps:
            if self.detail:
                print(f"\t{self.pers_name(s)} separated this month (EAOS: {s['EAOS']})")
            self.assignments = [x for x in self.assignments if x['DODID'] != s['DODID']]

        self.personnel = pers

    def run_step(self, m: datetime.date) -> None:
        ''' Simulates Navy HR operations for the current month '''

        billets = self.billets
        pers    = self.personnel
        print (f"Simulating {m.year}-{m.month:02d} with {len(billets)} billets and {len(pers)} personnel")

        # Remove separated Sailors
        self.separate_sailors_at_eaos(m)
        self.detach_sailors_at_PRD(m)
        self.gain_sailors_at_EDA(m)

        # Process advancements (NWAE or BBA as appropriate)
        # Process accessions under current ADP
        # Process AVAILs from students in training, LIMDU, etc.
        self.run_mna_cycle(m)

        if self.detail:
            print ("\t***** PERSONNEL ON ORDERS *****")
            for orders in sorted(self.assignments, key=lambda x: x['DETACH_DT']):
                s = self.sailor(orders['DODID'])
                pers_id = self.pers_name(s)

                if s["ACC"] == 'A400':
                    print(f"\t\t{pers_id} has detached en route to BIN {orders['GAIN_BIN']} on {orders['GAIN_DT']}")
                else:
                    print(f"\t\t{pers_id} will rotate to BIN {orders['GAIN_BIN']} on {orders['GAIN_DT']}")

        # Process re-enlistments

def read_billets(filename:str) -> None:
    ''' Reads in the given list of billets for the HR model simulation '''
    with open(filename, newline='') as csvfile:
        datareader = csv.DictReader(csvfile)
        return [row for row in datareader]

    raise OSError(f"Could not read {filename}")

def read_personnel(filename:str) -> None:
    ''' Reads in the given list of personnel for the HR model simulation '''
    with open(filename, newline='') as csvfile:
        datareader = csv.DictReader(csvfile)
        return [row for row in datareader]

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Simulates a Navy HR model with recruiting, separation, and personnel distribution and advancement")
    parser.add_argument('-b', '--billets', default='billets.csv', type=str,
                        help="Input file for billets")
    parser.add_argument('-p', '--personnel', default='personnel.csv', type=str,
                        help="Input file for personnel when model starts")
    parser.add_argument('-d', '--detail', action="store_true",
                        help="Turn on individualized reporting for each model step")
    parser.add_argument('-s', '--random-seed', default=19920813, type=int,
                        help="Number to use to seed randomness generator")

    args = parser.parse_args()

    billets = read_billets(args.billets)

    if len(billets) <= 0:
        print ("Billet file empty")
        sys.exit(1)

    pers    = read_personnel(args.personnel)

    if len(billets) <= 0:
        print ("Personnel file empty")
        sys.exit(1)

    print (f"Read in {len(billets)} billets")
    print (f"Read in {len(pers)} personnel")

    m = NavyModel(billets, pers)
    m.show_detail(args.detail)

    cur_date = datetime.date.today().replace(day=15)

    for _ in range(5):
        m.run_step(cur_date)
        cur_date = next_month(cur_date)

    sys.exit(0)
