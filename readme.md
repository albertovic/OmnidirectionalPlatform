# Omnidirectional Mecanum Robot with ROS 2 Foxy

A custom-built, four-wheeled omnidirectional mecanum mobile robot powered by an **Orange Pi 5B**, an **Arduino Mega** for low-level motor control, an **SLLidar** for 2D laser scans, and managed via **ROS 2 Foxy**. 

This project implements **laser-based odometry** to bypass the severe wheel slip typical of mecanum kinematics, achieving drift-free mapping and localization.

---

## System Architecture & Hardware Stack

* **Central Computer:** Orange Pi 5B running ROS 2 Foxy.
* **Microcontroller:** Arduino Mega (handling low-level PWM motor drivers and serial communication via `joyToSerial`).
* **Sensors:** Slamtec SLLidar (connected via `/dev/ttyUSB0` at 10Hz).
* **Drive System:** 4-wheel mecanum drive.
* **Localization Method:** `rf2o_laser_odometry` (Range Flow-based 2D laser odometry, replacing error-prone wheel encoders).
* **Mapping Framework:** `slam_toolbox`.

---

## What Has Been Done (Milestones)

1. **Low-Level Control & Teleoperation:**
   * Developed custom serial communication between the Orange Pi and Arduino Mega (`joyToSerial`).
   * Configured joystick nodes to stream velocity commands at 20Hz.
2. **Odometry Overhaul:**
   * Initially calibrated encoder math (TPR set to 225).
   * Diagnosed and eliminated mecanum wheel slip drift by muting raw encoder-based odometry/TF publishing.
   * Successfully built and integrated **`rf2o_laser_odometry`** from source for ROS 2 Foxy, resolving header compatibility issues (`tf2_geometry_msgs.h`).
3. **Sensor Integration & QoS Alignment:**
   * Resolved serial port mapping (`/dev/ttyUSB0` for LiDAR, `/dev/ttyACM0` for Arduino).
   * Fixed ROS 2 Quality of Service (QoS) reliability mismatches between the SLLidar publisher and the `rf2o` subscriber.
4. **Stable SLAM Mapping:**
   * Achieved completely rock-solid map tracking with zero rotational drift during full 360-degree spins.

---

## Project Gallery

*(Add images or architecture diagrams to an `images/` directory in the repo and reference them below)*


## Command Cheatsheet

1. Orange Pi (Robot Side)
```bash
# Source your ROS 2 workspace
cd ~/ros2_ws_orangepi
source install/setup.bash

# Launch hardware drivers, joy control, and laser odometry
ros2 launch omnidirectional_robot robot_bringup.launch.py
```

2. Laptop (Control & SLAM Side)
(Make sure export ROS_DOMAIN_ID=1 is set if communicating across machines)

```Bash
# Launch laptop SLAM and RViz2 visualization
ros2 launch ~/laptop_slam.launch.py
```

3. Diagnostics & Debugging

```Bash
# Check active topics and verify /scan is alive
ros2 topic list

# Inspect topic connection and QoS reliability profile
ros2 topic info /scan --verbose

# Monitor laser odometry output stream directly
ros2 topic echo /odom
```

4. Saving the Map
```Bash
# Run this from your laptop terminal once mapping is complete
ros2 run nav2_map_server map_saver_cli -f ~/my_room_map
```
