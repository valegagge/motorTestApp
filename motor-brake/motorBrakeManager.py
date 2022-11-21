# -------------------------------------------------------------------------
# Copyright (C) 2022 iCub Tech - Istituto Italiano di Tecnologia
# Python script for acquiring data from DSP6001 Dynamometer Controller
#
# Written by A. Mura and V. Gaggero
# <andrea.mura@iit.it> <valentina.gaggero@iit.it>
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
import signal
from motorBrakeYarpCmdReader import MotorBrakeYarpCmdReader as yCmdReader

# -------------------------------------------------------------------------
# General
# -------------------------------------------------------------------------

# This is the entry point of the Motor Brake Manager.
# There is the definition of the main and all functions used for the 
# interaction with the user by the prompt menu. Moreover the class
# MotorBrakeDataCollectorThread id defined. As its name says, 
# it is a thread that collect the data from the motor-brake device and
# it dumps them on file and/or publish them on yarp port "/motorbrake/out"
# depending by its configuration.
# The interaction with the hardware device is performed by the driver developed 
# in MotorBrakeDriver.py for the DSP6001 Dynamometer Controller



# -------------------------------------------------------------------------
# Prompt menu definition
# -------------------------------------------------------------------------
MENU_CODE_NOT_VALID=-1
MENU_CODE_get_id=1
MENU_CODE_start_acq=2
MENU_CODE_stop_acq=3
MENU_CODE_set_trq=4
MENU_CODE_set_sp=5
MENU_CODE_custom=6
MENU_CODE_ena_disa_acqtiming=7
MENU_CODE_quit=8

user_menu = {
    MENU_CODE_get_id: {"code":MENU_CODE_get_id, "usrStr":"Get motor-brake device Id and revision"},
    MENU_CODE_start_acq: {"code":MENU_CODE_start_acq, "usrStr":"Start data acquisition"},
    MENU_CODE_stop_acq: {"code":MENU_CODE_stop_acq, "usrStr":"Stop data acquisition"},
    MENU_CODE_set_trq: {"code":MENU_CODE_set_trq, "usrStr":"Send torque setpoint [Nm]"},
    MENU_CODE_set_sp: {"code":MENU_CODE_set_sp, "usrStr":"Send speed setpoint [deg/sec]"},
    MENU_CODE_custom: {"code":MENU_CODE_custom, "usrStr":"Custom"},
    MENU_CODE_ena_disa_acqtiming: {"code":MENU_CODE_ena_disa_acqtiming, "usrStr":"Enable/disable acquisition timing"},
    MENU_CODE_quit: {"code":MENU_CODE_quit, "usrStr":"Quit"},
}

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


class MotorBrakeManager:
    #def __init__(self, motor_br_dev, stopEvt, lock, period, logFileName, yarpSrvEnable):

    #returns 0 if all is ok
    #returns 1 if serial opening fails
    #returns 2 if yarp init fails
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
# Plot data
# -------------------------------------------------------------------------
def plot_data(var):
    time = []
    torque = []
    speed = []
    for obj in var: time.append(obj.time)
    for obj in var: speed.append(obj.speed)
    for obj in var: torque.append(obj.torque)
    
    plt.plot(time, speed, label = "speed")
    plt.plot(time, torque, label = "torque")
    plt.xlabel('time [s]')
    plt.ylabel('[Nmm]')
    plt.title('MAGTROL data')
    plt.legend()
    plt.grid(True)
    plt.draw()
    plt.pause(2.001)
    #input("Press [enter] to continue.")
    #plt.show(block=False)  

# -------------------------------------------------------------------------
# Scan COM ports
# -------------------------------------------------------------------------
def scanComPort():
    com_menu = 1
    com_port = 0
    com_list = []
    print('-------------------------------------------------');
    print('Scan COM ports...')
    ports = list(portlist.comports())
    if len(ports) == 0:
        print("No serial port found. Exiting...")
        return com_port
    for p in ports:
      print('[',com_menu,']: ', p)
      com_menu+=1
      com_list.append(p.device)
    
    com_port = inputComPort(com_list)
    return com_port
    
# -------------------------------------------------------------------------
# Input command
# -------------------------------------------------------------------------
def input_command():
    print('-------------------------------------------------');
    print('List of commands:')
    for p in user_menu:
      print('[',user_menu[p]["code"],']: ', user_menu[p]["usrStr"])
    cmd = inputMenu()
    return cmd 
    
# -------------------------------------------------------------------------
# Keyboard input
# -------------------------------------------------------------------------
def inputMenu():
    while True: #loop until the user enters a valid int
        try:
            print(colored('Choose menu:  ', 'green'), end='\b')
            menu = int(input())
            if menu>=1 and menu<=len(user_menu):
                return user_menu[menu]["code"]
            else: 
                print('Please only input number in the brackets')
        except ValueError:
            print('Please only input digits')
    

def inputComPort(list):
    while True: #loop until the user enters a valid int
        try:
            print(colored('Choose menu:  ', 'green'), end='\b')
            port_id = int(input())
            
            if port_id>=1 and port_id<=len(list):
                menu = list[port_id-1]
                return menu
            else: 
                print('Please only input number in the brackets')
        except ValueError:
            print('Please only input digits')

def inputFloatValue():
    while True: #loop until the user enters a valid int
        try:
            val = float(input())
            return val
        except ValueError:
            print('Please only float values')
            return 0

def inputIntValue():
    while True: #loop until the user enters a valid int
        try:
            val = int(input())
            return val
        except ValueError:
            print('Please only integer values')
            return -1
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
# main
# -------------------------------------------------------------------------
brkManager = MotorBrakeManager();


def sigIntHandler(signum, frame) -> int:
    print ("Recived ctrl +c")
    brkManager.deinit()
    exit(1)
    
def main():
    
    init()
    cmd_menu = MENU_CODE_NOT_VALID

    print('-------------------------------------------------')
    print(colored('         Motor Brake Manager          ', 'white', 'on_green'))
    print('-------------------------------------------------')
    

    print(colored('ATTENTION: please check that the metric units on the device!!', 'white', 'on_cyan'))

    args = parseInputArgument(sys.argv)

    print ("args.baudrate=", args.baudrate)
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
        #tips: use match/case instead of if/elif
        while True:
            
            cmd_menu = input_command()
            
            if cmd_menu == MENU_CODE_start_acq:
                print(colored('insert log file name:  ', 'green'), end='\b')
                logFileName = input()
                brkManager.startAcquisition(logFileName)
            elif cmd_menu == MENU_CODE_stop_acq:
                brkManager.stopAcquisition(l)
            elif cmd_menu == MENU_CODE_set_trq:
                print(colored('Type the torque value to send:  ', 'green'), end='\b')
                torque = inputFloatValue()
                brkManager.sendTorqueSetpoint(torque)
            elif cmd_menu == MENU_CODE_set_sp:
                print(colored('Type the speed value to send:  ', 'green'), end='\b')
                speed = inputFloatValue()
                brkManager.sendSpeedSetpoint(speed)
            elif cmd_menu == MENU_CODE_custom:
                print(colored('Type the command to send:  ', 'green'), end='\b')
                message_send = input()
                brkManager.sendCustomCommand(message_send)
            elif cmd_menu == MENU_CODE_quit:
                print ("Recived quit command")
                brkManager.deinit()
                print ("deinit finito")
                return;
            elif cmd_menu == MENU_CODE_ena_disa_acqtiming:
                print(colored('Type 0 to disable or 1 to enable:  ', 'green'), end='\b')
                cmd = inputIntValue()
                if cmd == 0:
                    brkManager.motor_br_dev.disableAcquisitionTiming()
                elif cmd == 1:
                    print(colored('Type the period in seconds:  ', 'green'), end='\b')
                    period = inputFloatValue()
                    brkManager.motor_br_dev.enableAcquisitionTiming(period)
                else:
                    print('Admited values: 0 (diable) and 1 (enable)')
    else: # running as daemon
        brkManager.startAcquisition(args.file)
        while(True):
            time.sleep(0.1)
    
    print ("sto per uscire")
    return

if __name__ == "__main__":
    main()
