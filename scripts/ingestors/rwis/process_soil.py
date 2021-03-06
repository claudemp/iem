""" Process Soil Data"""
from __future__ import print_function
import csv
import psycopg2.extras
from pyiem.util import get_dbconn

DBCONN = get_dbconn('iem')


def load_metadata():
    """
    Load up what we know about these traffic sites
    """
    meta = {}
    cur = DBCONN.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""SELECT * from rwis_soil_data""")
    rows = cur.fetchall()
    cur.close()
    for row in rows:
        key = "%s_%s" % (row["location_id"], row["sensor_id"])
        meta[key] = True
    return meta


def create_sensor(row):
    """Create a sensor in the database please"""
    print(("Adding RWIS Soil Probe: %s Probe Level: %s"
           ) % (row["site_id"], row["sensor_id"]))
    cursor = DBCONN.cursor()
    cursor.execute("""INSERT into rwis_soil_data(location_id,
     sensor_id) VALUES (%s, %s)""", (row["site_id"], row["sensor_id"]))
    cursor.close()


def processfile(filename):
    """processfile"""
    meta = load_metadata()
    fp = open("/mesonet/data/incoming/rwis/%s" % (filename,), 'r')
    data = []
    for row in csv.DictReader(fp):
        key = "%s_%s" % (int(row["site_id"]), int(row["sensor_id"]))
        if key not in meta:
            create_sensor(row)
            meta = load_metadata()
        if row["temp"] == "":
            row["temp"] = None
        if row["moisture"] == "":
            row["moisture"] = None
        data.append(row)
    fp.close()

    cursor = DBCONN.cursor()
    cursor.execute("SET TIME ZONE 'UTC'")
    cursor.executemany("""
        UPDATE rwis_soil_data SET
        valid = %(obs_date_time)s, moisture = %(moisture)s, temp = %(temp)s
        WHERE sensor_id = %(sensor_id)s and location_id = %(site_id)s
        """, data)
    cursor.close()
    DBCONN.commit()
    DBCONN.close()


if __name__ == '__main__':
    processfile("DeepTempProbeFile.csv")
