import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    # Dedicated RViz config with Nav2 panels & costmap displays loaded
    rviz_config = os.path.expanduser('~/.rviz2/nav2_config.rviz')
    
    return LaunchDescription([
        # Keep joystick active as an emergency manual takeover
        Node(
            package='joy',
            executable='joy_node',
            name='joy_node',
            parameters=[{'deadzone': 0.05}]
        ),
        
        # RViz2 with Nav2 Goal tools
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', rviz_config]
        )
    ])
