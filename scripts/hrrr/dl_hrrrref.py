"""Download and archive 1000 ft reflectivity from the NCEP HRRR"""
from __future__ import print_function
import sys
import os
import logging
import datetime

import pytz
import pygrib
import requests
from pyiem.util import utc, exponential_backoff

# 18 hours of output + analysis
COMPLETE_GRIB_MESSAGES = 18 * 4 + 1


def upstream_has_data(valid):
    """Does data exist upstream to even attempt a download"""
    utcnow = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
    # NCEP should have at least 24 hours of data
    return (utcnow - datetime.timedelta(hours=24)) < valid


def run(valid):
    """ run for this valid time! """
    if not upstream_has_data(valid):
        return
    mydir = valid.strftime("/mesonet/ARCHIVE/data/%Y/%m/%d/model/hrrr/%H")
    if not os.path.isdir(mydir):
        os.makedirs(mydir)
    gribfn = valid.strftime(("/mesonet/ARCHIVE/data/%Y/%m/%d/model/hrrr/%H/"
                             "hrrr.t%Hz.refd.grib2"))
    if os.path.isfile(gribfn):
        # See how many grib messages we have
        try:
            grbs = pygrib.open(gribfn)
            if grbs.messages == COMPLETE_GRIB_MESSAGES:
                # print("%s is complete!" % (gribfn, ))
                return
            del grbs
        except Exception as exp:
            logging.debug(exp)
            pass
    output = open(gribfn, 'wb')
    for hr in range(0, 19):
        shr = "%02i" % (hr,)
        uri = valid.strftime(("http://www.ftp.ncep.noaa.gov/data/nccf/"
                              "com/hrrr/prod/"
                              "hrrr.%Y%m%d/hrrr.t%Hz.wrfsubhf" + shr +
                              ".grib2.idx"))
        req = exponential_backoff(requests.get, uri, timeout=30)
        if req is None or req.status_code != 200:
            print("dl_hrrrref failed to fetch %s" % (uri, ))
            print("ABORT")
            return
        data = req.content

        offsets = []
        neednext = False
        for line in data.split("\n"):
            if line.strip() == '':
                continue
            tokens = line.split(":")
            if neednext:
                offsets[-1].append(int(tokens[1]))
                neednext = False
            if tokens[3] == 'REFD' and tokens[4] == '1000 m above ground':
                offsets.append([int(tokens[1])])
                neednext = True

        if hr > 0 and len(offsets) != 4:
            print(("dl_hrrrref[%s] hr: %s offsets: %s"
                   ) % (valid.strftime("%Y%m%d%H"), hr, offsets))
        for pr in offsets:
            headers = {'Range': 'bytes=%s-%s' % (pr[0], pr[1])}
            req = exponential_backoff(requests.get, uri[:-4],
                                      headers=headers)
            if req is None:
                print("dl_hrrrref FAIL %s %s" % (uri[:-4], headers))
                continue
            output.write(req.content)

    output.close()


def main(argv):
    """ Go Main Go """
    valid = utc(int(argv[1]), int(argv[2]), int(argv[3]), int(argv[4]))
    run(valid)
    # in case we missed some old data, re-download
    run(valid - datetime.timedelta(hours=12))


if __name__ == '__main__':
    # do main
    main(sys.argv)
