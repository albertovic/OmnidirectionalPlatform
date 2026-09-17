import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    slam_toolbox_dir = get_package_share_directory('slam_toolbox')
    slam_launch_file = os.path.join(slam_toolbox_dir, 'launch', 'online_async_launch.py')
    
    # Path to the RViz config
    rviz_config = os.path.expanduser('~/.rviz2/slam_config.rviz')
    
    return LaunchDescription([
        # Joystick Driver (Reads the controller plugged into the laptop)
        Node(
            package='joy',
            executable='joy_node',
            name='joy_node',
            parameters=[{'deadzone': 0.05}]
        ),
        
        # SLAM Toolbox
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(slam_launch_file)
        ),
        
        # RViz2
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', rviz_config]
        )
    ])
