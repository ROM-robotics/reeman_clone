#!/usr/bin/env bash
# Usage:
#   ./start_fortress_reeman_clone.sh                    # namespace: myanmar_robot_1 (default)
#   ./start_fortress_reeman_clone.sh my_robot_ns        # namespace: my_robot_ns
#
# NOTE: bash --init-file is used so that our namespace wins over any hardcoded
#       export inside the container's ~/.bashrc.

ROBOT_NS="${1:-myanmar_robot_1}"

docker stop simulator_01
docker rm simulator_01
xhost +local:root

# Write a temp init script that sources ~/.bashrc first, then overrides the namespace.
# Mounted read-only into the container so docker --env alone cannot be beaten by .bashrc.
INIT_SCRIPT=$(mktemp /tmp/docker_init_XXXXX.sh)
cat > "${INIT_SCRIPT}" <<INITEOF
[ -f ~/.bashrc ] && source ~/.bashrc
export ROM_ROBOT_NAMESPACE='${ROBOT_NS}'
INITEOF

docker run -it --network='host' \
  --ipc=host \
  -p 80:80 \
  -p 9090:9090 \
  --env='DISPLAY' \
  --env='QT_X11_NO_MITSHM=1' \
  --env="XDG_RUNTIME_DIR=/run/user/${UID}" \
  --env="ROM_ROBOT_NAMESPACE=${ROBOT_NS}" \
  --volume='/tmp/.X11-unix:/tmp/.X11-unix:rw' \
  --volume='/home/mr_robot/Desktop/Git/reeman_clone/src:/home/mr_robot/ros2_ws/src' \
  --volume="${INIT_SCRIPT}:/tmp/docker_init.sh:ro" \
  --name simulator_01 \
  romrobotics/gz_fortress_ubun22_humble:reeman_clone \
  bash --init-file /tmp/docker_init.sh

rm -f "${INIT_SCRIPT}"
docker stop simulator_01
docker rm simulator_01
