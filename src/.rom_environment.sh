#!/bin/bash
# ROM Robot Configuration

export ROM_SIMULATION=true
# for URDF and ROS2 pkg interchange
#export ROM_ROBOT_MODEL=rom2109
#export ROM_ROBOT_MODEL=yoyo
#export ROM_ROBOT_MODEL=robot2
export ROM_ROBOT_MODEL=bobo

# for Topic seperation
#export ROM_ROBOT_NAME=default_robot1
export ROM_ROBOT_NAMESPACE=default_robot1

# rplidar_a1, rplidar_a2, litra_r1
export ROM_LASER_MODEL=litra_r1

# export ROM_IMU_MODEL=
# export ROM_CAM_MODEL=
# export ROM_3DCAM_MODEL=
# export ROM_GPS_MODEL=
# export ROM_LIMIT_SENSOR_MODEL=
# export ROM_BUMP_SENSOR_MODEL=
# export ROM_WEIGHT_SENSOR_MODEL=

export USE_WITMOTION_USB_IMU=false
export USE_ROM_IMU=true
# export USE_CAM=false
# export USE_3DCAM=false
# export USE_GPS=false
# export USE_LIMIT_SENSOR=false
# export USE_BUMP_SENSOR=false
# export USE_WEIGHT_SENSOR=false    
# export USE_LIDAR=false

# ROS 2 Configuration
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
#export RWM_IMPLEMENTATION=rmw_zenoh_cpp

export ROM_ROS_BRIDGE_SECURITY_TYPE=free #secure

#export ROS_DOMAIN_ID=99
#export ROS_IP=192.168.1.4

source /opt/ros/humble/setup.bash
source /home/mr_robot/rom_drivers_ws/install/setup.bash
source /home/mr_robot/rom_maintain_ws/install/setup.bash
source /home/mr_robot/rom_nav2_ws/install/setup.bash
source /home/mr_robot/rom_sdk_ws/install/setup.bash
source /home/mr_robot/thirdparty_drivers_ws/install/setup.bash


# alias bb='colcon build && source install/setup.bash'
# alias bb_rm='colcon build && source install/setup.bash && rm -rf src/*'
# alias bb_save='colcon build --executor sequential --parallel-workers 4'
# alias bb_save_rm='colcon build --executor sequential --parallel-workers 4 && rm -rf src/*'
# alias bb_debug='colcon build --cmake-args -DCMAKE_BUILD_TYPE=Debug'
# alias delete_workspace='rm -rf build install log; echo "Done"'
# alias rom_date='date +"%Y-%m-%d-%H:%M:%S"'
# alias bb_save='colcon build --executor sequential --parallel-workers 4'


export GEMINI_API_KEY=xxxxxxx
export OPEN_AI_API_KEY=xxxxxxx



