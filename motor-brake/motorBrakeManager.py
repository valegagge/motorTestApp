# -------------------------------------------------------------------------
# Copyright (C) iCub Tech - Istituto Italiano di Tecnologia (IIT)
#
# Python script for interacting with a motor brake device. 
# Currently we are using the Magtrol DSP6001 and its driver is in 
# src.motorBrakeDriver module
#
# Written by A. Mura and V. Gaggero
# <andrea.mura@iit.it> <valentina.gaggero@iit.it>
# -------------------------------------------------------------------------

from concurrent.futures import thread

import yarp
from threading import Thread
from threading import Event
from threading import Lock
from termcolor import colored
from colorama import init
import sys
import argparse
import time
import signal
from src.motorBrakeYarpCmdReader import MotorBrakeYarpCmdReader as yCmdReader
import src.motorBrakePromptMenu as menu
from src.MotorBrakeDataCollector import MotorBrakeDataCollectorThread
from src.motorBrakeDriver import MotorBrake as MotBrDriver
# -------------------------------------------------------------------------
# General
# -------------------------------------------------------------------------

# This is the entry point of the Motor Brake Manager.
# there is the definition of the class MotorBrakeManager, that is the core of this application:
# it initializes the motor brake device driver, the yarp network if necessary and all threads 
# for collecting data and reading commands by yarp ports
# The interaction with the hardware device is performed by the driver developed 
# in MotorBrakeDriver.py for the DSP6001 Dynamometer Controller





class MotorBrakeManager:
    #Inits the device driver, the yarp network and the other threads for collecting data and reading commands by yarp ports
    #Returns:
    # - 0 if all is ok
    # - 1 if serial opening fails
    # - 2 if yarp init fails
    def init(self, serialport, baudrate, yarpServiceOn, period, file):
        self.yarpServiceOn = yarpServiceOn
        #1. open the serial port and init the driver
        self.motor_br_dev = MotBrDriver(serialport, baudrate)
        ret = self.motor_br_dev.openSerialPort()
        if ret == False:
            return 1
        print ("Serial Port opened successfully")
        #2. start yarp network init
        if yarpServiceOn == True:
            yarp.Network.init()
            if not yarp.Network.checkNetwork():
                print("yarpserver is not running")
                return 2
            print ("yarp network init successfully")
        else:
            print ("yarp network is not available ")
        #3. Start the Data Collerctor and the Yarp Command Reader
        self.stopThreadsEvt = Event()
        self.lock = Lock()
        self.dataCollectorTh = MotorBrakeDataCollectorThread(self.motor_br_dev, self.stopThreadsEvt, self.lock, period, file, yarpServiceOn)
        self.yCmdReaderTh = yCmdReader(self.motor_br_dev, self.stopThreadsEvt, self.lock)
        if yarpServiceOn == True:
            self.yCmdReaderTh.start()  
        
        return 0

    def startAcquisition(self, filename):
        self.dataCollectorTh.setLogFileName(filename)
        self.dataCollectorTh.start()

    def stopAcquisition(self):
        if self.dataCollectorTh.is_alive():
            self.stopThreadsEvt.set()
            self.dataCollectorTh.join()

    def sendTorqueSetpoint(self, torque):
        with self.lock:
            self.motor_br_dev.sendTorqueSetpoint(torque)

    def sendSpeedSetpoint(self, speed):
        with self.lock:
            self.motor_br_dev.sendSpeedSetpoint(speed)

    def sendCustomCommand(self, command):
        with self.lock:
            self.motor_br_dev.sendCommand(command)

    def deinit(self):
        if self.dataCollectorTh.is_alive() or self.yCmdReaderTh.is_alive():
            self.stopThreadsEvt.set()
        if self.dataCollectorTh.is_alive():
            print("Waiting for data collector...")
            self.dataCollectorTh.join()
        if self.yCmdReaderTh.is_alive():
            print("Waiting for yCmdReader...")
            self.yCmdReaderTh.join()
        print("closing serial port")
        self.motor_br_dev.closeSerialPort()
        if self.yarpServiceOn:
            print("closing yarp network")
            yarp.Network.fini()
        print("All services are closed")        


# -------------------------------------------------------------------------
# parseInputArgument
# -------------------------------------------------------------------------
def parseInputArgument(argv):
    

    parser = argparse.ArgumentParser(description="Motor brake manager bla bla",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-y", "--yarpServiceOn", action="store_true", help="enable yarp service")
    parser.add_argument("-d", "--daemon", action="store_true", help="starting as daemon, without menu for user interaction")
    parser.add_argument("-f", "--file", default="", help="name of file where log data")
    parser.add_argument("-p", "--period", default=0.015, type=float,help="acquisition data period(seconds)")
    parser.add_argument("-s", "--serialPort", default='/dev/ttyUSB0', help="Serial port")
    parser.add_argument("-b", "--baudrate", default=19200, type=int, help="Serial port baud rate")
    args = parser.parse_args()
    config = vars(args)
    print(config)

    return args

# -------------------------------------------------------------------------
# runWithPromptMenu
# -------------------------------------------------------------------------
def runWithPromptMenu():
#tips: use match/case instead of if/elif
    while True:
        
        cmd_menu = menu.input_command()
        
        if cmd_menu == menu.MENU_CODE_start_acq:
            print(colored('insert log file name:  ', 'green'), end='\b')
            logFileName = input()
            brkManager.startAcquisition(logFileName)
        elif cmd_menu == menu.MENU_CODE_stop_acq:
            brkManager.stopAcquisition()
        elif cmd_menu == menu.MENU_CODE_set_trq:
            print(colored('Type the torque value to send:  ', 'green'), end='\b')
            torque = menu.inputFloatValue()
            brkManager.sendTorqueSetpoint(torque)
        elif cmd_menu == menu.MENU_CODE_set_sp:
            print(colored('Type the speed value to send:  ', 'green'), end='\b')
            speed = menu.inputFloatValue()
            brkManager.sendSpeedSetpoint(speed)
        elif cmd_menu == menu.MENU_CODE_custom:
            print(colored('Type the command to send:  ', 'green'), end='\b')
            message_send = input()
            brkManager.sendCustomCommand(message_send)
        elif cmd_menu == menu.MENU_CODE_quit:
            print ("Recived quit command")
            brkManager.deinit()
            print ("deinit finito")
            return;
        elif cmd_menu == menu.MENU_CODE_ena_disa_acqtiming:
            print(colored('Type 0 to disable or 1 to enable:  ', 'green'), end='\b')
            cmd = menu.inputIntValue()
            if cmd == 0:
                brkManager.motor_br_dev.disableAcquisitionTiming()
            elif cmd == 1:
                print(colored('Type the period in seconds:  ', 'green'), end='\b')
                period = menu.inputFloatValue()
                brkManager.motor_br_dev.enableAcquisitionTiming(period)
            else:
                print('Admited values: 0 (diable) and 1 (enable)')

# -------------------------------------------------------------------------
# runAsDaemon
# -------------------------------------------------------------------------
def runAsDaemon(args):
    brkManager.startAcquisition(args.file)
    while(True):
        time.sleep(0.1)

# -------------------------------------------------------------------------
# main
# -------------------------------------------------------------------------
brkManager = MotorBrakeManager();


def sigIntHandler(signum, frame) -> int:
    print ("Recived ctrl +c")
    brkManager.deinit()
    exit(1)
    
def main():
    
    init()

    print('-------------------------------------------------')
    print(colored('         Motor Brake Manager          ', 'white', 'on_green'))
    print('-------------------------------------------------')
    

    print(colored('ATTENTION: please check that the metric units on the device!!', 'white', 'on_cyan'))

    args = parseInputArgument(sys.argv)

    ret = brkManager.init(args.serialPort, args.baudrate,args.yarpServiceOn, args.period, args.file)
    #if ret == 0 all is ok
    if ret == 1:
        print(colored('ERROR: fail open the serial port!!', 'white', 'on_red'))
        #if it fails and not is running ad deamon a prompt menu is proposed to the user
        if args.daemon == False:
            chosen_com_port = scanComPort()
            if chosen_com_port == 0:
                print(colored('ERROR: I cannot open the serial port...exiting', 'white', 'on_red')) 
                return
            brkManager.init(args.serialPort, args.yarpServiceOn, args.period, args.file)
        else:
            return
    elif ret == 2:
        print(colored('ERROR: fail init yarp network!!', 'white', 'on_red'))
        return

    # set the handler of ctrl+c signal 
    signal.signal(signal.SIGINT, sigIntHandler)

    if args.daemon == False:
        runWithPromptMenu()
    else: 
        runAsDaemon(args)
    

if __name__ == "__main__":
    main()
