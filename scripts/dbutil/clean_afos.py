"""Clean up some tables that contain bloaty NWS Text Data

called from RUN_2AM.sh
"""
from __future__ import print_function

from pyiem.util import get_dbconn


def main():
    """Clean AFOS and friends"""
    pgconn = get_dbconn('afos')
    acursor = pgconn.cursor()

    acursor.execute("""
        delete from products WHERE
        entered < ('YESTERDAY'::date - '7 days'::interval) and
        entered > ('YESTERDAY'::date - '31 days'::interval) and
        (pil ~* '^(RR[1-9SA]|ROB|MAV|MET|MTR|MEX|RWR|STO|HML)'
         or pil in ('HPTNCF', 'WTSNCF','WRKTTU','TSTNCF', 'HD3RSA'))
        """)
    if acursor.rowcount == 0:
        print('clean_afos.py: Found no products to delete between 7-31 days')
    acursor.close()
    pgconn.commit()

    # Clean Postgis
    pgconn = get_dbconn('postgis')
    cursor = pgconn.cursor()

    cursor.execute("""DELETE from text_products where geom is null""")
    cursor.close()
    pgconn.commit()


if __name__ == '__main__':
    main()
