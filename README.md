### docker pull
```
docker pull romrobotics/amr:reeman_clone
```

### copy this run scripts
#### start_fortress_reeman_clone
```bash
#!/usr/bin/env bash
# Usage:
#   ./start_fortress_reeman_clone.sh                    # namespace: myanmar_robot_1 (default)
#   ./start_fortress_reeman_clone.sh my_robot_ns        # namespace: my_robot_ns
#
# NOTE: bash --init-file is used so that our namespace wins over any hardcoded
#       export inside the container's ~/.bashrc.

CONTAINER_NAME=sim_rom_01_gz_prod
IMAGE=romrobotics/gz_fortress_ubun22_humble:reeman_clone

ROBOT_NS="${1:-myanmar_robot_1}"

# ── Stop and remove existing container if running ────────────────────────────
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "[start] Stopping and removing existing container: ${CONTAINER_NAME}"
    docker stop "${CONTAINER_NAME}"
    docker rm   "${CONTAINER_NAME}"
fi

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
  --name "${CONTAINER_NAME}" \
  "${IMAGE}" \
  bash -c "source /opt/ros/humble/setup.bash && source /tmp/docker_init.sh && cd /home/mr_robot && tmuxinator"

rm -f "${INIT_SCRIPT}"

# ── Stop and remove existing container if running ────────────────────────────
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "[start] Stopping and removing existing container: ${CONTAINER_NAME}"
    docker stop "${CONTAINER_NAME}"
    docker rm   "${CONTAINER_NAME}"
fi

```

### tmuxinator
```tmux

name: GAZEBO 
root: ~/

pre_window: export PS1=" \[$(tput sgr0)\]\[$(tput bold)\]\[\033[38;5;45m\]>>>\[$(tput sgr0)\] \[$(tput sgr0)\]"

# USE ROM_ROBOT_MODEL as ( bobo | yoyo | rom2109 ) in BASHRC
# WORLDS ( shin_thatedat_office_floor_plan | shin_thatedat_office ) at ros2 launch

startup_window: Main
# startup_pane: 0

windows:
  - Main: 
      root: ~/
      panes:
        - clear; source ~/.bashrc; source /tmp/docker_init.sh; ros2 launch reeman_clone_description sim.launch.py argument_1:=shin_thatedat_office_floor_plan
  - SubscriberLists: 
      root: ~/
      panes:
        - clear; source ~/.bashrc; source /tmp/docker_init.sh; sleep 10; ros2 topic subscribers_list
  - PublisherLists: 
      root: ~/
      panes:
        - clear; source ~/.bashrc; source /tmp/docker_init.sh; sleep 10; ros2 topic publishers_list
  - DanglerOrphans: 
      root: ~/
      panes:
        - clear; source ~/.bashrc; source /tmp/docker_init.sh; sleep 10; ros2 topic leaf_topics_list
```
