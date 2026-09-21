#!/bin/bash
xhost +local:root
docker run -it --net=host --ipc=host --privileged \
-e DISPLAY=$DISPLAY \
-v /tmp/.X11-unix:/tmp/.X11-unix:rw \
-v ~/OmnidirectionalPlatform:/root/OmnidirectionalPlatform \
-v /dev/input:/dev/input \
foxy-nav2 bash
