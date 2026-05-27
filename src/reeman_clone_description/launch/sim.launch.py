from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, RegisterEventHandler, SetEnvironmentVariable, TimerAction
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.actions import IncludeLaunchDescription
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare

urdf_file_name = 'reeman_clone.solidwork.fortress.urdf.xacro'

def generate_launch_description():
    world_file = PathJoinSubstitution([
        FindPackageShare('reeman_clone_description'),
        'worlds',
        'sensors_world.sdf',
    ])

    xacro_file = PathJoinSubstitution([
        FindPackageShare('reeman_clone_description'),
        'urdf',
        urdf_file_name,
    ])

    robot_description = ParameterValue(
        Command([
            FindExecutable(name='xacro'),
            ' ',
            xacro_file,
        ]),
        value_type=str,
    )

    rsp_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[
            {'robot_description': robot_description},
            {'use_sim_time': True},
        ],
    )

    gazebo_resource_path = PathJoinSubstitution([
        FindPackageShare('reeman_clone_description'),
        '..',
    ])

    gz_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=gazebo_resource_path,
    )

    ign_resource_path = SetEnvironmentVariable(
        name='IGN_GAZEBO_RESOURCE_PATH',
        value=gazebo_resource_path,
    )

    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare('ros_gz_sim'),
                'launch',
                'gz_sim.launch.py',
            ])
        ),
        launch_arguments={
            'gz_args': [
                '-r -v 1 ',
                LaunchConfiguration('world'),
            ],
            'on_exit_shutdown': 'true',
        }.items(),
    )

    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        output='screen',
        arguments=[
            '-topic', 'robot_description',
            '-name', 'diffbot',
            '-x', '0.0',
            '-y', '0.0',
            '-z', '0.15',
            '-allow_renaming', 'true',
        ],
    )

    spawn_joint_state_broadcaster = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'joint_state_broadcaster',
            '--controller-manager', '/controller_manager',
            '--controller-manager-timeout', '120',
        ],
        output='screen',
    )

    spawn_diff_drive_controller = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'diff_drive_controller',
            '--controller-manager', '/controller_manager',
            '--controller-manager-timeout', '120',
        ],
        output='screen',
    )

    bridge_node = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        output='screen',
        arguments=[
            # Clock
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
            # IMU sensors
            '/board_imu/data@sensor_msgs/msg/Imu[gz.msgs.IMU',
            '/usb_imu/data@sensor_msgs/msg/Imu[gz.msgs.IMU',
            # RGB camera
            '/camera/image_raw@sensor_msgs/msg/Image[gz.msgs.Image',
            '/camera/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo',
            # 2D Lidar
            '/lidar/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
            '/lidar/scan/points@sensor_msgs/msg/PointCloud2[gz.msgs.PointCloudPacked',
            # 3D Camera (RGBD)
            '/three_d_camera/image@sensor_msgs/msg/Image[gz.msgs.Image',
            '/three_d_camera/depth_image@sensor_msgs/msg/Image[gz.msgs.Image',
            '/three_d_camera/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo',
            '/three_d_camera/points@sensor_msgs/msg/PointCloud2[gz.msgs.PointCloudPacked',
        ],
    )

    # QoS relay: /cmd_vel (RELIABLE) → /diff_drive_controller/cmd_vel_unstamped (BEST_EFFORT)
    # This allows teleop_twist_keyboard (and any standard publisher) to drive the robot
    # without needing --qos-reliability best_effort flags.
    cmd_vel_relay = Node(
        package='reeman_clone_description',
        executable='cmd_vel_relay.py',
        name='cmd_vel_relay',
        output='screen',
    )

    spawn_robot_delayed = TimerAction(period=2.0, actions=[spawn_robot])

    return LaunchDescription([
        DeclareLaunchArgument(
            'world',
            default_value=world_file,
            description='World file to load (default: sensors_world.sdf)',
        ),
        gz_resource_path,
        ign_resource_path,
        rsp_node,
        gz_sim,
        bridge_node,
        cmd_vel_relay,
        spawn_robot_delayed,
        RegisterEventHandler(
            OnProcessExit(
                target_action=spawn_robot,
                on_exit=[spawn_joint_state_broadcaster],
            )
        ),
        RegisterEventHandler(
            OnProcessExit(
                target_action=spawn_joint_state_broadcaster,
                on_exit=[spawn_diff_drive_controller],
            )
        ),
    ])
