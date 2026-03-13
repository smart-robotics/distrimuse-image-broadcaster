# cam_recorder

Stream IP cameras as ROS2 topics with optional rosbag recording and replay.

## Setup

```bash
pixi install
```

## Configuration

Copy the example config and fill in your camera credentials:

```bash
cp config/config.yaml.example config/config.yaml
```

Edit `config/config.yaml` with your camera names, RTSP URLs, desired FPS, and topic template. See the comments in the file for details.

## Tasks

| Task | Description | Usage |
|------|-------------|-------|
| `broadcast` | Publish camera streams as ROS2 Image topics | `pixi run broadcast` |
| `replay` | Replay a rosbag recording with image display | `pixi run replay <bag_path>` |
| `view` | Display live camera topics in OpenCV windows | `pixi run view` |
| `test` | Run the test suite | `pixi run test` |

### broadcast

Starts a ROS2 node that captures RTSP streams and publishes them as `sensor_msgs/msg/Image` on `/camera/<name>/image_raw` topics.

```bash
# Use default cameras
pixi run broadcast

# Record to rosbag while broadcasting
pixi run broadcast --collect-bag

# Custom camera and FPS
pixi run broadcast --camera cam0=rtsp://user:pass@host:554/stream --fps 10

# Specify bag output path
pixi run broadcast --collect-bag --bag-path ./bags/my_recording
```

### replay

Replays a rosbag and displays the images in OpenCV windows with timestamps overlaid.

```bash
pixi run replay bags/recording_20260312_120000

# Loop playback
pixi run replay bags/recording_20260312_120000 --loop

# Adjust playback speed
pixi run replay bags/recording_20260312_120000 --rate 2.0

# Replay without display
pixi run replay bags/recording_20260312_120000 --no-display
```

### view

Subscribes to camera image topics and displays them in OpenCV windows with timestamps.

```bash
# View default camera topics
pixi run view

# View specific topics
pixi run view --topic /camera/cam0/image_raw --topic /camera/cam1/image_raw
```
