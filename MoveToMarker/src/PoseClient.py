#!/usr/bin/env python3

# This script moves the robot to the ArUco marker's position.

import rospy
from movetomarker.srv import GetMclPose, GetMclPoseRequest, GetArucoPose, GetArucoPoseRequest
import actionlib
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
from math import *
import tf.transformations as tf_trans
from MapToAruco import MapToAruco


mcl_yaw_data = None
aruco_pitch_data = None

def request_mcl_orientation():
    rospy.wait_for_service('/get_mcl_pose')
    global mcl_yaw_data
    try:
        get_mcl_pose = rospy.ServiceProxy('/get_mcl_pose', GetMclPose)
        response = get_mcl_pose(GetMclPoseRequest())
        mcl_orientation = response.mcl_pose.pose.orientation
        euler_angles = tf_trans.euler_from_quaternion([mcl_orientation.x, mcl_orientation.y, mcl_orientation.z, mcl_orientation.w])
        mcl_roll_data, mcl_pitch_data, mcl_yaw_data = euler_angles

        return mcl_yaw_data
    
    except rospy.ServiceException as e:
        rospy.logerr("Service call failed: %s", e)

def request_aruco_pose():
    rospy.wait_for_service('/get_aruco_pose')
    global aruco_pitch_data
    try:
        get_aruco_pose = rospy.ServiceProxy('/get_aruco_pose', GetArucoPose)
        response = get_aruco_pose(GetArucoPoseRequest())
        aruco_orientation = response.aruco_pose.pose.orientation
        euler_angles = tf_trans.euler_from_quaternion([aruco_orientation.x, aruco_orientation.y, aruco_orientation.z, aruco_orientation.w])
        aruco_roll_data, aruco_pitch_data, aruco_yaw_data = euler_angles

        return aruco_pitch_data
    
    except rospy.ServiceException as e:
        rospy.logerr("Service call failed: %s", e)


def movebase_client(x, y):
    global aruco_pitch_data
    global mcl_yaw_data
    d = 0.35
    new_x = None
    new_y = None
    theta = mcl_yaw_data - aruco_pitch_data
    new_theta = theta + pi
    z_value = sin(new_theta/2)
    w_value = cos(new_theta/2)

    if theta > 0 and theta < pi/2:
        new_x = x - d * cos(theta)
        new_y = y - d * sin(theta)
    elif theta < 0 and theta > -pi/2:
        new_x = x - d * cos(theta)
        new_y = y - d * sin(theta)
    elif theta > pi/2 and theta < pi:
        new_x = x + d * cos(pi - theta)
        new_y = y - d * sin(pi - theta) 
    elif theta < -pi/2 and theta > -pi:
        new_x = x + d * cos(pi + theta)
        new_y = y + d * sin(pi + theta)
    elif theta == 0:
        new_x = x - d
        new_y = y
    elif theta == -pi/2:
        new_x = x
        new_y = y + d
    elif theta == pi or theta == -pi:
        new_x = x + d
        new_y = y
    elif theta == pi/2:
        new_x = x
        new_y = y - d

    rospy.loginfo(f"new x: {new_x}, new y: {new_y}, new theta: {theta}")
    rospy.loginfo(f"x: {x}, y: {y}, theta: {theta}")

    client = actionlib.SimpleActionClient('move_base',MoveBaseAction)
    client.wait_for_server()
    if new_x is not None and new_y is not None:
        goal = MoveBaseGoal()
        goal.target_pose.header.frame_id = "map"
        goal.target_pose.header.stamp = rospy.Time.now()
        goal.target_pose.pose.position.x = new_x
        goal.target_pose.pose.position.y = new_y

        goal.target_pose.pose.orientation.z = z_value
        goal.target_pose.pose.orientation.w = w_value

        rospy.loginfo(goal.target_pose)
        client.send_goal(goal)
        wait = client.wait_for_result()
        if not wait:
            rospy.logerr("Action server not available!")
            rospy.signal_shutdown("Action server not available!")
        else:
            return client.get_result()
        

if __name__ == '__main__':
    rospy.init_node('pose_client')
    map_aruco = MapToAruco()
    map_aruco.run()

    request_mcl_orientation()
    request_aruco_pose()

    if aruco_pitch_data is not None and mcl_yaw_data is not None:
        result = movebase_client(map_aruco.marker_pose.pose.position.x, map_aruco.marker_pose.pose.position.y)
        if result:
            rospy.logwarn("Finished moving to marker!")