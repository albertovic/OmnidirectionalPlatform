import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32MultiArray
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped, Quaternion
from tf2_ros import TransformBroadcaster
import math
import time

class MecanumOdom(Node):
    def __init__(self):
        super().__init__('mecanum_odom')
        
        # --- PHYSICAL CONSTANTS ---
        self.RADIUS = 0.038  # 37.5mm from URDF
        self.TPR = 225 # Empirically
        self.METERS_PER_TICK = (2.0 * math.pi * self.RADIUS) / self.TPR
        
        # YOU MUST MEASURE THESE ON YOUR PHYSICAL CHASSIS (in meters)
        self.LX = 0.104  # Distance from robot center to front/back wheel axis (wheel_offset_x)
        self.LY = 0.088  # Distance from robot center to left/right wheel axis (wheel_offset_y)
        
        # --- STATE VARIABLES ---
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        
        self.prev_ticks = None
        self.last_time = self.get_clock().now()
        
        # --- ROS 2 INTERFACES ---
        self.sub = self.create_subscription(Int32MultiArray, '/wheel_ticks', self.tick_callback, 10)
        # self.odom_pub = self.create_publisher(Odometry, '/odom', 10)
        # self.tf_broadcaster = TransformBroadcaster(self)
        
        self.get_logger().info("Mecanum Odometry Node Started.")

    def tick_callback(self, msg):
        current_time = self.get_clock().now()
        current_ticks = msg.data
        
        if self.prev_ticks is None:
            self.prev_ticks = current_ticks
            self.last_time = current_time
            return
            
        # Calculate distance traveled by each wheel since last callback
        dt = (current_time - self.last_time).nanoseconds / 1e9
        
        d_fl = (current_ticks[0] - self.prev_ticks[0]) * self.METERS_PER_TICK
        d_fr = (current_ticks[1] - self.prev_ticks[1]) * self.METERS_PER_TICK
        d_rl = (current_ticks[2] - self.prev_ticks[2]) * self.METERS_PER_TICK
        d_rr = (current_ticks[3] - self.prev_ticks[3]) * self.METERS_PER_TICK
        
        self.prev_ticks = current_ticks
        self.last_time = current_time

        # Mecanum Forward Kinematics (Robot Centric)
        dx = (d_fl + d_fr + d_rl + d_rr) / 4.0
        dy = (-d_fl + d_fr + d_rl - d_rr) / 4.0
        dtheta = (-d_fl + d_fr - d_rl + d_rr) / (4.0 * (self.LX + self.LY))
        
        # Integrate into global Map/Odom frame
        self.x += dx * math.cos(self.theta) - dy * math.sin(self.theta)
        self.y += dx * math.sin(self.theta) + dy * math.cos(self.theta)
        self.theta += dtheta
        
        # Velocities
        vx = dx / dt if dt > 0 else 0.0
        vy = dy / dt if dt > 0 else 0.0
        vtheta = dtheta / dt if dt > 0 else 0.0
        
        # self.publish_odom(current_time, vx, vy, vtheta)

    def publish_odom(self, current_time, vx, vy, vtheta):
        q = euler_to_quaternion(0, 0, self.theta)
        
        # Publish TF (odom -> base_link)
        t = TransformStamped()
        t.header.stamp = current_time.to_msg()
        t.header.frame_id = 'odom'
        t.child_frame_id = 'base_link'
        t.transform.translation.x = self.x
        t.transform.translation.y = self.y
        t.transform.translation.z = 0.0
        t.transform.rotation = q
        # self.tf_broadcaster.sendTransform(t)
        
        # Publish Odometry message
        odom = Odometry()
        odom.header.stamp = current_time.to_msg()
        odom.header.frame_id = 'odom'
        odom.child_frame_id = 'base_link'
        
        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.position.z = 0.0
        odom.pose.pose.orientation = q
        
        odom.twist.twist.linear.x = vx
        odom.twist.twist.linear.y = vy
        odom.twist.twist.angular.z = vtheta
        
        # self.odom_pub.publish(odom)

def euler_to_quaternion(roll, pitch, yaw):
    q = Quaternion()
    q.x = math.sin(roll/2) * math.cos(pitch/2) * math.cos(yaw/2) - math.cos(roll/2) * math.sin(pitch/2) * math.sin(yaw/2)
    q.y = math.cos(roll/2) * math.sin(pitch/2) * math.cos(yaw/2) + math.sin(roll/2) * math.cos(pitch/2) * math.sin(yaw/2)
    q.z = math.cos(roll/2) * math.cos(pitch/2) * math.sin(yaw/2) - math.sin(roll/2) * math.sin(pitch/2) * math.cos(yaw/2)
    q.w = math.cos(roll/2) * math.cos(pitch/2) * math.cos(yaw/2) + math.sin(roll/2) * math.sin(pitch/2) * math.sin(yaw/2)
    return q

def main(args=None):
    rclpy.init(args=args)
    node = MecanumOdom()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()