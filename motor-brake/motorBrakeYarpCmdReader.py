# -------------------------------------------------------------------------
# Copyright (C) 2022 iCub Tech - Istituto Italiano di Tecnologia
# Python script for acquiring data from DSP6001 Dynamometer Controller
#
# Written by V. Gaggero
# <valentina.gaggero@iit.it>
# -------------------------------------------------------------------------

from concurrent.futures import thread
import serial.tools.list_ports as portlist
import yarp
from threading import Thread
from threading import Event
from threading import Lock
from motorBrakeDriver import MotorBrake as MotBrDriver
import matplotlib.pyplot as plt
from termcolor import colored
from colorama import init
import sys
import argparse
import time


class DataProcessor(yarp.PortReader):
    def __init__(self, motor_br_dev, lock):
        super().__init__()
        self.lock = lock
        self.motor_br_dev = motor_br_dev
    
    def read(self,connection):
        #print("in DataProcessor.read")
        if not(connection.isValid()):
            print("MotorBrakeYarpCmdReader: connection not valid...closing")
            return False
        bin = yarp.Bottle()
        bout = yarp.Bottle()
        print("Trying to read from connection")
        ok = bin.read(connection)
        if not(ok):
            print("MotorBrakeYarpCmdReader: failed to read input")
            return False
        self.__parseCommand(bin.toString())
        #print("Received [%s]"%bin.toString())
        #removed rensponce
        # bout.addString("Received:")
        # bout.append(bin)
        # print("Sending [%s]"%bout.toString())
        # writer = connection.getWriter()
        # if writer==None:
        #     print("No one to reply to")
        #     return True
        # return bout.write(writer)
    

    def __parseCommand(self, strCmd):
        cmdList = strCmd.split()
        if len(cmdList)==0:
            return False
        if cmdList[0] == 'torque':
            val = float(cmdList[1])
            with self.lock:
                self.motor_br_dev.sendTorqueSetpoint(val)
            print("MotorBrakeYarpCmdReader sends torque=", val)
        elif  cmdList[0] == 'speed':
            val = float(cmdList[1])
            with self.lock:
                self.motor_br_dev.sendSpeedSetpoint(val)
            print("MotorBrakeYarpCmdReader sends speed=", val)
        else:
            print("MotorBrakeYarpCmdReader command unknown!! ", cmdList[0])
            return False
        
        return True






class MotorBrakeYarpCmdReader (Thread):
    def __init__(self, motor_br_dev, stopEvt, lock, period, logFileName, yarpSrvEnable):
        Thread.__init__(self)
        self.motor_br_dev = motor_br_dev
        self.period = period
        self.stopEvt = stopEvt
        self.filelog = logFileName
        self.yarpSrvEnable =yarpSrvEnable
        self.lock = lock
        self.yarpInputPort =yarp.Port()
        #self.yarpInputPort.open("/motorbrake/cmd:i")
        #self.yarpInputPort.setTimeout(1.0)
        self.dataProc = DataProcessor(motor_br_dev,lock)
        self.yarpInputPort.setReader(self.dataProc)
        self.yarpInputPort.open("/motorbrake/cmd:i")
        
    def run(self):
        print ("MotorBrakeYarpCmdReader is starting ")
        
        while True:
            if self.stopEvt.is_set():
                print ("MotorBrakeYarpCmdReader is closing...")
                self.yarpInputPort.close()
                break;
            
            print ("MotorBrakeYarpCmdReader i'm reading...")
            time.sleep(3)
            # bottle = yarp.Bottle()
            # self.yarpInputPort.read(bottle)
            # print("I read", bottle.toString())

            #with self.lock:
            #    motor_br_data = self.motor_br_dev.setData()

                 