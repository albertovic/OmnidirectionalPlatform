#!/bin/bash
xhost +local:root
docker run -it --net=host --ipc=host --privileged \
-e DISPLAY=$DISPLAY \
-e RMW_IMPLEMENTATION=rmw_cyclonedds_cpp \
-e ROS_DOMAIN_ID=1 \
-e CYCLONEDDS_URI=file:///root/OmnidirectionalPlatform/cyclonedds_robot.xml \
-v /tmp/.X11-unix:/tmp/.X11-unix:rw \
-v ~/OmnidirectionalPlatform:/root/OmnidirectionalPlatform \
-v /dev/input:/dev/input \
foxy-nav2 bash
