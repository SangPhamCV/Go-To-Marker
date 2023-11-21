#!/usr/bin/env python3

# This script finds an ArUco marker and creates a marker transform to map

import rospy
import tf2_ros
import actionlib
from geometry_msgs.msg import PoseStamped
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
from geometry_msgs.msg import PoseStamped, Quaternion, Twist

class MapToAruco:
    def __init__(self):
        self.cmd_vel_pub = rospy.Publisher('/cmd_vel', Twist, queue_size=10)

        self.tf_buffer = tf2_ros.Buffer(rospy.Duration(2.0))
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer)
        self.client = actionlib.SimpleActionClient('move_base', MoveBaseAction)
        self.client.wait_for_server() # test edit online on github
 
        self.marker_pose = None
    
    def rotate_robot(self, source_frame):
        rospy.logwarn("Begin rotating to check for marker!")
        rate = rospy.Rate(5)  # Adjust the rate as needed
        while not rospy.is_shutdown():
            cmd_vel_msg = Twist()
            cmd_vel_msg.angular.z = 0.23
            self.cmd_vel_pub.publish(cmd_vel_msg)
            rospy.sleep(1)
            cmd_vel_msg.angular.z = 0
            self.cmd_vel_pub.publish(cmd_vel_msg)

            if self.tf_buffer.can_transform("map", source_frame, rospy.Time(0), rospy.Duration(2.0)):
                rospy.loginfo("Transformation is now available after rotation.")
                cmd_vel_msg.angular.z = 0.0
                self.cmd_vel_pub.publish(cmd_vel_msg)
                return
            rate.sleep()

    def run(self):
        source_frame = "aruco_marker_frame"  # Replace with your actual source frame name
        if not source_frame:
            raise ValueError("Source frame name is empty")

        try:
            if self.tf_buffer.can_transform("map", source_frame, rospy.Time(0), rospy.Duration(2.0)):
                transform = self.tf_buffer.lookup_transform("map", source_frame, rospy.Time(0), rospy.Duration(2.0))

                self.marker_pose = PoseStamped()
                self.marker_pose.header = transform.header
                self.marker_pose.pose.position = transform.transform.translation
                self.marker_pose.pose.orientation = transform.transform.rotation
             
            else:
                rospy.logwarn("Transformation from %s to map not available.", source_frame)
                self.rotate_robot(source_frame)
                rospy.sleep(1)
                self.run()

        except (tf2_ros.LookupException, tf2_ros.ConnectivityException, tf2_ros.ExtrapolationException, ValueError) as e:
            rospy.logerr("Error while transforming and navigating: %s", str(e))


# if __name__ == '__main__':
#     rospy.init_node('map_to_aruco')
#     ahaha = MapToAruco()
#     ahaha.run()  # Call the run method to populate marker_pose
