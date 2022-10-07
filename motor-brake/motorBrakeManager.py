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

# -------------------------------------------------------------------------
# General
# -------------------------------------------------------------------------

# Answer format 'S    0T0.488R\r\n'



# -------------------------------------------------------------------------
# DSP6001 COMMAND SET
# -------------------------------------------------------------------------
MENU_CODE_NOT_VALID=-1
MENU_CODE_get_id=1
MENU_CODE_start_acq=2
MENU_CODE_stop_acq=3
MENU_CODE_set_trq=4
MENU_CODE_set_sp=5
MENU_CODE_custom=6
MENU_CODE_quit=7

user_menu = {
    MENU_CODE_get_id: {"code":MENU_CODE_get_id, "usrStr":"Get Magtrol Id and revision",    "MagtrolCode": "*IDN?"},
    MENU_CODE_start_acq: {"code":MENU_CODE_start_acq, "usrStr":"Start data acquisition", "MagtrolCode": "OD"},
    MENU_CODE_stop_acq: {"code":MENU_CODE_stop_acq, "usrStr":"Stop data acquisition", "MagtrolCode": ""},
    MENU_CODE_set_trq: {"code":MENU_CODE_set_trq, "usrStr":"Send torque setpoint",           "MagtrolCode": "Q"},
    MENU_CODE_set_sp: {"code":MENU_CODE_set_sp, "usrStr":"Send speed setpoint",            "MagtrolCode": "N"},
    MENU_CODE_custom: {"code":MENU_CODE_custom, "usrStr":"Custom",                         "MagtrolCode": ""},
    MENU_CODE_quit: {"code":MENU_CODE_quit, "usrStr":"Quit",                           "MagtrolCode": ""},
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
        if self.yarpSrvEnable ==True:
            self.yarpOutPort = yarp.BufferedPortBottle()
            self.yarpOutPort.open("/motorbrake/out")
    def run(self):
        print ("MotorBrakeDataCollectorThread is starting ")
        if self.filelog:
            with open(self.filelog, 'w') as f:
                f.write("#\tTime\tSpeed\tTorque\tRotation\n")
        
        while True:
            if self.stopEvt.is_set():
                if self.yarpSrvEnable ==True:
                    self.yarpOutPort.close()
                if self.filelog:
                    f.close()
                print ("MotorBrakeDataCollectorThread is closing...")
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
            time.sleep(self.period-thExeDuration) #go to sleep for remaing time

            #ATTENTION:
            #note about sleep function
            #Changed in version 3.5: The function now sleeps at least secs even if the sleep is interrupted by a signal,
            #except if the signal handler raises an exception (see PEP 475 for the rationale).
            #from: https://docs.python.org/3/library/time.html#time.sleep
                 
    
    #TODO: add alive message      
    def setLogFileName(self, fileName):
        self.filelog = fileName



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
# -------------------------------------------------------------------------
# parseInputArgument
# -------------------------------------------------------------------------


def parseInputArgument(argv):
    

    parser = argparse.ArgumentParser(description="Motor brake manager bla bla",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-y", "--yarpServiceOn", action="store_true", help="enable yarp service")
    parser.add_argument("-u", "--noPrompt", action="store_true", help="starting without menu for user interaction")
    parser.add_argument("-f", "--file", default="", help="name of file where log data")
    parser.add_argument("-p", "--period", default=0.1, type=int,help="acquisition data period(seconds)")
    parser.add_argument("-s", "--serialPort", default='/dev/ttyUSB0', help="Serial port")
    args = parser.parse_args()
    config = vars(args)
    print(config)

    return args





# -------------------------------------------------------------------------
# main
# -------------------------------------------------------------------------
def main():
    init()

    print('-------------------------------------------------')
    print(colored('         MAGTROL DSP6001 control script          ', 'white', 'on_green'))

    args = parseInputArgument(sys.argv)

    if args.yarpServiceOn:
        yarp.Network.init()

        if not yarp.Network.checkNetwork():
            print("yarpserver is not running")
            quit()
    


    cmd_menu = MENU_CODE_NOT_VALID
   
    chosen_com_port = scanComPort()
    if chosen_com_port == 0:
        return
    motor_br_dev = MotBrDriver(chosen_com_port, 9600)
    motor_br_dev.openSerialPort()
    stopDataCollectorEvt = Event()
    lock = Lock()
    dataCollectorTh = MotorBrakeDataCollectorThread(motor_br_dev, stopDataCollectorEvt, lock, args.period, args.file, args.yarpServiceOn)
    #tips: use match/case instead of if/elif
    while True:
        cmd_menu = input_command()

        if cmd_menu == MENU_CODE_start_acq:
            print(colored('insert log file name:  ', 'green'), end='\b')
            logFileName = input()
            dataCollectorTh.setLogFileName(logFileName)
            dataCollectorTh.start()
        elif cmd_menu == MENU_CODE_stop_acq:
            if dataCollectorTh.is_alive():
                stopDataCollectorEvt.set()
                dataCollectorTh.join()
        elif cmd_menu == MENU_CODE_set_trq:
            print(colored('Type the torque value to send:  ', 'green'), end='\b')
            torque = inputFloatValue()
            with lock:
                motor_br_dev.sendTorqueSetpoint(torque)
        elif cmd_menu == MENU_CODE_set_sp:
            print(colored('Type the speed value to send:  ', 'green'), end='\b')
            speed = inputFloatValue()
            with lock:
                motor_br_dev.sendTorqueSetpoint(speed)
        elif cmd_menu == MENU_CODE_custom:
            print(colored('Type the command to send:  ', 'green'), end='\b')
            message_send = input()
            with lock:
                motor_br_dev.sendCommand(message_send)
        elif MENU_CODE_quit:
            if dataCollectorTh.is_alive():
                stopDataCollectorEvt.set()
                dataCollectorTh.join()
            motor_br_dev.closeSerialPort()
            break;
    



if __name__ == "__main__":
    main()
