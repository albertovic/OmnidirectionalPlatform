import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image

class PersonDetector(Node):
    def __init__(self):
        super().__init__('person_detector')

        # Subscribe to the raw image topic
        self.subscription = self.create_subscription(
            Image,
            '/image_raw', 
            self.image_callback,
            1)
    
    def image_callback(self, msg):
        # Extract size and check for correct encoding
        width = msg.width
        height = msg.height
        if msg.encoding != "rgb8":
            self.get_logger().error(f"Wrong image encoding. Should be rgb8.")
        
        self.get_logger().info(f"Got {width}x{height} {msg.encoding}", throttle_duration_sec=1.0)


def main(args=None):
    rclpy.init(args=args)
    node = PersonDetector()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
    
if __name__ == '__main__':
    main()