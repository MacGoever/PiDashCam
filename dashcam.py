#!/usr/bin/python

from gps import *
from time import *
import threading
import os
import math
from datetime import *
from libdashcam import *
import RPi.GPIO as GPIO

gpsp =  None
GPIOShutter = 6
GPIOAutoShutter = 5
GPIORed=19
GPIOGreen=20
GPIOBlue=21

if __name__ == '__main__':

    def triggerLED():
        GPIO.output(GPIOBlue, GPIO.HIGH) 
        sleep(.2)
        GPIO.output(GPIOBlue, GPIO.LOW) 


    GPIO.setmode(GPIO.BCM)
    GPIO.setup(GPIORed, GPIO.OUT) 
    GPIO.setup(GPIOGreen, GPIO.OUT) 
    GPIO.setup(GPIOBlue, GPIO.OUT) 



    gpsp = gpsPoller()
    gpsp.start()

    filename="/home/pi/gpx/" + datetime.strftime(datetime.utcnow(),"%Y-%m-%d_%H-%M-%S.gpx")
    gpxp = gpxWriter(gpsp, filename, 5 , 2, 10)
    gpxp.start()

    camera = photoTaker(gpsp, 300, "/home/pi/images/", True, triggerLED)

    #Control AutoShutter
    GPIO.setup(GPIOAutoShutter , GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def autoShutterStateChange(channel):
        sleep(0.1) #more debouncing
        camera.active=GPIO.input(GPIOAutoShutter)
        if camera.active:
            GPIO.output(GPIORed, GPIO.LOW) 
            GPIO.output(GPIOGreen, GPIO.HIGH) 
        else:
            GPIO.output(GPIORed, GPIO.HIGH) 
            GPIO.output(GPIOGreen, GPIO.LOW) 

    autoShutterStateChange(GPIOAutoShutter)
    GPIO.add_event_detect(GPIOAutoShutter, GPIO.BOTH, callback=autoShutterStateChange, bouncetime=500)

    camera.start() #Camera started delayd to find sate of autoShutter

    #Shutter
    GPIO.setup(GPIOShutter, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(GPIOShutter, GPIO.FALLING, callback=camera.instantImage, bouncetime=500)

    try:
        while 1:
            fix, utc=gpsp.getFix()

            if (False and fix != None and fix != None):
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

    
            sleep(1) #set to whatever

    except (KeyboardInterrupt, SystemExit): #when you press ctrl+c
        print "\nKilling GPX Writer..."
        gpxp.stop()
        gpxp.join()
        print ("GPX Writer finished")
        print "Killing Camera..."
        camera.stop()
        camera.join()
        print ("Camera finished")
        print "Killing GPS Poller..."
        gpsp.stop()
        gpsp.join() 
        print ("GPS Poller finished")
        print ("GPIO cleanup")
        GPIO.cleanup()
print "Done.\nExiting."
