#!/usr/bin/env python

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

"""
This rosnode keeps track of the current position of the robot. It also has methods
to save and upload current map available on /map topic. This rosnode has a method
to cancel a RoboMaker simulation, and call it when either the robot has stopped 
moving for a certain time, or the simulation itself has run for a designated time.
"""

import rospy
import subprocess
import tf
from robomaker_simulation_msgs.srv import Cancel
from file_uploader_msgs.msg import UploadFilesAction, UploadFilesGoal
from tf.transformations import euler_from_quaternion


class SendData:
    def __init__(self):
        self.last_robot_moving_time = rospy.rostime.time.time()
        self.start_time = rospy.rostime.time.time()
        self.prev_nav_pose = {'x' : 0.0, 'y' : 0.0 }
        self.write_map_and_terminate = False
        self.sent_terminate_command = False
        self.simulation_id = rospy.get_param('~AWS_ROBOMAKER_SIMULATION_JOB_ID')
        self.ROBOT_STOP_TIMEOUT = rospy.get_param('~ROBOT_STOP_TIMEOUT')
        self.TOTAL_MAPPING_TIMEOUT = rospy.get_param('~TOTAL_MAPPING_TIMEOUT')
        self.NORM_ONE_DISTANCE_THRESHOLD = rospy.get_param('~NORM_ONE_DISTANCE_THRESHOLD')
        self.LOCAL_MAP_WRITE_FOLDER = rospy.get_param('~LOCAL_MAP_WRITE_FOLDER')

    def norm_one_distance(self, point_a, point_b):
        return (abs(point_a['x'] - point_b['x']) + abs(point_a['y'] - point_b['y']))

    def write_map_to_disk(self, path, name):
        rospy.loginfo('[file_uploader] Writing map file to disk at {}{}'.format(path,name))
        subprocess.call( ['rosrun', 'map_server', 'map_saver', '-f' , path+name] )
        
    def cancel_job(self):
        rospy.logwarn('[file_uploader] Terminating robomaker here')
        rospy.wait_for_service("/robomaker/job/cancel")
        requestCancel = rospy.ServiceProxy("/robomaker/job/cancel", Cancel)
        response = requestCancel()
        if response.success:
            self.sent_terminate_command = True
            rospy.loginfo("[file_uploader] Successfully requested cancel job")
        else:
            rospy.logerr("[file_uploader] Cancel request failed: %s", response.message)

    def main(self):
        rate = rospy.Rate(10.0)
        listener = tf.TransformListener()

        while not rospy.is_shutdown():
            try:
                (trans,rot) = listener.lookupTransform('map', '/base_link', rospy.Time(0))
                nav_pose = {}
                nav_pose['x'] = trans[0]
                nav_pose['y'] = trans[1]

                if self.norm_one_distance( nav_pose, self.prev_nav_pose ) > self.NORM_ONE_DISTANCE_THRESHOLD:
                    self.last_robot_moving_time = rospy.rostime.time.time()
                    self.prev_nav_pose = nav_pose

                if (rospy.rostime.time.time() - self.last_robot_moving_time) > self.ROBOT_STOP_TIMEOUT:
                    rospy.logwarn('[file_uploader] Robot no longer moving')
                    self.write_map_and_terminate = True

                if (rospy.rostime.time.time() - self.start_time) > self.TOTAL_MAPPING_TIMEOUT:
                    rospy.logwarn('[file_uploader] Simulation time threshold reached')
                    self.write_map_and_terminate = True

                if (self.sent_terminate_command is False) and (self.write_map_and_terminate is True):
                    self.write_map_to_disk(self.LOCAL_MAP_WRITE_FOLDER, self.simulation_id)
                    self.cancel_job()
                    
            except (tf.LookupException, tf.ConnectivityException, tf.ExtrapolationException):
                rospy.loginfo("[file_uploader] TF exception in gathering current position")

            rate.sleep()

if __name__ == '__main__':
    rospy.init_node('file_uploader')
    send_data = SendData()
    send_data.main()
