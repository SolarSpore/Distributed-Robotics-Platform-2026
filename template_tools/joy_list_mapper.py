#!/usr/bin/env python3
"""
Steam Deck /joy mapper.
Prompts for one control at a time, waits up to 10s for it to register,
logs the exact buttons[]/axes[] index that changed, and prints a
summary at the end (including anything that never registered).
"""

import time
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy

# Threshold for treating an axis value as "changed" (ignores stick/trigger noise)
AXIS_THRESHOLD = 0.3
TIMEOUT_SECONDS = 10.0
BASELINE_SAMPLE_TIME = 0.5

# Controls to test, in order. Edit this list freely.
CONTROLS_TO_TEST = [
    "A",
    "B",
    "X",
    "Y",
    "L1 (LB)",
    "R1 (RB)",
    "L2 (LT) - squeeze",
    "R2 (RT) - squeeze",
    "L3 (left stick click)",
    "R3 (right stick click)",
    "Start / Menu",
    "Select / Back / View",
    "Guide / Steam button",
    "D-pad Up",
    "D-pad Down",
    "D-pad Left",
    "D-pad Right",
    "Left stick Up",
    "Left stick Down",
    "Left stick Left",
    "Left stick Right",
    "Right stick Up",
    "Right stick Down",
    "Right stick Left",
    "Right stick Right",
]


class JoyMapper(Node):
    def __init__(self):
        super().__init__('joy_mapper')
        self.latest_msg = None
        self.subscription = self.create_subscription(
            Joy, '/joy', self.joy_callback, 10
        )

    def joy_callback(self, msg):
        self.latest_msg = msg

    def spin_for(self, seconds):
        """Spin the node for a fixed wall-clock duration."""
        end_time = time.time() + seconds
        while time.time() < end_time:
            rclpy.spin_once(self, timeout_sec=0.02)

    def wait_for_first_message(self):
        print("Waiting for /joy messages...")
        while self.latest_msg is None:
            rclpy.spin_once(self, timeout_sec=0.1)
        print("Receiving /joy data.\n")

    def capture_baseline(self):
        """Average a short window of messages to get a stable baseline."""
        samples = []
        end_time = time.time() + BASELINE_SAMPLE_TIME
        while time.time() < end_time:
            rclpy.spin_once(self, timeout_sec=0.02)
            if self.latest_msg is not None:
                samples.append(self.latest_msg)

        if not samples:
            raise RuntimeError("No /joy messages received while capturing baseline.")

        num_buttons = len(samples[-1].buttons)
        num_axes = len(samples[-1].axes)

        avg_buttons = [0] * num_buttons
        avg_axes = [0.0] * num_axes

        for s in samples:
            for i in range(num_buttons):
                avg_buttons[i] += s.buttons[i]
            for i in range(num_axes):
                avg_axes[i] += s.axes[i]

        avg_buttons = [round(b / len(samples)) for b in avg_buttons]
        avg_axes = [a / len(samples) for a in avg_axes]

        return avg_buttons, avg_axes

    def detect_change(self, baseline_buttons, baseline_axes, timeout):
        """
        Poll /joy until something differs meaningfully from baseline,
        or timeout expires. Returns a list of (kind, index, from, to)
        tuples describing every changed index, or [] on timeout.
        """
        end_time = time.time() + timeout

        while time.time() < end_time:
            rclpy.spin_once(self, timeout_sec=0.02)
            msg = self.latest_msg
            if msg is None:
                continue

            changes = []

            for i, val in enumerate(msg.buttons):
                if i < len(baseline_buttons) and val != baseline_buttons[i]:
                    changes.append(("button", i, baseline_buttons[i], val))

            for i, val in enumerate(msg.axes):
                if i < len(baseline_axes):
                    if abs(val - baseline_axes[i]) > AXIS_THRESHOLD:
                        changes.append(("axis", i, baseline_axes[i], val))

            if changes:
                return changes

        return []


def main():
    rclpy.init()
    mapper = JoyMapper()
    results = {}

    try:
        mapper.wait_for_first_message()

        for control_name in CONTROLS_TO_TEST:
            input(f"\nButton to press: {control_name}  (press Enter when ready, then press it)")

            print("  Capturing baseline (hands off controller)...")
            baseline_buttons, baseline_axes = mapper.capture_baseline()

            print(f"  Now press: {control_name}  (you have {int(TIMEOUT_SECONDS)}s)")
            changes = mapper.detect_change(baseline_buttons, baseline_axes, TIMEOUT_SECONDS)

            if changes:
                # Take the change with the largest magnitude as the primary hit
                def magnitude(c):
                    kind, idx, frm, to = c
                    return abs(to - frm)

                changes.sort(key=magnitude, reverse=True)
                kind, idx, frm, to = changes[0]

                if kind == "button":
                    label = f"buttons[{idx}]  ({frm} -> {to})"
                else:
                    label = f"axes[{idx}]  ({frm:.2f} -> {to:.2f})"

                print(f"  LOGGED: {control_name} -> {label}")
                results[control_name] = label

                if len(changes) > 1:
                    extra = ", ".join(
                        f"{'buttons' if k=='button' else 'axes'}[{i}]"
                        for k, i, f, t in changes[1:]
                    )
                    print(f"  (also moved: {extra})")
            else:
                print(f"  NOT REGISTERED: no change detected within {int(TIMEOUT_SECONDS)}s")
                results[control_name] = "NOT REGISTERED"

        # ---- Summary ----
        print("\n" + "=" * 50)
        print("SUMMARY")
        print("=" * 50)
        for control_name in CONTROLS_TO_TEST:
            print(f"{control_name:30s} -> {results[control_name]}")

        not_registered = [c for c, v in results.items() if v == "NOT REGISTERED"]
        if not_registered:
            print("\nControls that did not register:")
            for c in not_registered:
                print(f"  - {c}")
        else:
            print("\nAll controls registered.")

    except KeyboardInterrupt:
        print("\nInterrupted.")
    finally:
        mapper.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
