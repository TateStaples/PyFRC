import time
from resources.Calculations.math_utils import *
from resources.Interfaces.Motors import MotorController


class PID:
    """
    Simple PID control.
    """

    def __init__(self, p=0, i=0, d=0, **kwargs):

        self._get_time = kwargs.pop('get_time', None) or time.time

        # initialze gains
        self.Kp = p
        self.Ki = i
        self.Kd = d

        # The value the controller is trying to get the system to achieve.
        self._target = 0

        # initialize delta t variables
        self._prev_tm = self._get_time()

        self._prev_feedback = 0

        self._error = None

    @property
    def error(self):
        return self._error

    @property
    def target(self):
        return self._target

    @target.setter
    def target(self, v):
        self._target = float(v)

    def __call__(self, feedback, curr_tm=None):
        """ Performs a PID computation and returns a control value.

            This is based on the elapsed time (dt) and the current value of the process variable
            (i.e. the thing we're measuring and trying to change).

        """

        # Calculate error.
        error = self._error = self._target - feedback

        # Calculate time differential.
        if curr_tm is None:
            curr_tm = self._get_time()
        dt = curr_tm - self._prev_tm

        # Initialize output variable.
        alpha = 0

        # Add proportional component.
        alpha -= self.Kp * error

        # Add integral component.
        alpha -= self.Ki * (error * dt)

        # Add differential component (avoiding divide-by-zero).
        if dt > 0:
            alpha -= self.Kd * ((feedback - self._prev_feedback) / float(dt))

        # Maintain memory for next loop.
        self._prev_tm = curr_tm
        self._prev_feedback = feedback

        return alpha


class Feedforward:
    '''
    A standard bad feedforward
    '''
    def __init__(self, ks, kv, ka=0):
        self.ks, self.kv, self.ka = ks, kv, ka

    def __call__(self, vel, acc=0):
        return self.estimate(vel, acc)

    def estimate(self, vel, acc=0):
        return self.ks + vel * self.kv + acc * self.ka  # i have no evidence this works


class DriveController:
    '''
    A class to drive a West-Coast drivetrain
    '''
    def __init__(self, left_control: MotorController, right_control: MotorController):
        self.left = left_control
        self

    def arcade_drive(self, speed, rotation, square_inputs=True):
        if square_inputs:
            speed = apply_sign(speed**2, speed)  # square while perserving sign
            rotation = apply_sign(rotation**2, rotation)

        max_input = apply_sign(max(abs(speed), abs(rotation)), speed)

        if speed >= 0:  # todo: Check if this is valid
            if rotation >= 0:
                left_speed = max_input
                right_speed = speed - rotation
            else:
                left_speed = speed + rotation
                right_speed = max_input
        else:
            if rotation >= 0:
                left_speed = speed + rotation
                right_speed = max_input
            else:
                left_speed = max_input
                right_speed = speed - rotation
        self.left.speed = left_speed
        self.right.speed = right_speed

    def tank_drive(self, left_speed, right_speed):
        self.left.speed = left_speed
        self.right.speed = right_speed


class Ramsete:  # https://github.com/wpilibsuite/allwpilib/blob/master/wpilibNewCommands/src/main/java/edu/wpi/first/wpilibj2/command/RamseteCommand.java
    pass