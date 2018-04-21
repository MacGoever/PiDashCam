#!/usr/bin/python

from gps import *
from time import *
import threading
import os
import math
from datetime import *

class gpsPoller(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.gpsd = gps(mode=WATCH_ENABLE)
        self.current_value=None
        self.running = True

    def run(self):
        while self.running:
            self.gpsd.next()
            sleep(.5)

    def getFixPresent(self):
        return (self.gpsd.fix.mode != MODE_NO_FIX)
        
    def getFix(self):
        if self.getFixPresent():
            return self.gpsd.fix
        else:
            raise IOError("No GPS fix")

    def getUTC(self):
        if self.getFixPresent():
            return gpsd.UTC
        else:
            raise IOError("No GPS fix")

    def getSatelites(self):
        if self.getFixPresent():
            return self.gpsd.satelites
        else:
            raise IOError("No GPS fix")

class gpxWriter(threading.Thread):
    def __init__(self, path,minDist,pollDelay):
        threading.Thread.__init__(self)
        self.oldLon=0
        self.oldLat=0
        self.path=path
        self.pollDelay=pollDelay
        self.minDist=minDist

    def writeWaypoint(self):
        global gpsp

        with open(self.path, "w") as gpx_log:
		gpx_log.write("<trkpt lat=\"{0}\" lon=\"{1}\">".format(gpsp.getFix().latitude, gpsd.getFix.longitude))
		gpx_log.write("<ele>{0}</ele>".format(gpsd.altitude))
		gpx_log.write("<time>2018-04-04T13:31:12.000Z</time>")
		gpx_log.write("<fix>2d</fix>")
		gpx_log.write("<sat>4</sat>")
		gpx_log.write("<hdop>2.3</hdop>")
		gpx_log.write("<vdop>1.0</vdop>")
		gpx_log.write("<pdop>2.5</pdop>")
		gpx_log.write("</trkpt>")


    def run(self):
        deglen=110.25
        global gpsd
        with open(self.path, "w") as gpx_log:
                gpx_log.write( "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n")
		gpx_log.write("<gpx version=\"1.1\" creator=\"dashcam.py\"\n")
		gpx_log.write("     xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"\n")
		gpx_log.write("xmlns=\"http://www.topografix.com/GPX/1/1\"\n")
		gpx_log.write("        xsi:schemaLocation=\"http://www.topografix.com/GPX/1/1\n")
		gpx_log.write("        http://www.topografix.com/GPX/1/1/gpx.xsd\">\n")
		gpx_log.write(" <metadata>\n")
		gpx_log.write("  <time>{0}</time>\n".format(gpsd.utc))
		gpx_log.write(" </metadata>\n")
		gpx_log.write(" <trk>\n")
		gpx_log.write("  <src>GPSD %s</src>\n", VERSION)
		gpx_log.write("  <trkseg>\n")



        #write headers - timestamp
        writeWaypoint()

        self.oldLon=gpsd.fix.longitude
        self.oldLat=gpsd.fix.latitude
        
        while self.running:
            #simplified distance calculation. Only suitable for distances < 5km 
            x = gpsd.fix.latitude - self.oldLat
            y = (gpsd.fix.longitude - self.oldLon) * math.cos(self.oldLat)
            distanceTraveled=deglen*math.sqrt(x*x + y*y) * 1000

            if (distanceTraveled > self.minDist):
                writeWaypoint()

            self.oldLon=gpsd.fix.longitude
            self.oldLat=gpsd.fix.latitude
            
            sleep(self.pollDelay)



#"  </trkseg>\n");
#" </trk>\n");
#"</gpx>\n");
