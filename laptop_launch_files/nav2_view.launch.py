import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    # Base paths
    workspace_dir = os.path.expanduser('~/OmnidirectionalPlatform')
    rviz_config = os.path.join(workspace_dir, 'config', 'my_nav2_config.rviz')
    
    # Nav2 specific paths
    map_yaml_file = os.path.join(workspace_dir, 'maps', 'my_room_map.yaml')
    nav2_params_file = os.path.join(workspace_dir, 'config', 'nav2_params.yaml')
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')

    return LaunchDescription([
        # 1. The Nav2 Brain (Map Server, AMCL, Path Planning)
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(nav2_bringup_dir, 'launch', 'bringup_launch.py')
            ),
            launch_arguments={
                'map': map_yaml_file,
                'params_file': nav2_params_file,
                'use_sim_time': 'False'
            }.items()
        ),

        # 2. Keep joystick active as an emergency manual takeover
		Node(
		    package='joy',
		    executable='joy_node',
		    name='joy_node',
		    parameters=[
		        {'deadzone': 0.05},
		        {'device_name': '/dev/input/js0'}
		    ]
		),
        
        # 3. RViz2 with Nav2 Goal tools
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', rviz_config]
        )
    ])
