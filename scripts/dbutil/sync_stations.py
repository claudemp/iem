# My purpose in life is to sync the mesosite stations table to other
# databases.  This will hopefully remove some hackery

import iemdb
import psycopg2
import psycopg2.extras
MESOSITE = iemdb.connect("mesosite")
subscribers = ["iem","coop","hads"]

def sync(dbname):
    """
    Actually do the syncing, please
    """
    # connect to synced database
    dbconn = iemdb.connect( dbname )
    dbcursor = dbconn.cursor()
    # query stations from source
    cur = MESOSITE.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""SELECT * from stations""")
    rows = cur.fetchall()
    cur.close()
    # delete current stations in dest
    dbcursor.execute("""DELETE from stations""")
    # insert queried stations
    dbcursor.executemany("""INSERT into stations(id, name, state,
     elevation, network, online, geom, params, county, plot_name, climate_site,
     wfo, archive_begin, archive_end, remote_id) values (%(id)s,
      %(name)s, %(state)s, %(elevation)s, %(network)s, %(online)s,
     %(geom)s, %(params)s, %(county)s, %(plot_name)s, %(climate_site)s,
     %(wfo)s, %(archive_begin)s, %(archive_end)s, %(remote_id)s)""",
     rows)
    # close connection
    dbcursor.close()
    dbconn.commit()
    dbconn.close()

for sub in subscribers:
    sync(sub)
MESOSITE.close()
