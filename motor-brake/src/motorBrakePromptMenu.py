# -------------------------------------------------------------------------
# Copyright (C) 2022 iCub Tech - Istituto Italiano di Tecnologia
#
# Here are defined all the functions used for the interaction with the user in the prompt menu.
#
# Written by V. Gaggero
# <valentina.gaggero@iit.it>
# -------------------------------------------------------------------------

import matplotlib.pyplot as plt
from termcolor import colored
import serial.tools.list_ports as portlist



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
