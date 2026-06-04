cmake_minimum_required(VERSION 3.8)
project(reeman_clone_description)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclcpp_components REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(robot_state_publisher REQUIRED)
find_package(xacro REQUIRED)
find_package(controller_manager REQUIRED)
find_package(ros2_control REQUIRED)
find_package(ros2_controllers REQUIRED)
find_package(diff_drive_controller REQUIRED)
find_package(joint_state_broadcaster REQUIRED)
find_package(ros_gz_sim REQUIRED)
find_package(ros_gz_bridge REQUIRED)
find_package(gz_ros2_control REQUIRED)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  # the following line skips the linter which checks for copyrights
  # comment the line when a copyright and license is added to all source files
  set(ament_cmake_copyright_FOUND TRUE)
  # the following line skips cpplint (only works in a git repo)
  # comment the line when this package is in a git repo and when
  # a copyright and license is added to all source files
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

install(
  DIRECTORY
    config
    launch
    meshes
    worlds
    urdf
    rviz
    scripts
  DESTINATION share/${PROJECT_NAME}
)

install(
  PROGRAMS
    #scripts/cmd_vel_relay.py
  DESTINATION lib/${PROJECT_NAME}
)

# ── namespace_adder component ──────────────────────────────────────────────
# Built as a shared library (composable component) for zero-copy IPC, and also
# registered as a standalone executable via rclcpp_components_register_node.
# add_library(namespace_adder_component SHARED
#   src/namespace_adder.cpp
# )
# target_compile_features(namespace_adder_component PUBLIC cxx_std_17)
# ament_target_dependencies(namespace_adder_component
#   rclcpp
#   rclcpp_components
#   sensor_msgs
# )
# rclcpp_components_register_node(namespace_adder_component
#   PLUGIN "NamespaceAdder"
#   EXECUTABLE namespace_adder
# )
install(TARGETS
  # namespace_adder_component
  # namespace_adder
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION lib/${PROJECT_NAME}
)

ament_package()
