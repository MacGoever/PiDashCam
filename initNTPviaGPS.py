#!/usr/bin/python

from gps import *
from time import *
import threading
import os
import math
from datetime import *
from libdashcam import gpsPoller

gpsp =  None

if __name__ == '__main__':
    gpsp = gpsPoller()
    gpsp.start()

    localTime = datetime.utcnow()
    gpsTime = None
    timeDiff = timedelta(days=100)
    
    gpsMode = MODE_NO_FIX

    try:
        while (gpsMode == MODE_NO_FIX or timeDiff.seconds != 0):
            try:    #In case no fix is present, the parsing would fail
                gpsMode=gpsp.getFix().mode 
                gpsTime = datetime.strptime(gpsp.getUTC(), "%Y-%m-%dT%H:%M:%S.000Z")
                localTime = datetime.utcnow()
                timeDiff= localTime - gpsTime
            except:
                print "Waiting for sync..."
            sleep(1) #set to whatever

        print "GPS Sync done..."

    except (KeyboardInterrupt, SystemExit): #when you press ctrl+c
        pass

print "\nKilling Thread..."
gpsp.running = False
gpsp.join() # wait for the thread to finish what it's doing
print "Done.\nExiting."
