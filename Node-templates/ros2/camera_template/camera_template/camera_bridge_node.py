#!/usr/bin/env python3
"""
camera_bridge_node.py

TEMPLATE: bridge for a network camera device (an ESP32 camera board, an IP
camera, or any device that serves an MJPEG stream over HTTP) into ROS 2.
Rename the package and edit the parameters for your device (see README.md).

It never touches drive topics, so a camera that is off, unplugged or
restarting cannot affect driving.

Video (HTTP, a multipart/x-mixed-replace stream of JPEG parts, each with a
Content-Length header; chunked transfer is fine):
  -> camera/image/compressed (sensor_msgs/CompressedImage, format jpeg)
  Each JPEG frame is passed on as it is, without decoding. Many small devices
  serve one stream viewer at a time: close any other viewer (a browser tab)
  while this node runs. The video is read in its own thread, so a slow stream
  never delays the other topics.

Device telemetry (optional, UDP, set telemetry_port; 0 = off):
  A text line broadcast by the device, "KEY: value | KEY: value".
  camera/telemetry_raw (std_msgs/String, the whole line)
  The field named by state_key ("CAM: 1" or "CAM: 0") is the device's camera
  state, published on camera/enabled (std_msgs/Bool, latched). Add the
  device's other fields (sensors) in handle_telemetry().

Camera on/off (optional, UDP, set cmd_port; 0 = off):
  Service camera/enable (std_srvs/SetBool): data true = on, false = off.
  Any node (a navigation stack, a Foxglove service call, the command line)
  can call it. The node sends cmd_on or cmd_off to the device. With telemetry
  on, the command is repeated until the device confirms; without telemetry
  the state is assumed to follow the command. The last request wins.
  While the camera is off the video thread pauses instead of retrying.
"""

import socket
import threading
import urllib.request

import rclpy
from rclpy.node import Node
from rclpy.qos import (
    qos_profile_sensor_data, QoSProfile, ReliabilityPolicy, DurabilityPolicy
)
from sensor_msgs.msg import CompressedImage
from std_msgs.msg import Bool, String
from std_srvs.srv import SetBool

JPEG_START = b'\xff\xd8'


def parse_telemetry(line):
    """'IR: 10 | CAM: 1' -> {'IR': '10', 'CAM': '1'}"""
    fields = {}
    for part in line.split('|'):
        if ':' in part:
            key, value = part.split(':', 1)
            fields[key.strip()] = value.strip()
    return fields


def parse_state(line, key):
    """'CAM: 1' -> True, 'CAM: 0' -> False, anything else -> None."""
    value = parse_telemetry(line).get(key)
    if value == '1':
        return True
    if value == '0':
        return False
    return None


def read_exactly(resp, count):
    data = bytearray()
    while len(data) < count:
        chunk = resp.read(count - len(data))
        if not chunk:
            return None
        data += chunk
    return bytes(data)


def read_frames(url, timeout, should_stop):
    """Yields one JPEG (as bytes) for every frame in the MJPEG stream."""
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        while not should_stop():
            length = None
            while True:
                line = resp.readline()
                if not line:
                    return
                text = line.strip().lower()
                if text.startswith(b'content-length:'):
                    length = int(text.split(b':', 1)[1])
                elif text == b'' and length is not None:
                    break
            frame = read_exactly(resp, length)
            if frame is None:
                return
            if frame.startswith(JPEG_START):
                yield frame


class CameraBridgeNode(Node):

    def __init__(self):
        super().__init__('camera_bridge')

        # ---- Parameters -----------------------------------------------
        # Edit these defaults, or set them in the launch file.
        self.declare_parameter('camera_host', '')            # REQUIRED
        self.declare_parameter('stream_port', 81)
        self.declare_parameter('stream_path', '/stream')
        self.declare_parameter('telemetry_port', 0)          # 0 = no telemetry
        self.declare_parameter('cmd_port', 0)                # 0 = no on/off
        self.declare_parameter('cmd_on', 'CAM,ON')
        self.declare_parameter('cmd_off', 'CAM,OFF')
        self.declare_parameter('state_key', 'CAM')
        self.declare_parameter('telemetry_poll_hz', 50.0)
        self.declare_parameter('read_timeout', 5.0)          # seconds
        self.declare_parameter('reconnect_delay', 2.0)       # seconds
        self.declare_parameter('stats_interval', 30.0)       # seconds
        self.declare_parameter('image_frame_id', 'camera_link')
        self.declare_parameter('command_retries', 5)
        self.declare_parameter('command_retry_period', 1.0)  # seconds

        g = lambda n: self.get_parameter(n).value
        self.camera_host = str(g('camera_host'))
        self.stream_port = int(g('stream_port'))
        self.stream_path = str(g('stream_path'))
        self.telemetry_port = int(g('telemetry_port'))
        self.cmd_port = int(g('cmd_port'))
        self.cmd_on = str(g('cmd_on'))
        self.cmd_off = str(g('cmd_off'))
        self.state_key = str(g('state_key'))
        self.telemetry_poll_hz = float(g('telemetry_poll_hz'))
        self.read_timeout = float(g('read_timeout'))
        self.reconnect_delay = float(g('reconnect_delay'))
        self.stats_interval = float(g('stats_interval'))
        self.image_frame_id = str(g('image_frame_id'))
        self.command_retries = int(g('command_retries'))
        self.command_retry_period = float(g('command_retry_period'))
        self.stream_url = (
            f'http://{self.camera_host}:{self.stream_port}{self.stream_path}'
        )
        self.can_switch = self.cmd_port > 0 and bool(self.camera_host)

        # ---- ROS interfaces ---------------------------------------------
        self.image_pub = self.create_publisher(
            CompressedImage, 'camera/image/compressed', qos_profile_sensor_data
        )
        self.raw_pub = self.create_publisher(String, 'camera/telemetry_raw', 10)
        # Latched, so a node that starts later still gets the current state.
        self.enabled_pub = self.create_publisher(
            Bool, 'camera/enabled',
            QoSProfile(depth=1,
                       reliability=ReliabilityPolicy.RELIABLE,
                       durability=DurabilityPolicy.TRANSIENT_LOCAL)
        )
        self.create_service(SetBool, 'camera/enable', self.enable_service)

        # ---- Sockets ------------------------------------------------------
        self.tx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.rx = None
        if self.telemetry_port > 0:
            try:
                rx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                rx.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                rx.bind(('', self.telemetry_port))
                rx.setblocking(False)
                self.rx = rx
            except (OSError, OverflowError) as exc:
                # Video still works without the telemetry line.
                self.get_logger().error(
                    f'Cannot listen for telemetry on UDP '
                    f'{self.telemetry_port}: {exc}. Telemetry disabled.'
                )
        self.has_feedback = self.rx is not None

        # ---- Camera on/off state ---------------------------------------------
        self.camera_running = None     # what the device last reported
        self.desired = None            # a request still waiting for the device
        self.retries_left = 0

        if self.rx is not None and self.telemetry_poll_hz > 0.0:
            self.create_timer(1.0 / self.telemetry_poll_hz, self.telemetry_timer)
        self.create_timer(self.command_retry_period, self.retry_timer)

        # ---- Video thread -------------------------------------------------
        self.stop_event = threading.Event()
        self.video_allowed = threading.Event()   # cleared while the camera is off
        self.video_allowed.set()
        self.frame_count = 0
        self.stats_time = self.get_clock().now()
        self.video_thread = None

        if not self.camera_host:
            self.get_logger().error(
                'camera_host is not set. Set it in the launch file or with '
                '--ros-args -p camera_host:=<address of the camera>. '
                'The video bridge is not running.'
            )
        else:
            self.video_thread = threading.Thread(
                target=self.video_loop, name='video', daemon=True
            )
            self.video_thread.start()
            self.get_logger().info(
                f'camera_bridge started: video from {self.stream_url}'
            )

    # ---- Video -----------------------------------------------------------
    def video_should_stop(self):
        return self.stop_event.is_set() or not self.video_allowed.is_set()

    def video_loop(self):
        while not self.stop_event.is_set():
            if not self.video_allowed.wait(timeout=0.5):
                continue   # the camera is off: nothing to read
            try:
                self.get_logger().info(
                    f'Connecting to {self.stream_url}',
                    throttle_duration_sec=30.0,
                )
                first_frame = True
                for frame in read_frames(
                        self.stream_url, self.read_timeout,
                        self.video_should_stop):
                    if first_frame:
                        self.get_logger().info('Camera stream connected.')
                        first_frame = False
                    self.publish_frame(frame)
                if self.video_allowed.is_set():
                    self.get_logger().warn('Camera stream ended.',
                                           throttle_duration_sec=10.0)
            except Exception as exc:
                if self.video_allowed.is_set():
                    self.get_logger().warn(f'Camera stream problem: {exc}',
                                           throttle_duration_sec=10.0)
            self.stop_event.wait(self.reconnect_delay)

    def publish_frame(self, frame: bytes):
        msg = CompressedImage()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self.image_frame_id
        msg.format = 'jpeg'
        msg.data = frame
        self.image_pub.publish(msg)

        self.frame_count += 1
        now = self.get_clock().now()
        elapsed = (now - self.stats_time).nanoseconds / 1e9
        if self.stats_interval > 0.0 and elapsed >= self.stats_interval:
            self.get_logger().info(
                f'Video: {self.frame_count / elapsed:.1f} frames/s'
            )
            self.frame_count = 0
            self.stats_time = now

    # ---- Telemetry ----------------------------------------------------------
    def telemetry_timer(self):
        for _ in range(20):   # drain what is waiting, but never spin forever
            try:
                data, _addr = self.rx.recvfrom(256)
            except BlockingIOError:
                return
            except OSError as exc:
                self.get_logger().warn(f'Telemetry receive failed: {exc}',
                                       throttle_duration_sec=5.0)
                return
            self.handle_telemetry(data.decode('utf-8', errors='replace').strip())

    def handle_telemetry(self, line: str):
        if not line:
            return
        self.raw_pub.publish(String(data=line))

        state = parse_state(line, self.state_key)
        if state is not None:
            self.update_camera_state(state)

        # Add the device's other fields here, for example a sensor:
        #   fields = parse_telemetry(line)
        #   if 'Dist' in fields: ... publish a sensor_msgs/Range ...

    # ---- Camera on/off --------------------------------------------------------
    def update_camera_state(self, running: bool):
        if running != self.camera_running:
            self.camera_running = running
            self.enabled_pub.publish(Bool(data=running))
            self.get_logger().info(
                f'Camera is {"on" if running else "off"} (reported by the device)'
            )
        # Follow the device, unless a request is still waiting for it.
        if self.desired is None or running == self.desired:
            if running:
                self.video_allowed.set()
            else:
                self.video_allowed.clear()

    def send_camera_command(self, on: bool):
        text = self.cmd_on if on else self.cmd_off
        try:
            self.tx.sendto(text.encode('utf-8'),
                           (self.camera_host, self.cmd_port))
        except OSError as exc:
            self.get_logger().warn(f'Camera command failed: {exc}',
                                   throttle_duration_sec=5.0)

    def request_camera(self, on: bool, source: str):
        """The last request wins. With telemetry the command is repeated until
        the device confirms; without it the state is assumed to follow."""
        self.desired = on
        self.retries_left = self.command_retries
        if on:
            self.video_allowed.set()
        else:
            self.video_allowed.clear()
        self.send_camera_command(on)
        self.get_logger().info(
            f'Camera {"on" if on else "off"} requested ({source})'
        )
        if not self.has_feedback:
            self.desired = None
            if on != self.camera_running:
                self.camera_running = on
                self.enabled_pub.publish(Bool(data=on))

    def retry_timer(self):
        if self.desired is None:
            return
        if self.camera_running == self.desired:
            self.desired = None
            return
        if self.retries_left <= 0:
            self.get_logger().warn(
                'The camera device did not confirm the camera switch. Is it '
                'powered, and does it report the state field in its telemetry?'
            )
            self.desired = None
            if self.camera_running is None or self.camera_running:
                self.video_allowed.set()   # nothing changed: keep the video going
            return
        self.retries_left -= 1
        self.send_camera_command(self.desired)

    def enable_service(self, request, response):
        if not self.can_switch:
            response.success = False
            response.message = (
                'Camera on/off is not set up: set camera_host and cmd_port.'
            )
            return response
        if self.desired is None and self.camera_running == request.data:
            response.success = True
            response.message = (
                f'The camera is already {"on" if request.data else "off"}.'
            )
            return response
        self.request_camera(bool(request.data), 'service camera/enable')
        response.success = True
        response.message = (
            f'Camera {"on" if request.data else "off"} requested: '
            f'watch camera/enabled for the device\'s answer.'
        )
        return response


def main(args=None):
    rclpy.init(args=args)
    node = CameraBridgeNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        node.stop_event.set()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
