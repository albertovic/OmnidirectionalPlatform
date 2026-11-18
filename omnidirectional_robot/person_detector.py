import rclpy
from rclpy.node import Node
from ultralytics import YOLO
import numpy as np
import time
import math
import cv2
from sensor_msgs.msg import Image, CompressedImage
from vision_msgs.msg import Detection2DArray, Detection2D, ObjectHypothesisWithPose

class PersonDetector(Node):
    def __init__(self):
        super().__init__('person_detector')

        # YOLO parameters
        self.declare_parameter('model_path', '/home/orangepi/ros2_ws_orangepi/src/omnidirectional_robot/models/yolov8n_rknn_model')
        model_path = self.get_parameter('model_path').value
        self.model = YOLO(model_path)

        # Run the model once on an empty array to load the model
        self.model(np.zeros((480, 640, 3), dtype=np.uint8), verbose=False)
        self.get_logger().info(f"Model loaded: {model_path}")

        self.frame_count = 0
        self.last_fps_time = time.perf_counter()

        # Subscribe to the raw image topic
        self.subscription = self.create_subscription(
            Image,
            '/image_raw', 
            self.image_callback,
            1)

        self.debug_pub = self.create_publisher(
            CompressedImage, 
            '/person_detector/debug_image/compressed', 
            1)

        self.det_pub = self.create_publisher(
            Detection2DArray, 
            '/person_detector/detections', 
            10)
    
    def image_callback(self, msg):
        # Extract size and check for correct encoding
        if msg.encoding != "rgb8":
            self.get_logger().error(f"Wrong image encoding. Should be rgb8.")
            return

        # Reshapes 1D array into the 640x480 pixel matrix we want on the three RGB channels
        frame = np.frombuffer(msg.data, dtype=np.uint8).reshape(msg.height, msg.width, 3)
        # Transforms from RGB to BGR
        frame = np.ascontiguousarray(frame[:,:,::-1])

        # Model evaluates the current frame and looks for people (classes [0])
        # Model returns a list with a Results object per image.
        results = self.model(frame, classes=[0], conf=0.5, verbose=False)
        r = results[0]
        detected_boxes = r.boxes
        detections = []
        for box in detected_boxes:
            cx, cy, w, h = box.xywh[0].tolist()
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            conf = float(box.conf[0])
            if not all(math.isfinite(v) for v in (cx, cy, w, h, conf)):
                self.get_logger().warn("Skipping a box with NaN/inf values", throttle_duration_sec=5.0)
                continue
            detections.append([x1, y1, x2, y2, cx, h, conf])

        det_array = Detection2DArray()
        det_array.header = msg.header            # camera timestamp: lets other nodes match it with the LiDAR scan

        for x1, y1, x2, y2, cx, h, conf in detections:
            det = Detection2D()
            det.header = msg.header

            # Box: center + size, in pixels
            det.bbox.center.x = cx
            det.bbox.center.y = (y1 + y2) / 2
            det.bbox.size_x = x2 - x1
            det.bbox.size_y = y2 - y1

            # What it is and how sure the model is
            hyp = ObjectHypothesisWithPose()
            hyp.id = 'person'
            hyp.score = conf
            det.results.append(hyp)

            det_array.detections.append(det)

        self.det_pub.publish(det_array)          # publish every frame, even with 0 detections

        self.get_logger().info(f"Detections: {detections}", throttle_duration_sec=1.0)

        # Debug image: draw only the boxes we accepted
        annotated = frame.copy()
        for x1, y1, x2, y2, cx, h, conf in detections:
            p1 = (int(x1), int(y1))            # top-left corner
            p2 = (int(x2), int(y2))            # bottom-right corner
            cv2.rectangle(annotated, p1, p2, (0, 255, 0), 2)                  # green (BGR), 2 px thick
            cv2.putText(annotated, f"person {conf:.2f}", (p1[0], max(p1[1] - 6, 14)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.circle(annotated, (int(cx), int((y1 + y2) / 2)), 4, (0, 0, 255), -1)  # red dot = center

        debug_msg = CompressedImage()
        debug_msg.header = msg.header
        debug_msg.format = 'jpeg'
        debug_msg.data = cv2.imencode('.jpg', annotated, [cv2.IMWRITE_JPEG_QUALITY, 85])[1].tobytes()
        self.debug_pub.publish(debug_msg)

        self.frame_count += 1
        now = time.perf_counter()
        elapsed = now - self.last_fps_time
        if elapsed >= 1.0:
            self.get_logger().info(f"FPS: {self.frame_count / elapsed:.1f}")
            self.frame_count = 0
            self.last_fps_time = now


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