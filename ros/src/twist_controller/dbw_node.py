#!/usr/bin/env python

import rospy
from std_msgs.msg import Bool
from dbw_mkz_msgs.msg import ThrottleCmd, SteeringCmd, BrakeCmd, SteeringReport
from geometry_msgs.msg import TwistStamped
import math

from twist_controller import Controller
from yaw_controller import YawController

'''
You can build this node only after you have built (or partially built) the `waypoint_updater` node.

You will subscribe to `/twist_cmd` message which provides the proposed linear and angular velocities.
You can subscribe to any other message that you find important or refer to the document for list
of messages subscribed to by the reference implementation of this node.

One thing to keep in mind while building this node and the `twist_controller` class is the status
of `dbw_enabled`. While in the simulator, its enabled all the time, in the real car, that will
not be the case. This may cause your PID controller to accumulate error because the car could
temporarily be driven by a human instead of your controller.

We have provided two launch files with this node. Vehicle specific values (like vehicle_mass,
wheel_base) etc should not be altered in these files.

We have also provided some reference implementations for PID controller and other utility classes.
You are free to use them or build your own.

Once you have the proposed throttle, brake, and steer values, publish it on the various publishers
that we have created in the `__init__` function.

'''

class DBWNode(object):
    def __init__(self):
        rospy.init_node('dbw_node')

        vehicle_mass = rospy.get_param('~vehicle_mass', 1736.35)
        fuel_capacity = rospy.get_param('~fuel_capacity', 13.5)
        brake_deadband = rospy.get_param('~brake_deadband', .1)
        decel_limit = rospy.get_param('~decel_limit', -5)
        accel_limit = rospy.get_param('~accel_limit', 1.)
        wheel_radius = rospy.get_param('~wheel_radius', 0.2413)
        wheel_base = rospy.get_param('~wheel_base', 2.8498)
        steer_ratio = rospy.get_param('~steer_ratio', 14.8)
        max_lat_accel = rospy.get_param('~max_lat_accel', 3.)
        max_steer_angle = rospy.get_param('~max_steer_angle', 8.)

        self.steer_pub = rospy.Publisher('/vehicle/steering_cmd',
                                         SteeringCmd, queue_size=1)
        self.throttle_pub = rospy.Publisher('/vehicle/throttle_cmd',
                                            ThrottleCmd, queue_size=1)
        self.brake_pub = rospy.Publisher('/vehicle/brake_cmd',
                                         BrakeCmd, queue_size=1)

        # TODO: Create `TwistController` object
        # self.controller = TwistController(<Arguments you wish to provide>)

        self.controller = Controller()
        #get steer controller
        #YawController(object):
            #def __init__(self, wheel_base, steer_ratio, min_speed, max_lat_accel, max_steer_angle):

        min_speed = 0 #2.2352 #5MPH
        self.steer_controller = YawController(wheel_base, steer_ratio, min_speed, max_lat_accel, max_steer_angle)

        # TODO: Subscribe to all the topics you need to
        # subscribe to /twist_cmd topic
        rospy.Subscriber('/twist_cmd', TwistStamped, self.twistcmd_cb)
        #subscribe to dbw enable topic
        rospy.Subscriber('/vehicle/dbw_enabled', Bool, self.dbw_enable_cb)
        #subscribe to /current_velocity topic
        rospy.Subscriber('/current_velocity', TwistStamped, self.current_velocity_cb)

        self.dbw_enable_flag = False
        self.target_linear_velocity = 0
        self.target_angular_velocity = 0
        self.current_linear_velocity = 0
        self.current_angular_velocity = 0
        #self.brake_max = decel_limit * vehicle_mass * wheel_radius
        self.vehicle_mass = vehicle_mass
        self.fuel_capacity = fuel_capacity
        self.decel_limit = decel_limit
        self.wheel_radius = wheel_radius

        self.loop()

    def loop(self):
        rate = rospy.Rate(50) # 50Hz
        while not rospy.is_shutdown():
            # TODO: Get predicted throttle, brake, and steering using `twist_controller`
            # You should only publish the control commands if dbw is enabled
            # throttle, brake, steering = self.controller.control(<proposed linear velocity>,
            #                                                     <proposed angular velocity>,
            #                                                     <current linear velocity>,
            #                                                     <dbw status>,
            #                                                     <any other argument you need>)
            # if <dbw is enabled>:
            #   self.publish(throttle, brake, steer)

            if self.dbw_enable_flag == True:

                control_parameter_dict = {}

                control_parameter_dict['current_vel'] =  self.current_linear_velocity
                control_parameter_dict['target_vel'] =  self.target_linear_velocity
                control_parameter_dict['target_angular_vel'] =  self.target_angular_velocity
                control_parameter_dict['yaw_control'] =  self.steer_controller
                control_parameter_dict['dbw_enable_flag'] =  self.dbw_enable_flag

                control_parameter_dict['decel_limit'] =  self.decel_limit
                control_parameter_dict['vehicle_mass'] =  self.vehicle_mass
                control_parameter_dict['fuel_capacity'] =  self.fuel_capacity
                control_parameter_dict['wheel_radius'] =  self.wheel_radius

                throttle, brake, steering = self.controller.control(**control_parameter_dict)
                if self.target_linear_velocity < 0.01:
                    throttle = 0.0;
                    brake = 5.0;

                #Need to adjust brake as torque, the controller is returning [0, -1] for brake
                self.publish(throttle, brake, steering)
            else:
                self.controller.pid_controller.reset()
                self.controller.throttle_filter.reset()
                self.controller.steer_filter.reset()


            rate.sleep()

    def publish(self, throttle, brake, steer):
        tcmd = ThrottleCmd()
        tcmd.enable = True
        tcmd.pedal_cmd_type = ThrottleCmd.CMD_PERCENT
        tcmd.pedal_cmd = throttle
        self.throttle_pub.publish(tcmd)

        scmd = SteeringCmd()
        scmd.enable = True
        scmd.steering_wheel_angle_cmd = steer
        self.steer_pub.publish(scmd)

        bcmd = BrakeCmd()
        bcmd.enable = True
        bcmd.pedal_cmd_type = BrakeCmd.CMD_TORQUE
        bcmd.pedal_cmd = brake
        self.brake_pub.publish(bcmd)

    def twistcmd_cb(self, twist_cmd_msg):
        self.target_linear_velocity = twist_cmd_msg.twist.linear.x
        self.target_angular_velocity = twist_cmd_msg.twist.angular.z

    def dbw_enable_cb(self, dbw_cmd_msg):
        self.dbw_enable_flag = dbw_cmd_msg.data

    def current_velocity_cb(self, current_velocity_msg):
        self.current_linear_velocity = current_velocity_msg.twist.linear.x
        self.current_angular_velocity = current_velocity_msg.twist.angular.z

if __name__ == '__main__':
    DBWNode()
