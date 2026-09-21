FROM osrf/ros:foxy-desktop

# Install Nav2, CycloneDDS, and Joystick drivers
RUN apt-get update && apt-get install -y \
    ros-foxy-navigation2 \
    ros-foxy-nav2-bringup \
    ros-foxy-rmw-cyclonedds-cpp \
    ros-foxy-joy \
    ros-foxy-teleop-twist-joy \
    nano \
    && rm -rf /var/lib/apt/lists/*

# Auto-source ROS and set environment variables
RUN echo "source /opt/ros/foxy/setup.bash" >> ~/.bashrc
RUN echo "export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp" >> ~/.bashrc
RUN echo "export ROS_DOMAIN_ID=1" >> ~/.bashrc
