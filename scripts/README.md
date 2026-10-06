# Steam Deck scripts

These aren't a ROS 2 package, they're plain scripts and desktop launchers
meant to live directly on the Steam Deck's filesystem, not inside the
ROS workspace.

## Install on the Deck

```bash
mkdir -p ~/Robotics ~/Robotics/logs
cp start_rover_controls.sh stop_rover_controls.sh ~/Robotics/
chmod +x ~/Robotics/start_rover_controls.sh ~/Robotics/stop_rover_controls.sh
cp desktop/*.desktop ~/Desktop/
chmod +x ~/Desktop/RoverControls.desktop ~/Desktop/StopRoverControls.desktop
mkdir -p ~/Robotics/tools
cp tools/*.py ~/Robotics/tools/
```

KDE may ask you to right-click a new `.desktop` icon and explicitly allow
it to run, the first time.

## What's here

- `start_rover_controls.sh` / `stop_rover_controls.sh` - launch and stop
  `rover_control`, `rover_motor_bridge`, and `foxglove_bridge` together,
  detached, with locking so a double-click can't stack a second launch on
  top of a running one.
- `desktop/` - the two desktop icons that call the scripts above.
- `tools/` - standalone UDP test scripts for bring-up and debugging,
  independent of ROS. Stop `rover_motor_bridge` before running either one.

## Not included here

A few one-off scripts used only once during bring-up (a config patch
script, an early single-channel `hold.py`) aren't included, since they
were throwaway and already applied. See `docs/changelog.md` for what they
did.
