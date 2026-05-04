import os
import sqlite3

# Delete database
if os.path.exists('database.db'):
    os.remove('database.db')
    print("Deleted database.db")

# Delete any existing migrations or cache
if os.path.exists('instance'):
    import shutil
    shutil.rmtree('instance')
    print("Deleted instance folder")

print("Database has been reset. Now run: python app.py")