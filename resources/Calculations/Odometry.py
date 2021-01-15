from math import cos, sin, pi
from math_utils import *
import time


class Pose:
    def __init__(self, x, y, theta):
        self.x, self.y, self.theta = x, y, theta
        self.x_vel, self.y_vel, self.theta_vel = 0, 0, 0

    def __call__(self, x, y, theta):
        self.x, self.y, self.theta = x, y, theta

    def __iter__(self):
        return iter((self.x, self.y, self.theta))


class Odometry:  # https://github.com/merose/diff_drive/blob/master/src/diff_drive/odometry.py
    def __init__(self, track_width, pose=(0, 0, 0)):
        self.track_width = track_width
        self.pose = Pose(*pose)
        self.previous_time = time.time()

    def update(self, heading, left_move, right_move):  # todo: check if this works
        # leftTravel = self.leftEncoder.getDelta() / self.ticksPerMeter  # idk what ticks per meter is
        # rightTravel = self.rightEncoder.getDelta() / self.ticksPerMeter

        # find how long since last update
        new_time = time.time()
        delta_time = new_time - self.previous_time
        self.previous_time = new_time

        # find how far it went and turning
        delta_move = average(left_move, right_move)
        delta_turn = (right_move - left_move) / self.track_width

        if right_move == left_move:  # if it went straight
            delta_x = left_move * cos(self.pose.theta)
            delta_y = left_move * sin(self.pose.theta)
        else:
            radius = delta_move / delta_turn

            # Find the instantaneous center of curvature (ICC).
            iccX = self.pose.x - radius * sin(self.pose.theta)
            iccY = self.pose.y + radius * cos(self.pose.theta)

            delta_x = cos(delta_turn) * (self.pose.x - iccX) \
                     - sin(delta_turn) * (self.pose.y - iccY) \
                     + iccX - self.pose.x

            delta_y = sin(delta_turn) * (self.pose.x - iccX) \
                     + cos(delta_turn) * (self.pose.y - iccY) \
                     + iccY - self.pose.y

        self.pose.x += delta_x
        self.pose.y += delta_y
        self.pose.theta = (self.pose.theta + delta_turn) % (2 * pi)
        self.pose.x_vel = delta_move / delta_time if delta_time > 0 else 0
        self.pose.y_vel = 0
        self.pose.theta_vel = delta_turn / delta_time if delta_time > 0 else 0

    def reset(self):
        self.pose = Pose(0, 0, 0)


class Gyro:  # todo: find a way to do this
    @property
    def heading(self):
        return 0
