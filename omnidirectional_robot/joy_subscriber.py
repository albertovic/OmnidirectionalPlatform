import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
import serial
import time
from std_msgs.msg import Int32MultiArray

class JoyToSerial(Node):
    def __init__(self):
        super().__init__('joysubscriber')
        
        # State variable to hold the most recent joystick command
        self.latest_command = "0,0,0,0\n"   

        # Publishes the ticks of the wheels
        self.tick_pub = self.create_publisher(Int32MultiArray, '/wheel_ticks', 10)
        
        # Stablish serial connection with Arduino
        try:
            self.serial_port = serial.Serial('/dev/ttyACM0', 115200, timeout=0.1, write_timeout=0.1)
            self.get_logger().info("Port opened. Waiting 2.5 seconds for Arduino PID to boot...")
            time.sleep(2.5)
            
            self.serial_port.reset_input_buffer()
            self.serial_port.reset_output_buffer()
            self.get_logger().info("Arduino awake! Sending target velocities at 20Hz...")
        except Exception as e:
            self.get_logger().error(f"Failed to connect to Arduino: {e}")
            self.serial_port = None
            
        self.subscriber = self.create_subscription(Joy, '/joy', self.joy_callback, 10)
        
        # Create the PID command every 50ms (20 times a sec)
        self.timer = self.create_timer(0.05, self.timer_callback)
        
    def joy_callback(self, msg):
        # Apply deadzones and curves
        def curve_axis(raw_val, deadzone):
            if abs(raw_val) < deadzone:
                return 0.0
            active = (abs(raw_val) - deadzone) / (1.0 - deadzone)
            curved = active ** 2
            return curved if raw_val > 0 else -curved

        vx = curve_axis(msg.axes[1], deadzone=0.15) 
        vy = curve_axis(msg.axes[0], deadzone=0.15) 
        w  = curve_axis(msg.axes[3], deadzone=0.15) 
        
        # Mecanum Inverse Kinematics
        fl = vx - vy - w
        fr = vx + vy + w
        rl = vx + vy - w
        rr = vx - vy + w
        
        # Normalize the speeds to 0.0 - 1.0 range
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
                                # Ignore corrupted packets to prevent a crashes.
                                pass

                # self.get_logger().info(f"Target Ticks: {self.latest_command.strip()}")
            
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
    joysubscriber = JoyToSerial()
    
    try:
        rclpy.spin(joysubscriber)
    except KeyboardInterrupt:
        pass
    finally:
        if joysubscriber.serial_port:
            try:
                joysubscriber.serial_port.write(b"0,0,0,0\n")
            except Exception:
                pass
            joysubscriber.serial_port.close()
        joysubscriber.destroy_node()
        rclpy.shutdown()
    
if __name__ == '__main__':
    main()
