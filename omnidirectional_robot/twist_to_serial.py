import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import serial
import time
from std_msgs.msg import Int32MultiArray

class TwistToSerial(Node):
    def __init__(self):
        super().__init__('twist_to_serial')

        # Subscribe to the final velocity topic
        self.subscription = self.create_subscription(
            Twist,
            '/cmd_vel_out', 
            self.twist_callback,
            10)
        
        # State variable to hold the most recent command
        self.latest_command = "0,0,0,0\n"   

        # Publishes the ticks of the wheels
        self.tick_pub = self.create_publisher(Int32MultiArray, '/wheel_ticks', 10)
        
        # Initialize serial connection with Arduino
        try:
            self.serial_port = serial.Serial('/dev/ttyACM0', 115200, timeout=0.1, write_timeout=0.1)
            self.get_logger().info("Port opened. Waiting 2.5 seconds for Arduino PID to boot...")
            time.sleep(2.5)
            
            self.serial_port.reset_input_buffer()
            self.serial_port.reset_output_buffer()
            self.get_logger().info("Arduino awake! Listening to /cmd_vel...")
        except Exception as e:
            self.get_logger().error(f"Failed to connect to Arduino: {e}")
            self.serial_port = None
            
        # Create the PID command every 50ms (20 times a sec)
        self.timer = self.create_timer(0.05, self.timer_callback)
    
    def twist_callback(self, msg):
        # Extract the target velocities (meters/sec and radians/sec)
        vx = msg.linear.x   # Forward/Backward
        vy = msg.linear.y   # Left/Right Strafe (Mecanum)
        wz = msg.angular.z  # Rotation
        
        # Mecanum Inverse Kinematics
        fl = vx - vy - wz
        fr = vx + vy + wz
        rl = vx + vy - wz
        rr = vx - vy + wz
        
        # Normalize the speeds to 0.0 - 1.0 range so proportions remain correct
        speeds = [abs(fl), abs(fr), abs(rl), abs(rr)]
        max_speed = max(speeds)
        if max_speed > 1.0:
            fl /= max_speed
            fr /= max_speed
            rl /= max_speed
            rr /= max_speed
            
        # Map the target to ticks
        MAX_TICKS = 25

        cmd_fl = int(fl * MAX_TICKS)
        cmd_fr = int(fr * MAX_TICKS)
        cmd_rl = int(rl * MAX_TICKS)
        cmd_rr = int(rr * MAX_TICKS)
        
        self.latest_command = f"{cmd_fl},{cmd_fr},{cmd_rl},{cmd_rr}\n"

    def timer_callback(self):
        # SEND TO ARDUINO (This feeds the watchdog and synchronizes with the PID)
        if self.serial_port:
            try:
                self.serial_port.write(self.latest_command.encode('utf-8'))

                # Read the ticks for telemetry
                while self.serial_port.in_waiting > 0:
                    line = self.serial_port.readline().decode('utf-8', errors='ignore').strip()
                    if line.startswith("T,"):
                        parts = line.split(',')
                        if len(parts) == 5:
                            try:
                                msg = Int32MultiArray()
                                msg.data = [int(parts[1]), int(parts[2]), int(parts[3]), int(parts[4])]
                                self.tick_pub.publish(msg)
                            except ValueError:
                                # Ignore corrupted packets to prevent crashes.
                                pass
            
            # Manage exceptions
            except serial.SerialTimeoutException:
                self.get_logger().warn("Serial Timeout! Dropping command.")
                self.serial_port.reset_output_buffer()
            except Exception as e:
                self.get_logger().error(f"USB connection lost! Error: {e}")
                self.serial_port.close()
                self.serial_port = None

def main(args=None):
    rclpy.init(args=args)
    twistSubscriber = TwistToSerial()
    
    try:
        rclpy.spin(twistSubscriber)
    except KeyboardInterrupt:
        pass
    finally:
        if twistSubscriber.serial_port:
            try:
                twistSubscriber.serial_port.write(b"0,0,0,0\n")
            except Exception:
                pass
            twistSubscriber.serial_port.close()
        twistSubscriber.destroy_node()
        rclpy.shutdown()
    
if __name__ == '__main__':
    main()