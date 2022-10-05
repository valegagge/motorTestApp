# -------------------------------------------------------------------------
# Copyright (C) 2022 iCub Tech - Istituto Italiano di Tecnologia
# Python script for acquiring data from DSP6001 Dynamometer Controller
#
# Written by A. Mura and V. Gaggero
# <andrea.mura@iit.it> <valentina.gaggero@iit.it>
# -------------------------------------------------------------------------

import sys, time
import serial.tools.list_ports as portlist
import serial
import logging
import datetime
import re
from threading import Thread
from threading import Event
import time
from motorBrakeDriver import MotorBrake as MotBrDriver
import matplotlib.pyplot as plt
from datetime import datetime
from termcolor import colored
from colorama import init

# -------------------------------------------------------------------------
# General
# -------------------------------------------------------------------------
filelog = 'dataDSP6001.txt'
titlelog = "#\tTime\tSpeed\tTorque\tRotation\n"
com_menu = 1
cmd_menu = 1
com_port = ''
# Answer format 'S    0T0.488R\r\n'


class dsp6001:
    def __init__(self, prog, time, speed, torque, rotation, freq):
        self.prog = prog
        self.time = time
        self.speed = speed
        self.torque = torque
        self.rotation = rotation
        self.freq = freq      
# -------------------------------------------------------------------------
# DSP6001 COMMAND SET
# -------------------------------------------------------------------------
dsp6001_cmd = [
    "*IDN?",         # Returns Magtrol Identification and software revision
    "OD",            # Prompts to return speed-torque-direction data string
    "PR",            # 
    "Q#",            # 
    "N#",            # 
    "Custom",        # 
    "Quit"           # Exit
    ]
dsp6001_end = "\r\n"

user_cmd = [
    "Get Magtrol Id and revision",
    "Start data acquisition on file",
    "Send torque setpoint",
    "Set speed setpoint",
    "Custom",
    "Quit"
]
MENU_CODE_NOT_VALID=-1
MENU_CODE_get_id=0
MENU_CODE_start_acq=1
MENU_CODE_set_trq=2
MENU_CODE_set_sp=3
MENU_CODE_custom=4
MENU_CODE_quit=5

user_menu = {
    MENU_CODE_get_id: {"code":MENU_CODE_get_id, "usrStr":"Get Magtrol Id and revision",    "MagtrolCode": "*IDN?"},
    MENU_CODE_start_acq: {"code":MENU_CODE_start_acq, "usrStr":"Start data acquisition on file", "MagtrolCode": "OD"},
    MENU_CODE_set_trq: {"code":MENU_CODE_set_trq, "usrStr":"Send torque setpoint",           "MagtrolCode": "Q"},
    MENU_CODE_set_sp: {"code":MENU_CODE_set_sp, "usrStr":"Send speed setpoint",            "MagtrolCode": "N"},
    MENU_CODE_custom: {"code":MENU_CODE_custom, "usrStr":"Custom",                         "MagtrolCode": ""},
    MENU_CODE_quit: {"code":MENU_CODE_quit, "usrStr":"Quit",                           "MagtrolCode": ""},
}

# -------------------------------------------------------------------------
# Data acquisition
# -------------------------------------------------------------------------
def data_acquisition(motor_br_dev):
    
    sample = []
    valid = False
    while not valid: #loop until the user enters a valid int
        try:
            print('-------------------------------------------------');
            print(colored('Enter number of samples:  ', 'green'), end='\b')
            sample_number = int(input())
            break
            valid = True
        except ValueError:
            print('Please only input digits')

    TX_messages = [cmd_menu+dsp6001_end]

    with open(filelog, 'w') as f:
        f.write(titlelog)


    with open(filelog, 'a') as f:
        for x in range(1, int(sample_number)+1):
            print('Message',x,'of',sample_number, end='\r')
            for msg in TX_messages:
                motor_br_dev.serialPort.write( msg.encode() )
                #-----------REMOVED FOR TEST ONLY!!! data = motor_br_dev.serialPort.readline().decode()
                # #data = "S    0T0.488R\r\n"      # fake message
                # if re.search("^S.+T.+R.+",data):
                #     dps6001_data = re.split("[S,T,R,L]", ''.join(data))
                #     date = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                #     sample.append(dsp6001(repr(x), date, dps6001_data[1], dps6001_data[2], data[12], "f"))
                #     f.write(sample[x-1].prog + '\t' + sample[x-1].time + '\t' + sample[x-1].speed + '\t' + sample[x-1].torque + '\t' + sample[x-1].rotation + '\t' + sample[x-1].freq + '\n')
                #--------------------------- 
                data = motor_br_dev.getData()
                print("torque=", data.torque, " speed= ", data.speed)     
    print(filelog,'ready')

    #plot_data(sample)


class MotorBrakeDataCollectorThread (Thread):
    def __init__(self, motor_br_dev, period, logOnFile, stopEvt):
        Thread.__init__(self)
        self.motor_br_dev = motor_br_dev
        self.period = period
        self.logOnFile = logOnFile
        self.stopEvt = stopEvt
        self.filelog = "MagtrolLog.txt"
    def run(self):
        print ("MotorBrakeDataCollectorThread is starting ")
        with open(filelog, 'w') as f:
            f.write("#\tTime\tSpeed\tTorque\tRotation\n")
        
        while True:
            if self.stopEvt.is_set():
                f.close()
                print ("MotorBrakeDataCollectorThread is closing...")
                break;
            
            motor_br_data = self.motor_br_dev.getDataFake()
            if self.logOnFile:
                with open(filelog, 'a') as f:
                    f.write(str(motor_br_data.progNum) + '\t' + motor_br_data.time + '\t' + str(motor_br_data.speed) + '\t' + str(motor_br_data.torque) + '\t' + motor_br_data.rotation + '\t' + '\n')
      
            #motor_br_data.printData()#print on screen
    #TODO: add a sleep to make this thread perioding. attention, take in account the time used by the w/r on serial port.   
    #TODO: add alive message      



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
    
# # -------------------------------------------------------------------------
# # Send command to Magtrol
# # -------------------------------------------------------------------------
# def send_cmd_magtrol(com_menu):
#     global com_port
#     TX_messages = [com_menu+dsp6001_end]
#     serialPort = open_serial_port(com_port)
#     for msg in TX_messages:
#         serialPort.write(msg.encode())
#         print(colored('\nMagtrol says:', 'yellow'), serialPort.readline().decode())
#     close_serial_port(serialPort, com_port) 
    
# # -------------------------------------------------------------------------
# # Open serial port
# # -------------------------------------------------------------------------
# def open_serial_port(com_port):
#     # Set up serial port for read
#     serialPort = serial.Serial(port=com_port, baudrate=9600, bytesize=8, timeout=1, stopbits=serial.STOPBITS_ONE)
#     #print('-------------------------------------------------');
#     #print('Starting Serial Port', com_port)
#     return serialPort

# # -------------------------------------------------------------------------
# # Close serial port
# # -------------------------------------------------------------------------
# def close_serial_port(serialPort, com_port):
#     #print('Closing Serial Port',com_port)
#     #print('-------------------------------------------------')
#     serialPort.close()

# -------------------------------------------------------------------------
# Scan COM ports
# -------------------------------------------------------------------------
def scan_com_port():

    global com_menu
    com_list = []
    print('-------------------------------------------------');
    print('Scan COM ports...')
    ports = list(portlist.comports())
    for p in ports:
      print('[',com_menu,']: ', p)
      com_menu+=1
      com_list.append(p.device)
    com_port = input_keyboard(com_list)
    return com_port
    
# -------------------------------------------------------------------------
# Input command
# -------------------------------------------------------------------------
def input_command():
    print('-------------------------------------------------');
    print('List of commands:')
    for p in user_menu:
      print('[',user_menu[p]["code"],']: ', user_menu[p]["usrStr"])
    cmd = inputKeyboard()
    return cmd 
    
# -------------------------------------------------------------------------
# Keyboard input
# -------------------------------------------------------------------------
def inputKeyboard():
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
    

def input_keyboard(list):
    valid = False
    #menu = 1
    while not valid: #loop until the user enters a valid int
        try:
            print(colored('Choose menu:  ', 'green'), end='\b')
            menu = int(input())
            if menu>=1 and menu<=len(list):
                menu = list[menu-1]
                return menu
                break
                valid = True
            else: 
                print('Please only input number in the brackets')
        except ValueError:
            print('Please only input digits')

# -------------------------------------------------------------------------
# main
# -------------------------------------------------------------------------
def main():
    init()
    cmd_menu = MENU_CODE_NOT_VALID
    print('-------------------------------------------------');
    print(colored('         MAGTROL DSP6001 control script          ', 'white', 'on_green'))
    chosen_com_port = scan_com_port()
    motor_br_dev = MotBrDriver(chosen_com_port, 9600)
    motor_br_dev.openSerialPort()
    stopDataCollectorEvt = Event()
    dataCollectorTh = MotorBrakeDataCollectorThread(motor_br_dev, 0,True,stopDataCollectorEvt)
    #tips: use match/case instead of if/elif
    while True:
        cmd_menu = input_command()

        if cmd_menu == MENU_CODE_start_acq:
            dataCollectorTh.start()
        elif cmd_menu == MENU_CODE_set_trq:
            print ("sending torque setpoint FAKE :P")
        elif cmd_menu == MENU_CODE_set_sp:
            print ("sending torque vale FAKE :P")
        elif cmd_menu == MENU_CODE_custom:
            print(colored('Type the command to send:  ', 'green'), end='\b')
            message_send = input()
            motor_br_dev.sendCommand(message_send)
        elif MENU_CODE_quit:
            if dataCollectorTh.is_alive():
                stopDataCollectorEvt.set()
                dataCollectorTh.join()
            motor_br_dev.closeSerialPort()
            break;
    



if __name__ == "__main__":
    main()
