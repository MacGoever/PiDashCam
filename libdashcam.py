#!/usr/bin/python

from gps import *
from time import *
import threading
import os
import math
from datetime import *
from picamera import PiCamera

class photoTaker(threading.Thread):
    def __init__(self, gpsp, interval, path, active, callBack):
        threading.Thread.__init__(self)
        self.gpsp = gpsp
        self.interval=interval
        self.path=path
        self.active = active
        self.callBack=callBack
        self.camera=PiCamera()
        self.camera.rotation = 180
        self.camera.resolution = (1920,1080)
        self.exit=threading.Event()

    def run (self):
        while not self.exit.is_set():
            if self.active:
                filename=self.path+datetime.strftime(datetime.utcnow(),"%Y-%m-%d_%H-%M-%S.jpg")
                self.camera.capture(filename)
                self.addEXIF(filename)
                self.callBack()

            self.exit.wait(self.interval)

    def stop (self):
        self.exit.set()

    def instantImage(self,channel):
        filename=self.path+"insta"+datetime.strftime(datetime.utcnow(),"%Y-%m-%d_%H-%M-%S.jpg")
        self.camera.capture(filename)
        self.addEXIF(filename)
        self.callBack()

    def addEXIF(self,filename):
        print("adding EXIF")

class gpsPoller(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.gpsd = gps(mode=WATCH_ENABLE)
        self.current_value=None
        self.running = True
        self.fixAge=0
        self.exit=threading.Event()

    def run(self):
        while not self.exit.is_set():
            self.gpsd.next()
            if (self.gpsd.fix.mode == MODE_NO_FIX): 
                self.fixAge = self.fixAge + 1
            else:
                self.fixAge=0
            self.exit.wait(0.9)

    def getFixPresent(self):
        return (not self.gpsd.fix.mode == MODE_NO_FIX)
        
    def getFix(self):
        if self.getFixPresent():
            return self.gpsd.fix, self.gpsd.utc
        else:
            return None, None

    def getSatellites(self):
            return self.gpsd.satellites

    def stop (self):
        self.exit.set()

    def getNumberOfSatellites(self):
            return len(self.gpsd.satellites)

    def getDistanceTravelled(self,oldLat,oldLon):
        deglen=110.25

        fix,utc=self.getFix()
        if fix == None:
            return 0
        else:
            #simplified distance calculation. Only suitable for distances < 5km 
            x = fix.latitude - oldLat
            y = (fix.longitude - oldLon) * math.cos(oldLat)
            distanceTravelled=deglen*math.sqrt(x*x + y*y) * 1000
            return distanceTravelled

class gpxWriter(threading.Thread):
    def __init__(self,gpsp, path,minDist,pollDelay,maxFixAge):
        threading.Thread.__init__(self)
        self.oldLon=0
        self.oldLat=0
        self.path=path
        self.pollDelay=pollDelay
        self.minDist=minDist
        self.gpsp=gpsp
        self.maxFixAge = maxFixAge
        self.utc=None
        self.fix=None
        self.exit=threading.Event()

    def writeWaypoint(self):
        with open(self.path, "a") as gpx_log:
		gpx_log.write("     <trkpt lat=\"{0}\" lon=\"{1}\">\n".format(self.fix.latitude, self.fix.longitude))
		gpx_log.write("         <time>{0}</time>\n".format(self.utc))
                if (self.fix.mode == MODE_2D ):
		    gpx_log.write("         <fix>2d</fix>\n")
                elif (self.fix.mode == MODE_3D ):
		    gpx_log.write("         <fix>3d</fix>\n")
		    gpx_log.write("         <ele>{0}</ele>\n".format(self.fix.altitude))
		gpx_log.write("         <sat>{0}</sat>\n".format(self.gpsp.getNumberOfSatellites()))
		gpx_log.write("     </trkpt>\n")


    def run(self):
        while (not self.exit.is_set() and (self.fix==None or self.utc==None) ):
            self.fix, self.utc=self.gpsp.getFix()
            self.exit.wait(self.pollDelay) 

        if (not self.exit.is_set()):
            with open(self.path, "w") as gpx_log:
                gpx_log.write("<?xml version=\"1.0\" encoding=\"utf-8\"?>\n")
		gpx_log.write(" <gpx version=\"1.1\" creator=\"dashcam.py\"\n")
		gpx_log.write("     xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"\n")
		gpx_log.write("     xmlns=\"http://www.topografix.com/GPX/1/1\"\n")
		gpx_log.write("     xsi:schemaLocation=\"http://www.topografix.com/GPX/1/1\n")
		gpx_log.write("     http://www.topografix.com/GPX/1/1/gpx.xsd\">\n")
		gpx_log.write(" <metadata>\n")
		gpx_log.write("     <time>{0}</time>\n".format(self.utc))
		gpx_log.write(" </metadata>\n")
		gpx_log.write(" <trk>\n")
		gpx_log.write("     <src>GPSD</src>\n")
		gpx_log.write("     <trkseg>\n")

            #write headers - timestamp
            self.writeWaypoint()
            self.oldLon=self.fix.longitude
            self.oldLat=self.fix.latitude
       
        while not self.exit.is_set():

            if (self.gpsp.getDistanceTravelled(self.oldLat,self.oldLon) > self.minDist):
                self.fix, self.utc=self.gpsp.getFix()
                if (not self.fix==None):
                    self.oldLon=self.fix.longitude
                    self.oldLat=self.fix.latitude
                    self.writeWaypoint() 

            if (self.gpsp.fixAge > self.maxFixAge):
                with open(self.path, "a") as gpx_log:
		    gpx_log.write("     </trkseg>\n")
		    gpx_log.write("     <trkseg>\n")
            self.exit.wait(self.pollDelay)

        with open(self.path, "a") as gpx_log:
                gpx_log.write("     </trkseg>\n");
                gpx_log.write("     </trk>\n");
                gpx_log.write("     </gpx>\n");

    def stop (self):
        self.exit.set()
