import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    # Get directories
    my_pkg_dir = get_package_share_directory('omnidirectional_robot')
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')

    # Define configurations
    map_yaml_file = LaunchConfiguration('map')
    params_file = LaunchConfiguration('params_file')

    # Declare arguments (Allows you to override the map from the terminal if needed)
    declare_map_yaml_cmd = DeclareLaunchArgument(
        'map',
        default_value=os.path.join(my_pkg_dir, 'maps', 'my_room_map.yaml'),
        description='Full path to map yaml file to load'
    )
    declare_params_file_cmd = DeclareLaunchArgument(
        'params_file',
        default_value=os.path.join(my_pkg_dir, 'config', 'nav2_params.yaml'),
        description='Full path to the ROS2 parameters file'
    )

    # Launch the Hardware (LiDAR, Odometry, Arduino)
    hardware_bringup_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(my_pkg_dir, 'launch', 'robot_bringup.launch.py')
        )
    )

    # Launch Nav2 (Map Server, AMCL, Path Planning)
    nav2_bringup_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_bringup_dir, 'launch', 'bringup_launch.py')
        ),
        launch_arguments={
            'map': map_yaml_file,
            'params_file': params_file,
            'use_sim_time': 'False'
        }.items()
    )

    # Create and populate the launch description
    ld = LaunchDescription()
    ld.add_action(declare_map_yaml_cmd)
    ld.add_action(declare_params_file_cmd)
    ld.add_action(hardware_bringup_cmd)
    ld.add_action(nav2_bringup_cmd)

    return ld