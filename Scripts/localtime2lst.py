#!/usr/bin/python

import sys
import ephem
from datetime import datetime
#from dateutil import tz
import pytz

# read local time; should be of the form "YYYY-mm-dd HH:MM:SS"
localTime = sys.argv[1]

# set observer's location
arecibo = ephem.Observer()
arecibo.lon = "-66:45:11.1"

# pyEphem requires time to be in UTC (even at observer's location!)
tempTime = datetime.strptime(localTime, "%Y-%m-%d %H:%M:%S")
#tempTime = tempTime.replace(tzinfo=tz.gettz("AST"))
tempTime = tempTime.replace(tzinfo=pytz.timezone("America/Puerto_Rico"))

utc = pytz.timezone('UTC')
universalTime = tempTime.astimezone(utc)
#universalTime = tempTime.astimezone(tz.gettz("UTC"))

# set observer's time
arecibo.date = universalTime

print arecibo.sidereal_time()

