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
        self.fixAge=0

    def run(self):
        while self.running:
            self.gpsd.next()
            if (self.gpsd.fix.mode == MODE_NO_FIX): 
                self.fixAge = self.fixAge + 1
            else:
                self.fixAge=0
            sleep(1)

    def getFixPresent(self):
        return (self.fixAge == 0)
        
    def getFix(self):
        if self.getFixPresent():
            fix=self.gpsd.fix
            fix.speed=fix.speed*0.514444 #from knots to m/s
            return fix
        else:
            raise IOError("No GPS fix")

    def getFixWait(self):
        while not (self.getFixPresent()):
            sleep(.5) 
        fix=self.gpsd.fix
        fix.speed=fix.speed*0.514444 #from knots to m/s
        return fix

    def getUTC(self):
        if self.getFixPresent():
            return self.gpsd.utc
        else:
            raise IOError("No GPS fix")

    def getUTCWait(self):
        while not (self.getFixPresent()):
            sleep(.5) 
        return self.gpsd.utc

    def getSatellites(self):
            return self.gpsd.satellites

    def getNumberOfSatellites(self):
            return len(self.gpsd.satellites)

    def getDistanceTravelled(self,oldLat,oldLon):
        deglen=110.25
        try:
            fix=self.getFix()

            #simplified distance calculation. Only suitable for distances < 5km 
            x = fix.latitude - oldLat
            y = (fix.longitude - oldLon) * math.cos(oldLat)
            distanceTravelled=deglen*math.sqrt(x*x + y*y) * 1000
            return distanceTravelled
        except (IOError):
            return 0

class gpxWriter(threading.Thread):
    def __init__(self,gpsp, path,minDist,pollDelay,maxFixAge):
        threading.Thread.__init__(self)
        self.oldLon=0
        self.oldLat=0
        self.path=path
        self.pollDelay=pollDelay
        self.minDist=minDist
        self.gpsp=gpsp
        self.fix=self.gpsp.getFixWait()
        self.running = True
        self.maxFixAge = maxFixAge

    def writeWaypoint(self):
        with open(self.path, "a") as gpx_log:
		gpx_log.write("     <trkpt lat=\"{0}\" lon=\"{1}\">\n".format(self.fix.latitude, self.fix.longitude))
		gpx_log.write("         <ele>{0}</ele>\n".format(self.fix.altitude))
		gpx_log.write("         <time>{0}</time>\n".format(self.gpsp.getUTCWait()))
		gpx_log.write("         <fix>{0}</fix>\n".format(self.fix.mode))
		gpx_log.write("         <sat>{0}</sat>\n".format(self.gpsp.getNumberOfSatellites()))
                #These need to be calculated...
		#gpx_log.write("<hdop>{0}</hdop>\n".format(fix.))
		#gpx_log.write("<vdop>{0}</vdop>\n".format(fix.))
		#gpx_log.write("<pdop>{0}</pdop>\n".format(fix.))
		gpx_log.write("     </trkpt>\n")


    def run(self):
        with open(self.path, "w") as gpx_log:
                gpx_log.write("<?xml version=\"1.0\" encoding=\"utf-8\"?>\n")
		gpx_log.write(" <gpx version=\"1.1\" creator=\"dashcam.py\"\n")
		gpx_log.write("     xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"\n")
		gpx_log.write("     xmlns=\"http://www.topografix.com/GPX/1/1\"\n")
		gpx_log.write("     xsi:schemaLocation=\"http://www.topografix.com/GPX/1/1\n")
		gpx_log.write("     http://www.topografix.com/GPX/1/1/gpx.xsd\">\n")
		gpx_log.write(" <metadata>\n")
		gpx_log.write("     <time>{0}</time>\n".format(self.gpsp.getUTCWait()))
		gpx_log.write(" </metadata>\n")
		gpx_log.write(" <trk>\n")
		gpx_log.write("     <src>GPSD</src>\n")
		gpx_log.write("     <trkseg>\n")


        #write headers - timestamp
        self.writeWaypoint()
        self.oldLon=self.fix.longitude
        self.oldLat=self.fix.latitude
        
        while self.running:

            if (self.gpsp.getDistanceTravelled(self.oldLat,self.oldLon) > self.minDist):
                fix=self.gpsp.getFixWait()
                self.oldLon=fix.longitude
                self.oldLat=fix.latitude
                self.writeWaypoint() 

            if (self.gpsp.fixAge > self.maxFixAge):
                with open(self.path, "a") as gpx_log:
		    gpx_log.write("     </trkseg>\n")
		    gpx_log.write("     <trkseg>\n")
            
            sleep(self.pollDelay)

        with open(self.path, "a") as gpx_log:
                gpx_log.write("     </trkseg>\n");
                gpx_log.write("     </trk>\n");
                gpx_log.write("     </gpx>\n");
