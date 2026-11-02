# dahu-2

## Basic Info

The most critical folder is `user_data` and, more specifically, the `dahu_2.db`
file, as it store the whole database of the app. Never delete this file if 
you haven't copied it somewhere else before.

## Updating the App

### Set up a dev environment on your machine

1. Install Python 3.14
2. `git clone <repo-url>`
3. `cd dahu-2`
4. `python -m venv venv`
5. `venv\Scripts\activate`
6. `pip install -r requirements.txt` (to be created)
7. Get a copy of the database to test against — see "Get a dev copy of the
   data" below. Never point your dev app at the production database file.
8. `streamlit run pages/entry_point.py`
9. Check the app opens locally at http://localhost:8501

### Get a dev copy of the data (before touching real records)

1. On the production machine, find `user_data/dahu_2.db`
2. Copy that single file (not the whole folder) to your dev machine,
   into your dev copy's `user_data/` folder
3. Do NOT copy this file back to production — it's for testing only

### Only if you've added/deleted/modified a table/model in the DB

Model/class/table are synonyms in this context, as well as attribute/column. 
If you've changed the structure of the database (the "schema"), we have to 
apply what we call a "migration", which is a small script that executes
every step needed to change the schema.

#### Example

Let's imagine that in the model `TriodeSputtering` there's an attribute called 
`argon_flow`. After a few years, we realise we could use something different 
that argon. So, we want to split de column `argon_flow` into two separate 
columns: `flow` and `flow_composition`. To do that, here are the 
steps needed (what the migration script should do):
1. Create a new table called `TriodeSputterginNew` with the right columns.
2. Copy data from TriodeSputtering to TriodeSputteringNew, with the difference 
that the column `flow` is populated with the values of the previous columns 
`argon_flow` and the column `flow_composition` populated with `argon` 
everywhere.
3. Delete the table `TriodeSputtering`.
4. Rename the table `TriodeSputteringNew` to `TriodeSputtering`

At the step 3, because TriodeSputtering is deleted, all other models pointing
to it (we call these pointers "foreign keys") will break, which will lead to 
an error. That is why there is, in fact, step 0 which will disable the 
foreign key constraint to avoid this error. This will allow a foreign
key to point towards a row/insance that doesn't exist any more.

Then, at the end of the migration script, we re-enable this constraint 
(that's a step 5).

##### Corresponding Python/SQL code

```python
from playhouse.sqlite_ext import SqliteExtDatabase  # noqa

db = SqliteExtDatabase("user_data/yourapp.db")

with db.atomic():
    db.execute_sql("""
        CREATE TABLE triode_sputtering (
            id INTEGER PRIMARY KEY,
            flow REAL,
            flow_composition TEXT DEFAULT 'argon',
            -- ... rest of columns with corrected types/constraints
        )
    """)
    db.execute_sql("""
        INSERT INTO triode_sputtering_new 
            (id, flow, flow_composition, ...)
        SELECT 
            id, argon_flow, 'argon', ... 
        FROM triode_sputtering
    """)
    db.execute_sql("DROP TABLE triode_sputtering")
    db.execute_sql(
       "ALTER TABLE triode_sputtering_new RENAME TO triode_sputtering"
    )
db.execute_sql("PRAGMA foreign_keys=ON")
print("Migration complete")
```
We can notice that TriodeSputtering is automatically renamed triode_sputtering 
in the database by Peewee (Peewee is the library we use to interface Python with
the database). That's because it's the convention in the database management 
world. 

#### Test the migration on your dev copy

1. Make sure venv is active: source venv/bin/activate
2. Run: python migrations/2026_09_split_argon_flow.py
3. Check it printed "Migration complete" with no errors
4. Open the dev database file with DataGrip and confirm the data looks right.
5. Run streamlit run app.py and click through the app to confirm
   everything that touches triode_sputtering still works

Note: don't use DataGrip to edit data or the database schema, as 
reproducibility is impossible when modifications are done manually. This could
lead to errors. Manual edits could also lead to data incoherence because 
sometimes modifications must be done together (even though we try to limit 
these cases). Only use this software to read and explore the data.

### Deploy your changes to production

1. `pip freeze > requirements.txt` (to add a possible new library)
2. `git add requirements.txt`
3. git add . (your code and migration changes)
4. `git commit -m "<Changes made...>"`
5. `git push`
 
### Deploy to production

1. On the production machine, open a terminal
2. `cd ~/dahu-2`
3. `git pull`
4. `venv\Scripts\activate`
5. `pip install -r requirements.txt`
6. If this update includes a migration script, run it now, ONCE:
python migrations/2026_09_split_argon_flow.py
7. `streamlit run app.py`
8. Check it works


To update the app, create a Python virtuel env on your machine, download the
code base from GitHub and put it inside the virtual env. Install all required 
libraries using requirements.txt.

Copy-paste the Restic repository folder used in production to have a dev
version (so as not to break production backups). Update the Dahu DB config file
to indicate the new location of the repository.

Also copy-paste the database file to have a dev version of it. To do this, go
to the production code base and look for the .db file in the user data
folder. Copy it and paste it in the dev code base, at the same location.

When you finished your new version of the app, change the app version in the
config file.

## Contributing

### Common mistakes

#### Forms

If field or sub-form validation doesn't work, check if the field/sub-form calls
`super()__init__`.

#### Switch page

Don't use `st.switch_page` to go from current page P1 to another page P2 if
P1 has query parameters in its URL. The browser's back button
will not restore these parameters if the user wants to go back. This will
break navigation.

In this case, use `st.page_link`, which will open the page
in a new tab. That way, if the user wants to go back, they will simply close
the newly opened tab. Otherwise, put an HTML link.

The `switch_page_bttn` function handles this automatically by detecting current
query parameters. Just use this all the time.

#### Double page load

In the code of a page P1, don't import code from another page P2. 
If you do, when P1 loads, the import line will load P2. So navigating 
to P1 will load both pages one after another.

That is why we create component files, so that P1 and P2 can share 
code without loading one another.

### Minor changes

#### Units

If you want to change a unit, look for the field used to input data in the unit
you want to replace. Every form field is a class, so you should find the
corresponding class. Then, change the unit in the class declaration. Now, the
unit has been automatically changed across the whole app. Values in DB will
still be correctly converted because everything stored in the DB has its own
unit (which is SI) that is automatically converted to UI unit (from field
declarations) when retrieved.

# Other info

## Project and app name

Dabu DB is just the definitive name of Dahu 2. It's preferred to use Dahu DB.

## Libraries

Every film is associated to one and only one library, and vice versa. The concept of library is useful when we expect a film to produce the same measurements as anotherone. For example, if film A and film B both have the same thickness, this measurement will only by added to film A because it's be done on A, but film B's library will refer to it. Thus, we can summerise by saying that a library is a collection of measurements that have be done on a certain film, or could have been done on this film and would produce the same results.

## Patches

A patch is a piece of material we put on a target to obtain the composition we want on the target.

## Network

The app is set up on a desktop PC in a room of the lab, in the internal network of the lab. There is a restic repo on a distant server, for backups.

## Data

All the app data is in user_data/dahu_2.db, and all user files are in the same folder (user_data).

## Software engineering concepts

The documentation should provide a brief explanation of OOP and DBMS terminology for terms that are used in the doc, because readers will be physicists, not devs.

## Requirements

A requirements.txt file will be provided at the end of the developement.

## Run the app

The app is run with `streamlit run pages/entry_point.py`

## Setup

Install Python 3.14+

Set variables in dahu_2_config.py.

Install restic (Windows command: "winget install --exact --id restic.restic --scope Machine").

Connect with Windows' remote Desktop feature to the desktop PC hosting the app, to be able to operate on it remotely. (Lukas' desktop PC ID was "DESKTOP-QFQ4PL0".)

Check all os.environ access in Python code and fill them in Windows.


## Table Creation

Use the script located in Dahu 2 code base -> logic -> migrations -> table_creation.

## Terminology

- **User files folder**: folder that contains all files uploaded by users (target photos, film measurements, etc.), or generated files (processed measurement data, HDF5 files, etc.).

- **Database**: SQL database storing metadata.

- **App state**: union of user files and database data at a specific point in time.


## Restic Repository Creation

A repo is not a simple folder, so files cannot be accessed in it through the usual file explorer. It's more like a black box that stores backups in a smart versioned way, that must be accessed through command lines.

Initiate it with: `restic init --repo O:\path\to\backup\folder\` and the password 'no_password'.


### Regular File Backuping

We backup all user files once an hour.

However, everytime a snapshot is created, it's added to the set of all created snapshots. To avoid an infinite accumulation, we have to enter the following command to delete some snapshots:

`restic forget --keep-hourly 8 --keep-daily 7 --keep-weekly 6 --keep-monthly 5 --keep-yearly 1 --prune --repo O:\path\to\backup\folder\`

- Last 8 hours -> hourly snapshots
- Last 7 days -> one per day
- Last 6 weeks -> one per week
- Last 5 months -> one per month
- Last year -> one yearly

So, everytime we create a new backup (once an hour), we need to enter the above command to avoid excessive accumulation.

The max number of backups here is 27. It may seem like a lot but only the differences between each other are stored, so it will not take too much space.


## Database Backups

The SQL DB is dumped and added to the DAHU stored files folder right before every Restic snapshot. So, everytime the DAHU user files folder is backed up, the resulting snapshot will contain the state of the DB at that time. This allows us to restore the state of the whole DAHU app (DB + stored files) in a previous _coherent_ state.

## User Interface Failure

If the classes or their attributes changed over time, restoring the database might not work. The feature to restore a database to a point with different classes is a very complex feature. However, if you'd like to explore stored files from a past restore point and avoid restoration feature in UI, you can manualy use Restic. Use Restic to restore files from the desired snapshot to any folder that you want (see Restic documentation). Then, you can explore the files in this folder.

## Attribute choices

For each model, we chose to add an attribute if the attribute:

(must be searchable) 
OR (is frequently accessed) 
OR ((is not in uploaded files) AND (can change) AND (has an impact on measurements))
