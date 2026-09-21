import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    # Get the path to the standard slam_toolbox launch directory
    slam_toolbox_dir = get_package_share_directory('slam_toolbox')

    return LaunchDescription([
        # Twist Multiplexer (Blends Joystick and Nav2)
        Node(
            package='twist_mux',
            executable='twist_mux',
            name='twist_mux',
            output='screen',
            parameters=[os.path.join(get_package_share_directory('omnidirectional_robot'), 'config', 'twist_mux_params.yaml')]
        ),
        # Sends velocity messages to Arduino
        Node(
            package='omnidirectional_robot',
            executable='TwistToSerial',
            name='TwistToSerial',
            output='screen'
        ),
        
        # The Odometry Node (Ticks to Map Coordinates)
        Node(
            package='omnidirectional_robot',
            executable='mecanum_odom',
            name='mecanum_odom',
            output='screen'
        ),

        # Static Transform (Robot Center to LiDAR)
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='base_link_to_laser',
            arguments=['0.089', '0.0', '0.15', '3.14159', '0.0', '0.0', 'base_link', 'laser']
        ),
        
        # RP-LiDAR Node
        Node(
            package='sllidar_ros2',
            executable='sllidar_node',
            name='sllidar_node',
            output='screen',
            parameters=[{
                'serial_port': '/dev/ttyUSB0',
                'serial_baudrate': 115200,
                'frame_id': 'laser',
                'inverted': False,
                'angle_compensate': True
            }]
        ),

        # SLAM Frame Bypass (Matches base_footprint to base_link)
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='footprint_to_link',
            arguments=['0.0', '0.0', '0.0', '0.0', '0.0', '0.0', 'base_link', 'base_footprint']
        ),

        # Laser Odometry (Replaces wheel encoders)
        Node(
            package='rf2o_laser_odometry',
            executable='rf2o_laser_odometry_node',
            name='rf2o_laser_odometry',
            output='screen',
            arguments=['--ros-args', '--log-level', 'ERROR'],
            parameters=[{
                'laser_scan_topic' : '/scan',
                'odom_topic' : '/odom',
                'publish_tf' : True,
                'base_frame_id' : 'base_link',
                'odom_frame_id' : 'odom',
                'init_pose_from_topic' : '',
                'freq' : 20.0
            }]
        ),
        
        # SLAM Toolbox (Live Mapping)
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(slam_toolbox_dir, 'launch', 'online_async_launch.py')
            ),
            launch_arguments={'use_sim_time': 'False'}.items()
        )
    ])