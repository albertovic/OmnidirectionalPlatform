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


# Orange Pi & Laptop Workflows

*(Requirement: Ensure `export ROS_DOMAIN_ID=1` is set in all active terminals on both machines so they can communicate over Wi-Fi).*

---

## Mode A: Building a Map (SLAM)

**1. On the Orange Pi (Hardware Layer):**
Start the LiDAR, odometry, and Arduino bridge.
```bash
cd ~/ros2_ws_orangepi
source install/setup.bash
ros2 launch omnidirectional_robot robot_bringup.launch.py
```

**2. On the Laptop (SLAM Layer):**
Launch the joystick driver, SLAM Toolbox, and RViz to visualize the mapping process.
```bash
ros2 launch ~/mapping.launch.py
```
*(Drive the robot around the environment until the map looks complete and enclosed in RViz).*

**3. On the Orange Pi (Save the Map):**
Open a *new SSH terminal* into the Orange Pi and save the map directly into your package's `maps` folder:
```bash
cd ~/ros2_ws_orangepi/src/omnidirectional_robot/maps
ros2 run nav2_map_server map_saver_cli -f my_room_map
```
*(This generates `my_room_map.yaml` and `my_room_map.pgm` directly on the robot).*

## Mode B: Autonomous Navigation

**1. On the Orange Pi (Hardware + Autonomy Brain):**
Launch the master file. This brings up the hardware AND the Nav2 planners simultaneously. It uses `my_room_map.yaml` by default.
```bash
cd ~/ros2_ws_orangepi
source install/setup.bash
ros2 launch omnidirectional_robot navigation.launch.py
```
*(To use a different map, run: `ros2 launch omnidirectional_robot navigation.launch.py map:=/home/orangepi/ros2_ws_orangepi/src/omnidirectional_robot/maps/other_map.yaml`)*

**2. On the Laptop (Remote Control & Visualization):**
Launch the Nav2 visualization tools. Use the "2D Pose Estimate" button to tell the robot where it is, and the "Nav2 Goal" button to tell it where to drive.
```bash
ros2 launch ~/nav2_view.launch.py
```

---

## Future Improvements & Roadmap

Here is a roadmap of upcoming features, expansions, and experiments planned for the robot:

### 1. Sensor Suite Expansions
* [ ] **Add a Camera:** Integrate a depth or RGB camera (e.g., RealSense or OAK-D) for visual SLAM, object detection, or person-following.
* [ ] **IMU / Gyro Integration:** Incorporate a hardware IMU to fuse high-frequency rotation data with `rf2o` laser odometry using an EKF (`robot_localization` package).

### 2. Autonomy & Navigation
* [ ] **Autonomous Navigation (Nav2):** Configure costmaps, global/local planners, and behavior trees to enable autonomous point-to-point navigation and obstacle avoidance.
* [ ] **Wayland / Patrol Routes:** Set up pre-defined goal waypoints for automated looping or patrol demos.

### 3. Software & Telemetry Enhancements
* [ ] **Foxglove Studio / Web Dashboard:** Set up a lightweight web-based telemetry stream or Foxglove connection for remote monitoring without needing a full local ROS 2 GUI setup.
* [ ] **Auto-Docking / Charging:** Explore docking logic for automated battery management.

### 4. Gazebo Simulation & Digital Twin
* [ ] **Integrate Simulation Models:** Import existing wheel meshes, chassis URDF, and sensor plugins into Gazebo.
* *Note:* Evaluate utility primarily for safely benchmarking Nav2 path planners and recovery behaviors.

---

## Project Gallery

*(Add images or architecture diagrams to an `images/` directory in the repo and reference them below)*


## Command Cheatsheet

1. Diagnostics & Debugging

```Bash
# Check active topics and verify /scan is alive
ros2 topic list

# Inspect topic connection and QoS reliability profile
ros2 topic info /scan --verbose

# Monitor laser odometry output stream directly
ros2 topic echo /odom
```

2. Saving the Map
```Bash
# Run this from your laptop terminal once mapping is complete
ros2 run nav2_map_server map_saver_cli -f ~/my_room_map
```

3. Managing Packages Over SSH Without Ethernet 

If the robot is operating on an isolated network and cannot connect directly to Wi-Fi, you can route the Orange Pi's package manager (`apt`) through your laptop's internet connection using a reverse SOCKS proxy over SSH.

Step 1: Open a Reverse Proxy SSH Session (Laptop Terminal)
Open a new terminal on your laptop and log into the Orange Pi with the `-R` flag to open port `8080`:
```bash
ssh -R 8080 orangepi@<YOUR_ORANGE_PI_IP>
```

Step 2: Run APT Updates & Installs (Orange Pi Terminal)
Inside that SSH session, override apt to route traffic through the local proxy tunnel:
```bash
# Update package lists
sudo apt -o Acquire::http::Proxy="socks5h://localhost:8080" update

# Install ROS 2 or system packages (e.g., Nav2)
sudo apt -o Acquire::http::Proxy="socks5h://localhost:8080" install ros-foxy-navigation2 ros-foxy-nav2-bringup
```

Or to use Git with this method:

```bash
# Push your changes
git -c http.proxy="socks5h://localhost:8080" push origin main

# Pull changes
git -c http.proxy="socks5h://localhost:8080" pull origin main
```

Or to use curl:

```bash
curl -x socks5h://localhost:8080 -O <link to download>
```








