# Omnidirectional Mecanum Robot with ROS 2 Foxy

A custom-built, four-wheeled omnidirectional mecanum mobile robot powered by an **Orange Pi 5B**, an **Arduino Mega** for low-level motor control, an **SLLidar** for 2D laser scans, and managed via **ROS 2 Foxy**. 

This project implements **laser-based odometry** to bypass the severe wheel slip typical of mecanum kinematics, achieving drift-free mapping and localization, combined with **`twist_mux`** for safe priority-based multiplexing between autonomous Nav2 commands and manual joystick overrides.

## System Architecture & Hardware Stack

* **Central Computer:** Orange Pi 5B running ROS 2 Foxy.
* **Microcontroller:** Arduino Mega (handling low-level PWM motor drivers and PID serial communication).
* **Sensors:** Slamtec SLLidar (connected via `/dev/ttyUSB0` with a 180-degree yaw offset for correct front alignment).
* **Drive System:** 4-wheel mecanum drive.
* **Localization Method:** `rf2o_laser_odometry` (Range Flow-based 2D laser odometry, replacing error-prone wheel encoders).
* **Mapping Framework:** `slam_toolbox` & Nav2 (`amcl`, `DWBLocalPlanner`).
* **Control Multiplexer:** `twist_mux` (prioritizing manual joystick over autonomous navigation).

## What Has Been Done (Milestones)

1. **Low-Level Control & Teleoperation:**
   * Developed custom serial communication between the Orange Pi and Arduino Mega (`twist_to_serial.py`).
   * Integrated `teleop_twist_joy` to translate Xbox controller inputs into standard `Twist` velocity commands.
2. **Odometry & Sensor Calibration:**
   * Built and integrated **`rf2o_laser_odometry`** from source for ROS 2 Foxy.
   * Fixed sensor-to-base frame alignments, ensuring correct directional mapping and navigation performance.
3. **Control Safety via `twist_mux`:**
   * Configured `twist_mux` to blend velocities, allowing instant manual safety override via the controller's deadman switch.
4. **Autonomous Navigation (Nav2):**
   * Configured `amcl` for omnidirectional movement.
   * Tuned costmaps, footprints, inflation radiuses, and forced full costmap updates to prevent diagonal RViz shearing and corner clipping.

# Orange Pi & Laptop Workflows

*(Requirement: Ensure `export ROS_DOMAIN_ID=1` and your CycloneDDS configuration are active in all terminals on both machines so they can communicate over Wi-Fi).*

## Mode A: Manual Teleoperation

**1. On the Orange Pi :**
Start the hardware bringup (LiDAR, odometry, Arduino bridge, and multiplexer).
```bash
cd ~/ros2_ws_orangepi
source install/setup.bash
ros2 launch omnidirectional_robot robot_bringup.launch.py
```

**2. On the Laptop (inside the docker container):**
Use your controller with the deadman switch to manually drive the robot. Move to the package directory, then:
```bash
ros2 launch ./laptop_launch_files/visualize_omni_robot.launch.py
```

## Mode B: Building a Map (SLAM)

**1. On the Orange Pi:**
Start the hardware bringup (LiDAR, odometry, Arduino bridge, and multiplexer).
```bash
cd ~/ros2_ws_orangepi
source install/setup.bash
ros2 launch omnidirectional_robot mapping.launch.py
```

**2. On the Laptop (inside the docker container):**
Use your controller with the deadman switch to manually drive and position the robot. Move to the package directory, then:
```bash
ros2 launch ./laptop_launch_files/visualize_omni_robot.launch.py
```
*(Drive the robot around the environment until the map looks complete and enclosed in RViz).*

**3. On the Orange Pi (save the map):**
Open a *new SSH terminal* into the Orange Pi and save the map directly into your package's `maps` folder:
```bash
cd ~/ros2_ws_orangepi/src/omnidirectional_robot/maps
ros2 run nav2_map_server map_saver_cli -f my_room_map
```
*(This generates `my_room_map.yaml` and `my_room_map.pgm` directly on the robot).*

## Mode C: Autonomous Navigation

**1. On the Orange Pi:**
Launch the master file. This brings up the hardware AND the Nav2 planners simultaneously. It uses `my_room_map.yaml` by default.
```bash
cd ~/ros2_ws_orangepi
source install/setup.bash
ros2 launch omnidirectional_robot navigation.launch.py
```
*(To use a different map, run: `ros2 launch omnidirectional_robot navigation.launch.py map:=/home/orangepi/ros2_ws_orangepi/src/omnidirectional_robot/maps/other_map.yaml`)*

**2. On the Laptop (inside the docker container):**
Launch the visualization tools. Use the "2D Pose Estimate" button to tell the robot where it is, and the "Nav2 Goal" button to tell it where to drive. Move to the package directory, then:
```bash
ros2 launch ./laptop_launch_files/visualize_omni_robot.launch.py
```

## Activate People Tracking:
Launch the people trackikng node (from the gtihub repo: https://github.com/TeamSOBITS/2d_lidar_person_detection/tree/humble-devel) through the following command:
```bash
ros2 launch dr_spaam_ros dr_spaam_ros.launch.py 
```

---

# Future Improvements & Roadmap
Here is a roadmap of upcoming features and expansions planned for the robot:

1. Sensor Suite Expansions
- Add a Camera: Integrate a depth or RGB camera for visual tracking or obstacle inspection.

- IMU / Gyro Integration: Incorporate a hardware IMU to fuse high-frequency rotation data with rf2o laser odometry using an EKF (robot_localization).

2. Autonomy & Navigation
- Auto-Docking / Charging: Explore docking logic for automated battery management.

3. Gazebo Simulation & Digital Twin
- Integrate Simulation Models: Import existing wheel meshes, chassis URDF, and sensor plugins into Gazebo to safely benchmark custom path planners.

---

## Project Gallery

*(Add images or architecture diagrams to an `images/` directory in the repo and reference them below)*


## Command Cheatsheet

1. Managing Packages Over SSH Without Ethernet 

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
git -c http.proxy="socks5h://localhost:8080" push origin master

# Pull changes
git -c http.proxy="socks5h://localhost:8080" pull origin master
```

Or to use curl:

```bash
curl -x socks5h://localhost:8080 -O <link to download>
```








