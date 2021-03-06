"""
Generate an animated GIF of HRRR forecasted 1km reflectivity

Run from RUN_40AFTER.sh and for the previous hour's HRRR run
"""
from __future__ import print_function
import datetime
import subprocess
import os
import sys

import pygrib
import numpy as np
import pytz
from pyiem.plot import MapPlot
import pyiem.reference as ref
from pyiem.util import utc


def compute_bounds(lons, lats):
    ''' figure out a minimum box to extract data from, save CPU '''
    dist = ((lats - ref.MW_NORTH)**2 + (lons - ref.MW_WEST)**2)**0.5
    x2, y1 = np.unravel_index(dist.argmin(), dist.shape)
    dist = ((lats - ref.MW_SOUTH)**2 + (lons - ref.MW_EAST)**2)**0.5
    x1, y2 = np.unravel_index(dist.argmin(), dist.shape)
    return x1 - 50, x2 + 40, y1 - 50, y2 + 40


def run(utc, routes):
    ''' Generate the plot for the given UTC time '''
    fn = utc.strftime(("/mesonet/ARCHIVE/data/%Y/%m/%d/model/hrrr/%H/"
                       "hrrr.t%Hz.refd.grib2"))

    grbs = pygrib.open(fn)

    subprocess.call("rm /tmp/hrrr_ref_???.gif", shell=True,
                    stderr=subprocess.PIPE, stdout=subprocess.PIPE)

    lats = None
    lons = None
    i = 0
    for minute in range(0, 18 * 60 + 1, 15):
        now = utc + datetime.timedelta(minutes=minute)
        now = now.astimezone(pytz.timezone("America/Chicago"))
        grbs.seek(0)
        try:
            gs = grbs.select(level=1000, forecastTime=minute)
        except ValueError:
            continue
        if lats is None:
            lats, lons = gs[0].latlons()
            x1, x2, y1, y2 = compute_bounds(lons, lats)
            lats = lats[x1:x2, y1:y2]
            lons = lons[x1:x2, y1:y2]

        reflect = gs[0]['values'][x1:x2, y1:y2]

        mp = MapPlot(sector='midwest', axisbg='tan',
                     title=('%s UTC NCEP HRRR 1 km AGL Reflectivity'
                            ) % (utc.strftime("%-d %b %Y %H"),),
                     subtitle=('valid: %s'
                               ) % (now.strftime("%-d %b %Y %I:%M %p %Z"),))

        mp.pcolormesh(lons, lats, reflect, np.arange(0, 75, 5), units='dBZ',
                      clip_on=False)
        mp.postprocess(filename='/tmp/hrrr_ref_%03i.png' % (i,))
        mp.close()

        subprocess.call(("convert /tmp/hrrr_ref_%03i.png "
                         "/tmp/hrrr_ref_%03i.gif") % (i, i), shell=True)

        i += 1

    # Generate anim GIF
    subprocess.call(("gifsicle --loopcount=0 --delay=50 "
                     "/tmp/hrrr_ref_???.gif > /tmp/hrrr_ref.gif"),
                    shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)

    pqstr = ("plot %s %s model/hrrr/hrrr_1km_ref.gif "
             "model/hrrr/hrrr_1km_ref_%02i.gif gif"
             ) % (routes, utc.strftime("%Y%m%d%H%M"), utc.hour)
    subprocess.call("/home/ldm/bin/pqinsert -p '%s' /tmp/hrrr_ref.gif" % (
                                                            pqstr,),
                    shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)

    os.remove("/tmp/hrrr_ref.gif")


def main(argv):
    """Go Main"""
    valid = utc(int(argv[1]), int(argv[2]), int(argv[3]), int(argv[4]))
    now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
    routes = 'a'
    if (now - valid) < datetime.timedelta(hours=2):
        routes = 'ac'

    run(valid, routes)


if __name__ == '__main__':
    # go go gadget
    main(sys.argv)
