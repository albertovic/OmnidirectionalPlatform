from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # The Bridge Node (Joystick to Arduino)
        Node(
            package='omnidirectional_robot',
            executable='joyToSerial',
            name='joyToSerial',
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
        # Arguments: [x, y, z, yaw, pitch, roll, parent_frame, child_frame]
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='base_link_to_laser',
            arguments=['0.089', '0.0', '0.15', '0.0', '0.0', '0.0', 'base_link', 'laser']
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
    ])
