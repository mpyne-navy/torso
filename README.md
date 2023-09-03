# TORSO

TORSO is a simulator that attempts to provide an integrated model of enlisted
Navy HR personnel functions, including:

* Recruiting / Accessions
* Advancements (i.e. promotions)
* Separations and Retirements
* Distribution and orders (i.e. permanent changes of station)

# Installation

You should have Python 3 installed.  You should also have
[Pipenv](https://pipenv.pypa.io/en/latest/) installed so that it can setup
installation of the few dependencies (the 'Faker' module for fake data
handling).

If you have Faker setup you don't currently need Pipenv.

# Running

First off you need to have some sample data.  Run:

* `gen_billets.py` first, to generate fake manpower profiles to serve as the
  demand signal for Navy HR processes.
* Then run `gen_personnel.py` to generate the initial fake set of personnel in
  the modeled Navy.

From there you can run:

* `torso.py` to run the model itself.

# Copying and licensing

This software is open-source, under the [GPL v3](https://choosealicense.com/licenses/gpl-3.0/).

# Endorsements

This is **not affiliated with the U.S. Navy**, the U.S. Department of Defense
or any U.S. government agency.  It is developed in the author's personal
capacity on the author's own time and resources, and without the use of any
non-public or controlled information.

Nothing in this program is endorsed by the U.S. Department of Defense, U.S.
Navy or any government agency.

# Warning

I cannot stress enough how many pieces are still missing on this, especially
user-interface.  The only input is through command-line options to the 3
scripts listed above.  Output is whatever they spit out to the console, or to
the files you direct.

All scripts support being run with the `--help` option to explain more about
what each does.

# Author

Michael Pyne
