#!/usr/bin/python

from gps import *
from time import *
import threading
import os
import math
from datetime import *

gpsd=None

class gpsPoller(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        global gpsd
        gpsd = gps(mode=WATCH_ENABLE)
        self.current_value=None
        self.running = True

    def run(self):
        global gpsd
        while self.running:
            gpsd.next()

class gpxWriter(threading.Thread):
    def __init__(self, path,minDist,pollDelay):
        threading.Thread.__init__(self)
        self.oldLon=0
        self.oldLat=0
        self.path=path
        self.pollDelay=pollDelay
        self.minDist=minDist

    def writeWaypoint(self):
        global gpsd

#   <trkpt lat="51.931957" lon="7.622663">
#    <ele>79.300000</ele>
#       <time>2018-04-04T13:31:12.000Z</time>
#           <fix>2d</fix>
#               <sat>4</sat>
#                   <hdop>2.3</hdop>
#                       <vdop>1.0</vdop>
#                           <pdop>2.5</pdop>
#                              </trkpt>


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




if __name__ == '__main__':
    gpsp = gpsPoller()
    gpsp.start()

    localTime = datetime.utcnow()
    gpsTime = None
    timeDiff=timedelta(seconds=10)

    try:

        
        while gpsd.fix.mode == MODE_NO_FIX or timeDiff.seconds == 0:
            print ("Waiting for fix and Timsync")
            try:    #In case no fix is present, the parsing would fail
                gpsTime = datetime.strptime(gpsd.utc, "%Y-%m-%dT%H:%M:%S.000Z")
                localTime = datetime.utcnow()
                timeDiff= localTime - gpsTime
            except:
                pass

            sleep(2)




        while 1:
            print
            print ' GPS reading'
            print '----------------------------------------'
            print 'latitude    ' , gpsd.fix.latitude
            print 'longitude   ' , gpsd.fix.longitude
            print 'time utc    ' , gpsd.utc,' + ', gpsd.fix.time
            print 'altitude (m)' , gpsd.fix.altitude
            print 'eps         ' , gpsd.fix.eps
            print 'epx         ' , gpsd.fix.epx
            print 'epv         ' , gpsd.fix.epv
            print 'ept         ' , gpsd.fix.ept
            print 'speed (m/s) ' , gpsd.fix.speed
            print 'climb       ' , gpsd.fix.climb
            print 'track       ' , gpsd.fix.track
            print 'mode        ' , gpsd.fix.mode
            print
            print 'sats        ' , gpsd.satellites
    
            sleep(1) #set to whatever

    except (KeyboardInterrupt, SystemExit): #when you press ctrl+c
        print "\nKilling Thread..."
        gpsp.running = False
        gpsp.join() # wait for the thread to finish what it's doing
print "Done.\nExiting."
