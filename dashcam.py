#!/usr/bin/python

from gps import *
from time import *
import threading
import os
import math
from datetime import *
from libdashcam import *

gpsp =  None

if __name__ == '__main__':
    gpsp = gpsPoller()
    gpsp.start()

    filename=datetime.strftime(datetime.utcnow(),"%Y-%m-%d_%H-%M-%S.gpx")
    gpxp = gpxWriter(gpsp, filename, 1 , 5, 10)
    gpxp.start()

    try:
        while 1:
            try:
                fix=gpsp.getFix()
                utc=gpsp.getUTC()
                satellites=gpsp.getSatellites()
                print
                print ' GPS reading'
                print '----------------------------------------'
                print 'latitude    ' , fix.latitude
                print 'longitude   ' , fix.longitude
                print 'time utc    ' , utc,' + ', fix.time
                print 'altitude (m)' , fix.altitude
                print 'eps         ' , fix.eps
                print 'epx         ' , fix.epx
                print 'epv         ' , fix.epv
                print 'ept         ' , fix.ept
                print 'speed (m/s) ' , fix.speed
                print 'climb       ' , fix.climb
                print 'track       ' , fix.track
                print 'mode        ' , fix.mode
                print 'sats        ' , gpsp.getNumberOfSatellites()

            except (IOError):
                pass
    
            sleep(1) #set to whatever

    except (KeyboardInterrupt, SystemExit): #when you press ctrl+c
        print "\nKilling Thread..."
        gpxp.running = False
        gpxp.join()
        gpsp.running = False
        gpsp.join() # wait for the thread to finish what it's doing
print "Done.\nExiting."
