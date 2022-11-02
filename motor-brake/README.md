# Motor Brake Manager 

Motor Brake Manager is an utility for interacting with a motor brake device by command line and/or by yarp ports.

The main functionalities of the Motor Brake Manager are:
 - read the motor brake data, like torque and speed and dumps them on file and/or publishes them on a yarp port
 - send torque and speed setpoints to the motor brake device
 - send a custom command to the motor brake device

In the next sections you can find instruction on how to interact with the device using the command line and yarp ports.

## How to install 
The Motor Brake Manager is a small set of python scripts so you need python3 to run it.
Moreover the following packages are necessary:
 - `matplotlib`
 - `termcolor`
 - `colorama`
 - `serialport`

If you are interesting in yarp services also, you need to install yarp with python binding enabled (set `ON` the `ROBOTOLOGY_USES_PYTHON` CMake option).

Alternatively, you can use the docker images available [here](https://hub.docker.com/r/valegagge/setupmotorbrake) that has already installed all needed packages and yarp.

## How to run 

You need to just type `python3 motorBrakeManager.py` .

### Start options
If you run the Motor Brake Manager with `--help` option you get all available options, that are reported here:

 - `-h, --help            show this help message and exit`
 - `-y, --yarpServiceOn   enable yarp service (default: False)`
 - `-f FILE, --file FILE  name of file where log data (default: )` **current not available**
 - `-p PERIOD, --period PERIOD acquisition data period(seconds) (default: 0.1)`
 - `-s SERIALPORT, --serialPort SERIALPORT Serial port (default: /dev/ttyUSB0) **current not available**

If you are interested in publishing the motor brake data on port yarp and/or in commanding the device by a yarp port, you need to use the option `yarpServiceOn`. See the section __yarp service__ for more detail.


### Command menu
The commands available in the prompt are:
 - `[1] : Get Magtrol Id and revision` : get the ID end revision 
 - `[2] : Start data acquisition` : start the data acquision in background. When this option is chosen, the utility ask the name of file where save the retrived data; if it isn't  provided the data are not saved on file.
 - `[3] : Stop data acquisition`: stop the data acquision
 - `[4] : Send torque setpoint`: sends a torque setpoint. When this option is chosen, the utility ask the value to the user. The value is in Nmm.
 - `[5] : Send speed setpoint`: sends a speed setpoint. When this option is chosen, the utility ask the value to the user. The value is in rpm.
 - `[6] : Custom`: send a custom comamnd
 - `[7] : Quit` : exit from the application closing all yarp services also, if they have been anabled.

## Yarp service
If the MotorBrakeManager is launched with the option `--yarpServiceOn`, it opens the port `/motorbrake/cmd:i` for receiving command to forward to the device and publish on port `/motorbrake/out` the data read by the device.

### How to send command to the motor brake by yarp port
You need to send the following commands to the port `/motorbrake/cmd:i`:
 - `torque <torque_value>`: send the torque setpoint (also with decimal digit ) expressed in nNm
 - `speed <speed_value>` :  send the speed setpoint (also with decimal digit ) expressed in rpm
Other commands are ignored.

### Motor brake data published on yarp port
When the user enables the data acquisition option, the MotorBrakeManager starts a thread with the period specified by the user by `--period` option (otherwise 0.1 second is used); such thread collects speed and torque values from the device and publish them on yarp port `/motorbrake/out`.


## Implementation details

The Motor brake manager is a multi threading application not hardware dependent. 
This application now works with the device Magtrol DSP6001, but if you want to use with a different device it is sufficient to implement a new driver with the same interface of the deployed in the file motorBrakeDriver.py.

Here is reported the class diagram.
![immagine](./misc/MotorBrake_class.jpg)

If you go through the code you can find more information about each class.

Check the units of torque and speed and if are the same in yarp, else it's better add a conversion.



---------------------------------
# Next improvements
1. check the period of data collector
2. fix the issue con memory leak
3. develop the option -s 
4. develop the option -f
5. improve the style of the commands
6. use type hints to make the code more readable
7. Make configurable the torque and speed units. This is necessary to compare motor brake data and yarp values.


Note: the point 3 and 4 are necessary for running the application without any interaction with the user. (for example if we want to deploy it.)

