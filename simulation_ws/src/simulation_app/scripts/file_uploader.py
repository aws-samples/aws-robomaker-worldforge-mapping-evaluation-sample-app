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
"""

import rospy
import actionlib
import subprocess
import tf
import os
from robomaker_simulation_msgs.srv import Cancel
from file_uploader_msgs.msg import UploadFilesAction, UploadFilesGoal
from tf.transformations import euler_from_quaternion


class SendData:
    ACTION = "/s3_file_uploader/UploadFiles"
    FILE_PATH = "/tmp/"
    NORM_ONE_DISTANCE_THRESHOLD = 0.1
    ROBOT_STOP_TIMEOUT = 60  #60 seconds of no motion
    TOTAL_MAPPING_TIMEOUT = 600  #10 minutes of mapping time

    def __init__(self):
        self.simulation_id = os.environ["AWS_ROBOMAKER_SIMULATION_JOB_ID"]
        self.last_robot_moving_time = rospy.rostime.time.time()
        self.start_time = rospy.rostime.time.time()
        self.prev_nav_pose = {'x' : 0.0, 'y' : 0.0 }
        self.upload_map_and_terminate = False
        self.sent_terminate_command = False

    def norm_one_distance(self, point_a, point_b):
        return (abs(point_a['x'] - point_b['x']) + abs(point_a['y'] - point_b['y']))

    def write_map_to_disk(self, path, name):
        rospy.loginfo('[file_uploader] Writing map file to disk at {}{}'.format(path,name))
        subprocess.call( ['rosrun', 'map_server', 'map_saver', '-f' , path+name] )

    def upload_file_request(self, path, name):
        rospy.loginfo('[file_uploader] Uploading map file to S3 from {}{}'.format(path,name))
        S3_KEY_PREFIX = "maps/{}/".format(self.simulation_id)

        goal = UploadFilesGoal(
                    upload_location=S3_KEY_PREFIX,
                    files=[path + name  + ".pgm"]
                )
        client = actionlib.SimpleActionClient(SendData.ACTION, UploadFilesAction)
        client.wait_for_server()
        client.send_goal(goal)

        goal = UploadFilesGoal(
                    upload_location=S3_KEY_PREFIX,
                    files=[path + name  + ".yaml"]
                )
        client = actionlib.SimpleActionClient(SendData.ACTION, UploadFilesAction)
        client.wait_for_server()
        client.send_goal(goal)


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

                if self.norm_one_distance( nav_pose, self.prev_nav_pose ) > SendData.NORM_ONE_DISTANCE_THRESHOLD:
                    self.last_robot_moving_time = rospy.rostime.time.time()
                    self.prev_nav_pose = nav_pose

                if (rospy.rostime.time.time() - self.last_robot_moving_time) > SendData.ROBOT_STOP_TIMEOUT:
                    rospy.logwarn('[file_uploader] Robot no longer moving')
                    self.upload_map_and_terminate = True

                if (rospy.rostime.time.time() - self.start_time) > SendData.TOTAL_MAPPING_TIMEOUT:
                    rospy.logwarn('[file_uploader] Simulation time threshold reached')
                    self.upload_map_and_terminate = True

                if (self.sent_terminate_command is False) and (self.upload_map_and_terminate is True):
                    self.write_map_to_disk(SendData.FILE_PATH, self.simulation_id)
                    self.upload_file_request(SendData.FILE_PATH, self.simulation_id)
                    self.cancel_job()
                    
            except (tf.LookupException, tf.ConnectivityException, tf.ExtrapolationException):
                rospy.loginfo("[file_uploader] TF exception in gathering current position")

            rate.sleep()

if __name__ == '__main__':
    rospy.init_node('map_data_uploader')
    send_data = SendData()
    send_data.main()
