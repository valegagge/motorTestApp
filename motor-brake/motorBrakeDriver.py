# -------------------------------------------------------------------------
# Copyright (C) 2022 iCub Tech - Istituto Italiano di Tecnologia
# This module is the driver for interacting with motor brake.
#
# Valentina Gaggero
# <valentina.gaggero@iit.it>
# -------------------------------------------------------------------------

import sys, time
from numpy import False_
import serial.tools.list_ports as portlist
import serial
import logging
import datetime
import re

import matplotlib.pyplot as plt
from datetime import datetime
from termcolor import colored
from colorama import init

# -------------------------------------------------------------------------
# General
# -------------------------------------------------------------------------
com_menu = 1
cmd_menu = 1
com_port = ''
# Answer format 'S    0T0.488R\r\n'

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



class MotorBrakeCfg:
    def __init__(self, comport, baudrate=9600):
        self.comport=comport
        self.baudrate=baudrate

class MotorBrakeOuputData:
    def __init__(self) -> None:
        self.torque=0.0
        self.speed=0.0
        self.rotation="-"
        self.time = "::"
        self.progNum=0
    def printData(self):
        print(self.time, " torque=", self.torque, " speed= ", self.speed, "rotation=", self.rotation)



#note: how to manage error??? see here https://stackoverflow.com/questions/45411924/python3-two-way-serial-communication-reading-in-data
class MotorBrake:
    "put here the class documentation"

    def __init__(self, comport, baudrate):
        self.cfg=MotorBrakeCfg(comport, baudrate) #is it usefull??
        self.mydata = MotorBrakeOuputData()
        self.serialPort = serial.Serial()
        self.serialPort.baudrate = self.cfg.baudrate
        self.serialPort.port = self.cfg.comport
        self.serialPort.bytesize = 8
        self.serialPort.timeout = 1
        self.serialPort.stopbits = serial.STOPBITS_ONE
        #self.initted=False
    def openSerialPort(self):
        # Set up serial port for read
         
        if not self.serialPort.is_open:
            self.serialPort.open()
            # = serial.Serial(self.cfg.comport, self.cfg.baudrate, bytesize=8, timeout=1, stopbits=serial.STOPBITS_ONE)
            #print('-------------------------------------------------');
            #print('Starting Serial Port', com_port)
    def getDataFake(self):
        self.mydata.torque += 1
        self.mydata.speed +=1
        return self.mydata # check return value or reference
    def getData(self):
        cmd_menu="OD"
        TX_messages = [cmd_menu+dsp6001_end]
        for msg in TX_messages:
            self.serialPort.write( msg.encode() )
        data = self.serialPort.readline().decode()
        if re.search("^S.+T.+R.+",data):
            data_split_str = re.split("[S,T,R,L]", ''.join(data))
            date = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            self.mydata.speed = float(data_split_str[1])
            self.mydata.torque = float(data_split_str[2])
            self.mydata.rotation = data[12]
            self.mydata.time = date
            self.progNum +=1

        return self.mydata # check return value or reference
    
    def closeSerialPort(self):
        #print('Closing Serial Port',com_port)
        #print('-------------------------------------------------')
        if self.serialPort.is_open:
            self.serialPort.close()
    def sendCommand(self, command):
        if self.serialPort.is_open:
            try:
                TX_messages = [command+dsp6001_end]
                for msg in TX_messages:
                    self.serialPort.write(msg.encode())
                    print(colored('\nMagtrol says:', 'yellow'), self.serialPort.readline().decode())
                    return True
            except Exception as e:
                print ("Error communicating...: " + str(e))
                return False
        else:
            print ("Cannot open serial port.")
            return False



        


# # -------------------------------------------------------------------------
# # Data acquisition
# # -------------------------------------------------------------------------
# def data_acquisition():
#     global com_port
#     sample = []
#     valid = False
#     while not valid: #loop until the user enters a valid int
#         try:
#             print('-------------------------------------------------');
#             print(colored('Enter number of samples:  ', 'green'), end='\b')
#             sample_number = int(input())
#             break
#             valid = True
#         except ValueError:
#             print('Please only input digits')

#     TX_messages = [cmd_menu+dsp6001_end]

#     with open(filelog, 'w') as f:
#         f.write(titlelog)

#     serialPort = open_serial_port(com_port)
#     p = yarp.BufferedPortBottle()
#     p.open("/motorbrake/out")

#     with open(filelog, 'a') as f:
#         for x in range(1, int(sample_number)+1):
#             print('Message',x,'of',sample_number, end='\r')
#             for msg in TX_messages:
#                 serialPort.write( msg.encode() )
#                 data = serialPort.readline().decode()
#                 #data = "S    0T0.488R\r\n"      # fake message
#                 if re.search("^S.+T.+R.+",data):
#                     dps6001_data = re.split("[S,T,R,L]", ''.join(data))
#                     date = datetime.now().strftime("%H:%M:%S.%f")[:-3]
#                     sample.append(dsp6001(repr(x), date, dps6001_data[1], dps6001_data[2], data[12], "f"))
#                     f.write(sample[x-1].prog + '\t' + sample[x-1].time + '\t' + sample[x-1].speed + '\t' + sample[x-1].torque + '\t' + sample[x-1].rotation + '\t' + sample[x-1].freq + '\n')
#                     bottle = p.prepare()
#                     bottle.clear()
#                     bottle.addFloat32(float(sample[x-1].speed))
#                     bottle.addFloat32(float(sample[x-1].torque))
#                     bottle.addString(sample[x-1].rotation) #R is Clockwise dynamometer shaft rotation (right), while L is Counterclockwise dynamometer shaft rotation (left).
#                     bottle.addString(sample[x-1].freq)
#                     p.write()    
                    
#     close_serial_port(serialPort, com_port)    
#     print(filelog,'ready')

#     #plot_data(sample)
    





# # -------------------------------------------------------------------------
# # Scan COM ports
# # -------------------------------------------------------------------------
# def scan_com_port():
#     global com_port
#     global com_menu
#     com_list = []
#     print('-------------------------------------------------');
#     print('Scan COM ports...')
#     ports = list(portlist.comports())
#     for p in ports:
#       print('[',com_menu,']: ', p)
#       com_menu+=1
#       com_list.append(p.device)
#     com_port = input_keyboard(com_list)
    
# # -------------------------------------------------------------------------
# # Input command
# # -------------------------------------------------------------------------
# def input_command():
#     global cmd_menu
#     cmd_menu=1
#     print('-------------------------------------------------');
#     print('List of commands:')
#     for p in dsp6001_cmd:
#       print('[',cmd_menu,']: ', p)
#       cmd_menu+=1
#     cmd_menu = input_keyboard(dsp6001_cmd)
    
# # -------------------------------------------------------------------------
# # Keyboard input
# # -------------------------------------------------------------------------
# def input_keyboard(list):
#     valid = False
#     #menu = 1
#     while not valid: #loop until the user enters a valid int
#         try:
#             print(colored('Choose menu:  ', 'green'), end='\b')
#             menu = int(input())
#             if menu>=1 and menu<=len(list):
#                 menu = list[menu-1]
#                 return menu
#                 break
#                 valid = True
#             else: 
#                 print('Please only input number in the brackets')
#         except ValueError:
#             print('Please only input digits')
    

# # -------------------------------------------------------------------------
# # main
# # -------------------------------------------------------------------------
# def main():
#     init()
#     global cmd_menu
#     print('-------------------------------------------------');
#     print(colored('         MAGTROL DSP6001 control script          ', 'white', 'on_green'))
#     scan_com_port()
#     while cmd_menu!='Quit': 
#         input_command()
#         if cmd_menu == 'OD':
#             data_acquisition()
#         elif cmd_menu == 'Custom':
#             print(colored('Type the command to send:  ', 'green'), end='\b')
#             message_send = input()
#             send_cmd_magtrol(message_send)
#         else:
#             send_cmd_magtrol(cmd_menu)

# yarp.Network.init()

# if not yarp.Network.checkNetwork():
#     print("yarpserver is not running")
#     quit()



# if __name__ == "__main__":
#     main()
