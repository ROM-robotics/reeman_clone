from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, RegisterEventHandler, SetEnvironmentVariable, TimerAction
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.actions import IncludeLaunchDescription
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node, PushRosNamespace
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare
from ament_index_python.packages import get_package_share_directory
import os
import sys
import tempfile
import yaml as _yaml

def _get_launch_arg(name, default=''):
    prefix = f'{name}:='
    for arg in sys.argv:
        if arg.startswith(prefix):
            return arg[len(prefix):]
    return default

def _make_namespaced_controller_yaml(namespace, yaml_path):
    """Generate a temp YAML with /{namespace}/key prefixes so gz_ros2_control finds params."""
    with open(yaml_path, 'r') as f:
        config = _yaml.safe_load(f)
    ns_config = {}
    for key, value in config.items():
        ns_config[f'/{namespace}/{key}' if namespace else key] = value
    tmp = tempfile.NamedTemporaryFile(
        mode='w', suffix='.yaml', delete=False, prefix='ros2ctrl_'
    )
    _yaml.dump(ns_config, tmp)
    tmp.flush()
    return tmp.name

def _make_namespaced_rviz_config(namespace, rviz_path):
    """Generate a temp RViz config with namespace-prefixed Fixed Frame."""
    with open(rviz_path, 'r') as f:
        content = f.read()
    # TF frame IDs are absolute (/odom), so Fixed Frame stays 'odom' regardless of namespace
    tmp = tempfile.NamedTemporaryFile(
        mode='w', suffix='.rviz', delete=False, prefix='rviz_ns_'
    )
    tmp.write(content)
    tmp.flush()
    return tmp.name

argument_1 = _get_launch_arg('argument_1', default='')

# urdf_file_name = 'reeman_clone.urdf.xacro'
urdf_file_name = 'reeman_clone_fortress.urdf.xacro'


# world_file_name = 'sensors_world.sdf'
# world_file_name = 'sensors_world_scanniverse_office.sdf'
world_file_name = 'sensors_world_shin_thatedat_office.sdf'
# world_file_name = 'sensors_world_polycam_office.sdf'

if (argument_1 == 'empty_world'):
    world_file_name = 'sensors_world.sdf'
    robot_position = {
        '-x': '0.5',
        '-y': '4.0',
        '-z': '0.015',
        '-R': '0.00',
        '-P': '0.00',
        '-Y': '-1.5708',
    }
elif (argument_1 == 'shin_thatedat_office_floor_plan'):
    world_file_name = 'sensors_world_shin_thatedat_office.sdf'
    robot_position = {
        '-x': '-0.7',
        '-y': '-6.0',
        '-z': '0.02',
        '-R': '0.00',
        '-P': '0.00',
        '-Y': '1.5708',
    }
elif (argument_1 == 'shin_thatedat_office'):
    world_file_name = 'sensors_world_polycam_office.sdf'
    robot_position = {
        '-x': '0.5',
        '-y': '4.0',
        '-z': '0.015',
        '-R': '0.00',
        '-P': '0.00',
        '-Y': '-1.5708',
    }
else:
    world_file_name = 'sensors_world.sdf'  # default world file
    robot_position = {
        '-x': '0.5',
        '-y': '4.0',
        '-z': '0.015',
        '-R': '0.00',
        '-P': '0.00',
        '-Y': '-1.5708',
    }

def generate_launch_description():
    # robot_namespace = os.environ.get('ROM_ROBOT_NAMESPACE', 'default_robot1')
    # robot_namespace = os.environ.get('ROM_ROBOT_NAMESPACE', '')
    # rom_simulation = os.environ.get('ROM_SIMULATION', 'false').lower() == 'true'
    # robot_namespace = os.environ.get('ROM_ROBOT_NAMESPACE', '' if rom_simulation else 'default_robot1')
    robot_namespace = os.environ.get('ROM_ROBOT_NAMESPACE', 'default_robot1')

    cm_name = f'/{robot_namespace}/controller_manager' if robot_namespace else '/controller_manager'

    base_controller_yaml = os.path.join(
        get_package_share_directory('reeman_clone_description'),
        'config', 'diff_drive_controller.yaml'
    )
    controller_yaml = _make_namespaced_controller_yaml(robot_namespace, base_controller_yaml)

    world_file = PathJoinSubstitution([
        FindPackageShare('reeman_clone_description'),
        'worlds',
        world_file_name,
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
            ' robot_namespace:=',
            robot_namespace,
            ' controller_yaml:=',
            controller_yaml,
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
        parameters=[{'use_sim_time': True}],
        arguments=[
            '-topic', f'/{robot_namespace}/robot_description' if robot_namespace else '/robot_description',
            '-name', robot_namespace if robot_namespace else 'reeman_clone',
            '-x', robot_position['-x'],
            '-y', robot_position['-y'],
            '-z', robot_position['-z'],
            '-R', robot_position['-R'],
            '-P', robot_position['-P'],
            '-Y', robot_position['-Y'],
            '-allow_renaming', 'true',
        ],
    )

    spawn_joint_state_broadcaster = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'joint_state_broadcaster',
            '--controller-manager', cm_name,
            '--controller-manager-timeout', '120',
        ],
        parameters=[{'use_sim_time': True}],
        output='screen',
    )

    spawn_diff_drive_controller = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'diff_controller',
            '--controller-manager', cm_name,
            '--controller-manager-timeout', '120',
        ],
        parameters=[{'use_sim_time': True}],
        output='screen',
    )

    # Gazebo sensor topics use absolute names (leading '/') so PushRosNamespace won't
    # remap them.  We remap explicitly here so every sensor topic is already under
    # /{robot_namespace}/ without needing a separate relay node.
    _ns = robot_namespace  # local alias for readability
    _sensor_topics = [
        '/imu/out',
        '/imu/wit/out',
        '/camera/image_raw',
        '/camera/camera_info',
        '/scan',
        '/scan/points',
        '/three_d_camera/image',
        '/three_d_camera/depth_image',
        '/three_d_camera/camera_info',
        '/three_d_camera/points',
    ]
    bridge_remappings = (
        [(t, f'/{_ns}{t}') for t in _sensor_topics] if _ns else []
    )

    bridge_node = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        output='screen',
        parameters=[{'use_sim_time': True}],
        remappings=bridge_remappings,
        arguments=[
            # Clock (absolute — stays global, no namespace needed)
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
            # IMU sensors
            '/imu/out@sensor_msgs/msg/Imu[gz.msgs.IMU',
            '/imu/wit/out@sensor_msgs/msg/Imu[gz.msgs.IMU',
            # RGB camera
            '/camera/image_raw@sensor_msgs/msg/Image[gz.msgs.Image',
            '/camera/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo',
            # 2D Lidar
            '/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
            '/scan/points@sensor_msgs/msg/PointCloud2[gz.msgs.PointCloudPacked',
            # 3D Camera (RGBD)
            '/three_d_camera/image@sensor_msgs/msg/Image[gz.msgs.Image',
            '/three_d_camera/depth_image@sensor_msgs/msg/Image[gz.msgs.Image',
            '/three_d_camera/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo',
            '/three_d_camera/points@sensor_msgs/msg/PointCloud2[gz.msgs.PointCloudPacked',
        ],
    )

    rqt_publisher_node = Node(
        package='rqt_publisher',
        executable='rqt_publisher',
        name='rqt_publisher',
        output='screen',
        parameters=[{'use_sim_time': True}],
        condition=IfCondition(LaunchConfiguration('use_rqt_publisher')),
    )

    twist_mux_params = os.path.join(get_package_share_directory('reeman_clone_description'), 'config', 'twist_mux.yaml')
    twist_mux_node = Node(
        package="twist_mux",
        executable="twist_mux",
        parameters=[twist_mux_params],
        remappings=[('cmd_vel_out', f'/{robot_namespace}/diff_controller/cmd_vel_unstamped' if robot_namespace else '/diff_controller/cmd_vel_unstamped')]
    )

    base_rviz_config = os.path.join(
        get_package_share_directory('reeman_clone_description'), 'rviz', 'sensor_check.rviz'
    )
    rviz_config_file = _make_namespaced_rviz_config(robot_namespace, base_rviz_config)

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config_file],
        parameters=[{'use_sim_time': True}],
        condition=IfCondition(LaunchConfiguration('use_rviz')),
    )

    spawn_robot_delayed = TimerAction(period=2.0, actions=[spawn_robot])

    return LaunchDescription([
        DeclareLaunchArgument(
            'world',
            default_value=world_file,
            description='World file to load (default: sensors_world.sdf)',
        ),
        DeclareLaunchArgument(
            'use_rqt_publisher',
            default_value='false',
            description='Launch rqt_publisher GUI for manual topic publishing',
        ),
        DeclareLaunchArgument(
            'use_rviz',
            default_value='true',
            description='Launch RViz2 with sensor_check config',
        ),
        gz_resource_path,
        ign_resource_path,
        spawn_robot_delayed,
        GroupAction([
            PushRosNamespace(robot_namespace),
            rsp_node,
            gz_sim,
            bridge_node,
            rqt_publisher_node,
            rviz_node,
            twist_mux_node,
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
        ]),
    ])