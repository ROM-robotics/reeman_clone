#!/usr/bin/env python3
"""
cmd_vel_relay.py
================
Bridges the QoS mismatch between teleop_twist_keyboard and
diff_drive_controller.

  teleop_twist_keyboard  →  /cmd_vel  (RELIABLE)
                                ↓  [this node]
  diff_drive_controller  ←  /diff_drive_controller/cmd_vel_unstamped  (BEST_EFFORT)
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy
from geometry_msgs.msg import Twist


class CmdVelRelay(Node):
    def __init__(self):
        super().__init__('cmd_vel_relay')

        # Publisher → BEST_EFFORT (matches diff_drive_controller subscription)
        pub_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
            durability=DurabilityPolicy.VOLATILE,
        )
        self.publisher = self.create_publisher(
            Twist,
            '/diff_drive_controller/cmd_vel_unstamped',
            pub_qos,
        )

        # Subscriber → RELIABLE (matches teleop_twist_keyboard)
        sub_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
            durability=DurabilityPolicy.VOLATILE,
        )
        self.subscription = self.create_subscription(
            Twist,
            '/cmd_vel',
            self._relay_callback,
            sub_qos,
        )

        self.get_logger().info(
            'cmd_vel_relay started: /cmd_vel (RELIABLE) → '
            '/diff_drive_controller/cmd_vel_unstamped (BEST_EFFORT)'
        )

    def _relay_callback(self, msg: Twist):
        self.publisher.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = CmdVelRelay()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
