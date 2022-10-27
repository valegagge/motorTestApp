# Motor Bake Manager 

Motor Brake Manager is an utility for interacting with a motor brake device by command line and/or by yarp ports.

The main functionalities of the Motor Brake Manager are:
 - read the motor brake data, like torque and speed and dumps them on file and/or publishes them on a yarp port
 - send torue and speed setpoint to the motor brake device
 - send a custom command to the motor brake device

In the next sections you can find instruction on how to interact with the device using the command line and yarp ports.

## 1 Start options
If you run the Motor Brake Manager with `--help` option you get all available options, that are reported here:

 - `-h, --help            show this help message and exit`
 - `-y, --yarpServiceOn   enable yarp service (default: False)`
 - `-f FILE, --file FILE  name of file where log data (default: )` **current not available**
 - `-p PERIOD, --period PERIOD acquisition data period(seconds) (default: 0.1)`
 - `-s SERIALPORT, --serialPort SERIALPORT Serial port (default: /dev/ttyUSB0) **current not available**

If you are interested in publishing the motor brake data on port yarp and/or in commanding the device by a yarp port you need to use the option `yarpServiceOn`. See the section __yarp service__ for more detail.


## Command menu
The command available in the promt are:
 - `[1] : Get Magtrol Id and revision` : get the ID end revision 
 - `[2] : Start data acquisition` : start the data acquision in background. When this option is chosen, the utility ask the name of file where save the data retrived; if is not provided the data are not saved on file.
 - `[3] : Stop data acquisition`: start the data acquision
 - `[4] : Send torque setpoint`: sends a torque setpoint. When this option is chosen, the utility ask the value to the user. the value is in nNM.
 - `[5] : Send speed setpoint`: sends a torque setpoint. When this option is chosen, the utility ask the value to the user. the value is in rpm.
 - `[6] : Custom`: send a custom comamnd
 - `[7] : Quit` : exit from the application closing all yarp services also, if they have been anabled.

## 1. Yarp service
If the MotorBrakeManager is launched with the option `--yarpServiceOn`, it opens the port `/motorbrake/cmd:i` for receiveing command to send to the device and publish on port `/motorbrake/out` the data read by the device.

### 1.2 How to send command to the motor brake by yarp port
You need to send the following commands to the port 'bla bla':
 - `torque <torque_value>`: send the torque setpoint (also with decimal digit ) expressed in nNm ????
 - `speed <speed_value>` :  send the speed setpoint (also with decimal digit ) expressed in rpm
Other commands are ignored.

### 1.3 Motor brake data published on yarp port
When the user enables the data acquisition option, the MotorBrakeManager starts a thread with the period specifed by the user by `--period` option (otherwise 0.1 second is used) that collects speed and torque values from the device.





---------------------------------
# Improvements
1. check the period of data collector
2. fix the issue con memory leak
3. develop the option -s 
4. develop the option -f
5. improve the style of the commands
6. use type hints to make the code more readable


Note: the point 3 and 4 are necessary for running the application without any intercation with the user. (for example if we want to deploy it.)



-------------------------
# OLD


# using docker 
command:

```
docker run -it --name motorbrakeappsdev --mount type=bind,source=${HOME}/FIVE_WORKSPACE/motorTestApp/,target=/root/motorTestApp --mount type=bind,source=${HOME}/.config/yarp,target=/root/.config/yarp --env DISPLAY=${DISPLAY} --env XAUTHORITY=/root/.Xauthority --mount type=bind,source=${XAUTHORITY},target=/root/.Xauthority --mount type=bind,source=/tmp/.X11-unix,target=/tmp/.X11-unix icubteamcode/superbuild:master-stable_sources bash 

```

# necessary packets
1. ```sudo apt-get install python3-matplotlib```
(I got some installation errors, but it installed the desired packets!)

2. ```apt-get install python3-termcolor```

3. ```apt-get install python3-colorama```

4. - install dependencies:
   ```
   apt update
   cd robotology-superbuild
   chmod +x ./scripts/install_apt_python_dependencies.sh
   ./scripts/install_apt_python_dependencies.sh 
   ```
    - compile robotology-syperbuild with `ROBOTOLOGY_USES_PYTHON` CMake option `ON`

 For more info: [compiling robologysuperbuild with python](https://github.com/robotology/robotology-superbuild/blob/master/doc/cmake-options.md#python)

5. export PYTHONPATH=${PYTHONPATH}:/usr/local/lib/python3/dist-packages/ 

# to develop test app
In first attempt I decided to use the RTF, because for me is quiker get a working application
```
docker run -it --name motorbraketest --mount type=bind,source=${HOME}/FIVE_WORKSPACE/,target=/root/FIVE_WORKSPACE --mount type=bind,source=${HOME}/.config/yarp,target=/root/.config/yarp --env DISPLAY=${DISPLAY} --env XAUTHORITY=/root/.Xauthority --mount type=bind,source=${XAUTHORITY},target=/root/.Xauthority --mount type=bind,source=/tmp/.X11-unix,target=/tmp/.X11-unix icubteamcode/superbuild-icubtest:master-stable_sources bash
```
