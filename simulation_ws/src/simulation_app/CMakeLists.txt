cmake_minimum_required(VERSION 3.0.2)
project(simulation_app)

find_package(catkin REQUIRED COMPONENTS
  rospy
  std_msgs
)

catkin_package()

catkin_install_python(PROGRAMS
    scripts/file_uploader.py
    DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(DIRECTORY launch rviz
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)
include_directories(
# include
  ${catkin_INCLUDE_DIRS}
)
