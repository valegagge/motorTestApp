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
