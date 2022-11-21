# -------------------------------------------------------------------------
# Copyright (C) 2022 iCub Tech - Istituto Italiano di Tecnologia
#
# here the class MotorBrakeDataCollectorThread id defined. As its name says, 
# it is a thread that collect the data from the motor-brake device and
# it dumps them on file and/or publish them on yarp port "/motorbrake/out"
# depending by its configuration.
# The interaction with the hardware device is performed by the driver developed 
# in MotorBrakeDriver.py for the DSP6001 Dynamometer Controller
#
# Written by V. Gaggero
# <valentina.gaggero@iit.it>
# -------------------------------------------------------------------------

import yarp
from threading import Thread
from threading import Event
from threading import Lock
from src.motorBrakeDriver import MotorBrake as MotBrDriver
import time
# -------------------------------------------------------------------------
# Data acquisition
# -------------------------------------------------------------------------

class MotorBrakeDataCollectorThread (Thread):
    def __init__(self, motor_br_dev, stopEvt, lock, period, logFileName, yarpSrvEnable):
        Thread.__init__(self)
        self.motor_br_dev = motor_br_dev
        self.period = period
        self.stopEvt = stopEvt
        self.filelog = logFileName
        self.yarpSrvEnable =yarpSrvEnable
        self.lock = lock
        if self.yarpSrvEnable == True:
            self.yarpOutPort = yarp.BufferedPortBottle()
            self.yarpOutPort.open("/motorbrake/out")
    def run(self):
        print ("MotorBrakeDataCollector is starting ")
        if self.filelog:
            with open(self.filelog, 'w') as f:
                f.write("#\tTime\tSpeed[deg/sec]\tTorque[Nm]\tRotation[R or L]\n")
        
        while True:
            if self.stopEvt.is_set():
                if self.yarpSrvEnable ==True:
                    self.yarpOutPort.close()
                if self.filelog:
                    f.close()
                print ("MotorBrakeDataCollector is closing...")
                break;
            start_time = time.time()
            with self.lock:
                motor_br_data = self.motor_br_dev.getData()

            if self.filelog:
                with open(self.filelog, 'a') as f:
                    f.write(str(motor_br_data.progNum) + '\t' + motor_br_data.time + '\t' + str(motor_br_data.speed) + '\t' + str(motor_br_data.torque) + '\t' + motor_br_data.rotation + '\t' + '\n')
            if self.yarpSrvEnable ==True:
                bottle = self.yarpOutPort.prepare()
                bottle.clear()
                bottle.addFloat32(motor_br_data.speed)
                bottle.addFloat32(motor_br_data.torque)
                bottle.addString(motor_br_data.rotation) #R is Clockwise dynamometer shaft rotation (right), while L is Counterclockwise dynamometer shaft rotation (left).
                self.yarpOutPort.write()
            thExeDuration = time.time() - start_time
            #print("MotorBrakeDataCollectorThread: exetime=", thExeDuration, "sleep for", self.period-thExeDuration)
            sleep_time = self.period-thExeDuration
            if sleep_time>0:
                time.sleep(sleep_time) #go to sleep for remaing time

            #ATTENTION:
            #note about sleep function
            #Changed in version 3.5: The function now sleeps at least secs even if the sleep is interrupted by a signal,
            #except if the signal handler raises an exception (see PEP 475 for the rationale).
            #from: https://docs.python.org/3/library/time.html#time.sleep
                 
    
    #TODO: add alive message      
    def setLogFileName(self, fileName):
        self.filelog = fileName
