#!/usr/bin/env python3
import os
from launch import LaunchDescription
from launch.actions import RegisterEventHandler, DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription, TimerAction, GroupAction
from launch.event_handlers import OnProcessExit
from launch.substitutions import Command, FindExecutable, PathJoinSubstitution
from ament_index_python.packages import get_package_share_directory
from launch_ros.actions import Node, PushRosNamespace
from launch_ros.substitutions import FindPackageShare
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.descriptions import ParameterValue
from launch.launch_description_sources import PythonLaunchDescriptionSource
def generate_launch_description():
    rom_robot_name = os.environ.get('ROM_ROBOT_MODEL', 'bobo')
    rom_simulation = os.environ.get('ROM_SIMULATION', 'false').lower() == 'true'
    rom_robot_namespace = os.environ.get('ROM_ROBOT_NAMESPACE', '' if rom_simulation else 'default_robot1')

    # rplidar_a1, rplidar_a2, litra_r1
    # ltme_1, ltme_2, lti1, lakibeam, bluesea
    rom_laser_name = os.environ.get('ROM_LASER_MODEL', 'rplidar_a2')

    use_lidar = LaunchConfiguration('use_lidar')
    use_imu = LaunchConfiguration('use_imu')
    use_stm32_imu = LaunchConfiguration('use_stm32_imu')
    use_rviz = LaunchConfiguration('use_rviz')

    # Get URDF via xacro
    robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            PathJoinSubstitution(
                [FindPackageShare('total_description'), "urdf", f'{rom_robot_name}.urdf.xacro']
            ),
        ]
    )
    robot_description = {"robot_description": ParameterValue(robot_description_content, value_type=str)}

    robot_controllers = PathJoinSubstitution(
        [
            FindPackageShare(f'{rom_robot_name}_controller'),
            "config",
            f'{rom_robot_name}_controllers.yaml',
        ]
    )

    rviz_config_file = PathJoinSubstitution(
        [FindPackageShare(f'{rom_robot_name}_controller'), "rviz", "diffbot.rviz"]
    )

    robot_state_pub_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="both",
        parameters=[robot_description],
    )
    
    control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[robot_description, robot_controllers],
        output="both",
    )
    
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="log",
        arguments=["-d", rviz_config_file],
        condition=IfCondition(LaunchConfiguration('use_rviz'))
    )

    cm_name = f'/{rom_robot_namespace}/controller_manager' if rom_robot_namespace else '/controller_manager'

    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "joint_state_broadcaster",
            "--controller-manager",
            cm_name,
            "--param-file",
            robot_controllers,
        ],
    )

    base_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        namespace=rom_robot_namespace,
        arguments=[
            "diff_controller",
            "--controller-manager",
            cm_name,
            "--param-file",
            robot_controllers,
        ],
    )

    gpio_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        namespace=rom_robot_namespace,
        arguments=[
            "gpio_controller",
            "--controller-manager",
            cm_name,
            "--param-file",
            robot_controllers,
        ],
    )

    # Delay rviz start after `joint_state_broadcaster`
    delay_rviz_after_joint_state_broadcaster_spawner = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=joint_state_broadcaster_spawner,
            on_exit=[rviz_node],
        )
    )

    # Delay start of robot_controller after `joint_state_broadcaster`
    delay_base_controller_spawner_after_joint_state_broadcaster_spawner = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=joint_state_broadcaster_spawner,
            on_exit=[base_controller_spawner],
        )
    )

    delay_gpio_after_base_controller_spawner = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=base_controller_spawner,
            on_exit=[gpio_controller_spawner],
        )
    )

    twist_mux_params = os.path.join(get_package_share_directory(f'{rom_robot_name}_controller'), 'config', 'twist_mux.yaml')
    twist_mux_node = Node(
        package="twist_mux",
        executable="twist_mux",
        parameters=[twist_mux_params],
        remappings=[('cmd_vel_out', f'/{rom_robot_namespace}/diff_controller/cmd_vel_unstamped' if rom_robot_namespace else '/diff_controller/cmd_vel_unstamped')]
    )

    rplidar_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(get_package_share_directory(f'{rom_robot_name}_controller'), 'launch', f'{rom_laser_name}.launch.py')]),
        launch_arguments={'use_lidar': use_lidar}.items(),
        condition=IfCondition(use_lidar)
    )

    imu_node = Node(
        package="rom_wit_motion_imu_publisher",
        executable="imu",
        name="imu",
        condition=IfCondition(LaunchConfiguration('use_imu'))
    )

    embedded_imu_node = Node(
        package="bobo_controller",
        executable="imu_topic_changer",
        name="imu_topic_changer",
        condition=IfCondition(LaunchConfiguration('use_stm32_imu'))
    )

    # wit_imu_static_tf_pub = Node(
    #         package='tf2_ros',
    #         executable='static_transform_publisher',
    #         name='static_tf_pub',
    #         condition=IfCondition(LaunchConfiguration('use_imu')),
    #         arguments=['0.007', '0.0000', '-0.05',    # Translation: x, y, z
    ##                    '0.0', '0.0', '0.0', '1.0',  # Rotation: Quaternion (qx, qy, qz, qw) roll = 0, pitch = 180, yaw = 90
    #                    '0.0', '3.14159', '1.5708',  # Rotation: Quaternion (qx, qy, qz, qw) roll = 0, pitch = 180, yaw = 90
    #                    'base_footprint', 'wit_imu_link'],  # Parent frame and child frame
    #     )
    

    # Wrap all nodes in namespace group
    namespaced_nodes = GroupAction(
        actions=[
            PushRosNamespace(rom_robot_namespace),
            control_node,
            robot_state_pub_node,
            joint_state_broadcaster_spawner,
            delay_base_controller_spawner_after_joint_state_broadcaster_spawner,
            twist_mux_node,
            delay_rviz_after_joint_state_broadcaster_spawner,
            delay_gpio_after_base_controller_spawner,
            rplidar_launch,
            imu_node,
            embedded_imu_node,
            # wit_imu_static_tf_pub,
        ]
    )

    nodes = [
        DeclareLaunchArgument('use_lidar', default_value='false', description='Use lidar or Not.'),
        DeclareLaunchArgument('use_imu', default_value='false', description='Use imu or Not.'),
        DeclareLaunchArgument('use_stm32_imu', default_value='false', description='Use STM32 imu or Not.'),
        DeclareLaunchArgument('use_rviz', default_value='false', description='Use rviz or Not.'),
        namespaced_nodes,
    ]

    return LaunchDescription(nodes)
