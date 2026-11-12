# camera_template

A ROS 2 package template for a **network camera device**: an ESP32 camera board, an IP camera, or any device that serves an MJPEG stream over HTTP. Copy it into your robot's workspace, rename it, point it at your camera, and the video appears as a ROS topic that Foxglove (or any other node) can use.

It is a template in the same sense as `robot_template`: real, working starting files that you copy and edit. It contains no robot-specific code.

## What it gives you

| Topic or service | Type | What it is |
|---|---|---|
| `camera/image/compressed` | `sensor_msgs/CompressedImage` | Every JPEG frame of the stream, passed on as it is (no decoding) |
| `camera/enabled` | `std_msgs/Bool` (latched) | The camera state the device last reported |
| `camera/telemetry_raw` | `std_msgs/String` | Every telemetry line the device sends (optional, see below) |
| `camera/enable` | service, `std_srvs/SetBool` | `true` switches the camera on, `false` off (optional, see below) |

The video is read in its own thread, so a slow stream never delays the other topics, and the node reconnects by itself if the device restarts. While the camera is switched off, the node waits quietly instead of retrying.

## What your device needs to provide

Only the first row is required.

| Part | What the device does | Settings |
|---|---|---|
| Video (required) | Answers an HTTP GET with a `multipart/x-mixed-replace` stream. Each part has a `Content-Length` header and one JPEG | `camera_host`, `stream_port`, `stream_path` |
| Telemetry (optional) | Broadcasts text lines over UDP in the form `KEY: value \| KEY: value`. The field named by `state_key` is `1` when the camera is on and `0` when it is off | `telemetry_port` (0 = off), `state_key` |
| On/off (optional) | Accepts a text command over UDP to switch the camera sensor on or off | `cmd_port` (0 = off), `cmd_on`, `cmd_off` |

Without telemetry the node cannot confirm that the device obeyed an on/off command, so it assumes it did. With telemetry it repeats the command until the device confirms it.

## Parameters

| Parameter | Default | Meaning |
|---|---|---|
| `camera_host` | empty | **Required.** The address of the camera. The node does nothing until it is set |
| `stream_port` | `81` | HTTP port of the stream |
| `stream_path` | `/stream` | Path of the stream |
| `telemetry_port` | `0` | UDP port the device broadcasts telemetry on; `0` means no telemetry |
| `cmd_port` | `0` | UDP port the device accepts commands on; `0` means no on/off control |
| `cmd_on`, `cmd_off` | `CAM,ON`, `CAM,OFF` | The command texts |
| `state_key` | `CAM` | The telemetry field that holds the camera state |
| `command_retries`, `command_retry_period` | `5`, `1.0` | How often an unconfirmed command is repeated |
| `read_timeout`, `reconnect_delay` | `5.0`, `2.0` | Seconds |
| `image_frame_id` | `camera_link` | Frame name on the images |

## Using the template

Replace `<repo>` with the folder where you cloned this repository, and `my_camera` with your own package name. Run these in a Konsole:

```bash
cp -r <repo>/Node-templates/ros2/camera_template ~/Robotics/ros2_ws/src/my_camera
cd ~/Robotics/ros2_ws/src/my_camera
mv camera_template my_camera
mv resource/camera_template resource/my_camera
mv launch/camera_template.launch.py launch/my_camera.launch.py
grep -rl camera_template . | xargs sed -i 's/camera_template/my_camera/g'
cd ~/Robotics/ros2_ws
pixi run colcon build --symlink-install --packages-select my_camera
pixi run ros2 launch my_camera my_camera.launch.py camera_host:=<address of the camera>
```

Expected: the build finishes, and the node logs `Camera stream connected.` once it reaches the device. Check the topic:

```bash
cd ~/Robotics/ros2_ws && pixi run ros2 topic hz /camera/image/compressed
```

To see the picture, start `foxglove_bridge`, open Foxglove Studio, connect to `ws://localhost:8765`, add an **Image** panel and choose `/camera/image/compressed`.

## Making it yours

- Set the defaults in `camera_bridge_node.py` (or in your launch file) for your device's ports and command texts.
- If your device reports other values in its telemetry line, such as a distance or a temperature, parse them in `handle_telemetry()` and publish them. There is a comment showing where.
- To switch the camera from a gamepad, add a `/joy` subscription that calls `request_camera()` after a held button or axis. The rover repository's camera bridge does this with the D-pad.

## Things to know

- Many small camera boards serve **one stream viewer at a time**. Close any browser tab on the stream while the node runs.
- When the camera is off, the last picture stays in the Image panel, because nothing new is published.
- Video shares your Wi-Fi with any other traffic. A smaller picture or a lower frame rate on the device helps if a robot's drive commands stutter.
- The stream reader was tested against a simulated MJPEG server, and the switching logic against simulated input. Check it on your own device before relying on it.
