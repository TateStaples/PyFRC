import odrive
from odrive.enums import *
import constants, time


driver = None


def connect_to_motors():
    global driver
    if constants.O_DRIVE_SERIAL is None:
        driver = odrive.find_any(timeout=60)
    else:  # todo: check these configs
        driver = odrive.find_any(path='usb', serial_number=constants.O_DRIVE_SERIAL, search_cancellation_token=None, channel_termination_token=None, timeout=60)


class MotorController:  # abstract base class
    '''
    Abstract base motor controller class
    '''
    @property
    def speed(self):  # override this
        pass

    @speed.setter
    def speed(self, vel):
        self._set_speed(vel)

    def _set_speed(self, vel):
        pass


class ODrive(MotorController):
    '''
    A wrapper for the odrive module, given the number of a odrive motor it can perform important actions
    '''
    def __init__(self, *axes):
        if driver is None:
            connect_to_motors()
        self.motors = [driver.__getattribute__(f"axis{i}") for i in axes]
        self.indices = axes
        self.engage()
        self._input = None
        self._control = None

    def disconnect(self):
        driver.release()

    def calibrate(self):  # this should never be called during normal play
        for i, axis in enumerate(self.motors):
            axis.requested_state = AXIS_STATE_FULL_CALIBRATION_SEQUENCE

            while axis.current_state != AXIS_STATE_IDLE:  # carry out the sequence until done
                time.sleep(0.1)

            # axis.motor.config.pre_calibrated = True  # todo: this might be true
            # axis.encoder.config.pre_calibrated = True
            if axis.error != 0:
                return False
        return True

    def engage(self):
        for axis in self.motors:
            axis.controller.vel_setpoint = 0
            axis.requested_state = AXIS_STATE_CLOSED_LOOP_CONTROL
            axis.controller.config.control_mode = CONTROL_MODE_VELOCITY_CONTROL

    def apply_pid(self, p, i=0, d=0):  # odrive comes with its own control loop
        pass

    def apply_feedforward(self, feedforward):  # todo: figure out how to do this
        pass

    def speed(self, index=None):
        num_motors = len(self.motors)
        if num_motors == 1:
            return self.motors[0].encoder.vel_estimate
        elif index is None:
            return [axis.encoder.vel_estimate for axis in self.motors]
        else:
            return self.motors[index].encoder.vel_estimate

    def _set_speed(self, vel):
        self._assert_input_mode(INPUT_MODE_VEL_RAMP)
        self._assert_control_mode(CONTROL_MODE_VELOCITY_CONTROL)
        for axis in self.motors:
            axis.controller.vel_setpoint = vel

    def _assert_control_mode(self, mode: int):
        if self._control != mode:
            self._control = mode
            for axis in self.motors:
                axis.controller.config.control_mode = mode

    def _assert_input_mode(self, mode: int):
        if self._input != mode:
            self._input = mode
            for axis in self.motors:
                axis.controller.config.input_mode = mode

    def mirror(self, other: MotorController, ratio=1):
        self._assert_control_mode(CONTROL_MODE_POSITION_CONTROL)
        self._assert_input_mode(INPUT_MODE_MIRROR)
        axis_number = other.motors.indices[0]
        for axis in self.motors:
            axis.controller.config.mirror_ratio = ratio
            axis.controller.config.axis_to_mirror = axis_number


class Encoder:
    '''
    Wrapper for an ODrive encoder
    '''
    def __init__(self, axis_number):
        self._inner = driver.__get_attr__(f'axis{axis_number}').encoder

    @property
    def position(self):
        return self._inner.pos_estimate

    @property
    def velocity(self):
        return self._inner.vel_estimate



"""
import serial, time, logging
from serial.serialutil import SerialException


# code based on: https://github.com/MarquetteRMC/Software/blob/eaeef743a38b8e9880a75a0036bf67f27eff8ad6/ros/src/odrive_ros/src/odrive_ros_digging_dumping/odrive_interface.py
default_logger = logging.getLogger(__name__)
default_logger.setLevel(logging.DEBUG)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

default_logger.addHandler(ch)

# motor info: https://docs.google.com/spreadsheets/d/12vzz7XVEK6YNIOqH0jAz51F5VUpc-lJEs3mmkWP1H4Y/edit#gid=0
# encoder info: https://docs.google.com/spreadsheets/d/1OBDwYrBb5zUPZLrhL98ezZbg94tUsZcdTuwiVNgVqpU
class ODriveSerialInterface:
    '''
    Params:
    https://docs.odriverobotics.com/#start-odrivetool

    Motor: odrv0.axis{n}.motor.config.{}
    current_lim
    vel_lim
    brake_resistance
    pole_pairs
    torque_constant: torque per amp or 8.27 / kv
    motor_type: MOTOR_TYPE_HIGH_CURRENT or MOTOR_TYPE_GIMBAL

    Encoder: odrv0.axis0{n).encoder.config.{}
    cpr: Count per revolution (should be found on datasheet)

    Move Modes: axis.controller.config.input_mode
    INPUT_MODE_TRAP_TRAJ - use a trapeziodal trajectory with pre-set max vel and acc
        congifs: <odrv>.<axis>.trap_traj.config.
        vel_limit
        accel_limit
        decel_limit
    INPUT_MODE_POS_FILTER
    '''
    def __init__(self, *ports):
        self.logger = default_logger

    def connect(self, port):
        for retry in range(4):
            try:
                self.port = serial.Serial(port)
            except SerialException as e:
                if e.errno == 16:  # [Errno 16] Device or resource busy
                    self.logger.debug("Busy. Retrying in 5s...")
                else:
                    raise
            if self.port:
                break
            time.sleep(5)
        if not self.port:
            self.logger.debug("Failed to connect to ODrive. Exiting.")
        self.port.timeout = 0.5

    def setup(self):
        self.port.write('r vbus_voltage\n')
        voltage = self.port.read(100).strip()
        voltage = voltage if voltage else "unknown"
        self.logger.debug("Vbus: %s" % voltage)

        self.port.write('r vbus_voltage\n')
        voltage = self.port.read(100).strip()
        voltage = voltage if voltage else "unknown"
        self.logger.debug("Vbus: %s" % voltage)

        self.logger.debug("Calibrating left motor... (20 seconds)")
        self.port.write('w axis1.requested_state 3\n')
        time.sleep(20)

        self.logger.debug("Calibrating right motor... (20 seconds)")
        self.port.write('w axis0.requested_state 3\n')
        time.sleep(20)

    def engage(self):
        if not self.port:
            self.logger.error("Not connected.")
            return

        self.logger.debug("Setting drive mode...")
        self.port.write('w axis0.requested_state 8\n')
        time.sleep(0.01)
        self.port.write('w axis1.requested_state 8\n')
        time.sleep(0.01)

        self.port.write('w axis0.controller.config.control_mode 2\n')
        time.sleep(0.01)
        self.port.write('w axis1.controller.config.control_mode 2\n')
        time.sleep(0.01)

        self.port.write('w axis0.controller.vel_setpoint 0\n')
        time.sleep(0.01)
        self.port.write('w axis1.controller.vel_setpoint 0\n')
        time.sleep(0.01)

    def release(self):
        self.logger.debug("Releasing.")
        self.port.write('w axis0.requested_state %d\n' % AXIS_STATE_IDLE)
        time.sleep(0.01)
        self.port.write('w axis1.requested_state %d\n' % AXIS_STATE_IDLE)
        time.sleep(0.01)

    def drive(self, left_motor_val, right_motor_val):
        if not self.port:
            self.logger.error("Not connected.")
            return

        self.port.write('w axis0.controller.vel_setpoint %d\n' % right_motor_val)
        time.sleep(0.01)
        self.port.write('w axis1.controller.vel_setpoint %d\n' % left_motor_val)
        time.sleep(0.01)


class ODriveInterfaceAPI(object):
    driver = None
    encoder_cpr = 4096
    right_axis = None
    left_axis = None
    connected = False

    def __init__(self, logger=None):
        self.logger = logger if logger else default_logger

    def __del__(self):
        self.disconnect()

    def connect(self, port=None, right_axis=0):
        if self.driver:
            self.logger.info("Already connected. Disconnecting and reconnecting.")

        try:  # todo change the configs here
            self.driver = odrive.find_any(path="usb", serial_number="206430804648", search_cancellation_token=None,
                                          channel_termination_token=None, timeout=30, logger=self.logger)
            # 206430804648
            self.axes = (self.driver.axis0, self.driver.axis1)

        except:
            self.logger.error("No ODrive found. Is device powered? Is the Serial Number Correct?")
            return False

        # save some parameters for easy access
        self.right_axis = self.driver.axis0 if right_axis == 0 else self.driver.axis1
        self.left_axis = self.driver.axis1 if right_axis == 0 else self.driver.axis0
        self.encoder_cpr = self.driver.axis0.encoder.config.cpr

        self.connected = True
        return True

    def disconnect(self):
        self.connected = False
        self.right_axis = None
        self.left_axis = None

        if not self.driver:
            self.logger.error("Not connected.")
            return False

        temp_driver = self.driver
        self.driver = None
        try:
            temp_driver.release()
        except:
            return False
        return True

    def calibrate(self):
        if not self.driver:
            self.logger.error("Not connected.")
            return False

        self.logger.info("Vbus %.2fV" % self.driver.vbus_voltage)

        for i, axis in enumerate(self.axes):
            self.logger.info("Calibrating axis %d..." % i)
            # axis.requested_state = AXIS_STATE_FULL_CALIBRATION_SEQUENCE
            axis.motor.config.pre_calibrated = True
            axis.encoder.config.pre_calibrated = True

            # while axis.current_state != AXIS_STATE_IDLE:
            # time.sleep(0.1)
            if axis.error != 0:
                self.logger.error(
                    "Failed calibration with axis error 0x%x, motor error 0x%x" % (axis.error, axis.motor.error))
                return False

        return True

    def preroll(self):
        if not self.driver:
            self.logger.error("Not connected.")
            return False

        self.logger.info("Vbus %.2fV" % self.driver.vbus_voltage)

        for i, axis in enumerate(self.axes):
            self.logger.info("Index search preroll axis %d..." % i)
            axis.requested_state = AXIS_STATE_ENCODER_INDEX_SEARCH

        for i, axis in enumerate(self.axes):
            while axis.current_state != AXIS_STATE_IDLE:
                time.sleep(0.1)

        for i, axis in enumerate(self.axes):
            if axis.error != 0:
                self.logger.error(
                    "Failed preroll with axis error 0x%x, motor error 0x%x" % (axis.error, axis.motor.error))
                return False

        return True

    def engage(self):
        if not self.driver:
            self.logger.error("Not connected.")
            return False

        self.logger.debug("Setting drive mode.")
        for axis in self.axes:
            axis.controller.vel_setpoint = 0
            axis.requested_state = AXIS_STATE_CLOSED_LOOP_CONTROL
            axis.controller.config.control_mode = CTRL_MODE_VELOCITY_CONTROL

        return True

    def release(self):
        if not self.driver:
            self.logger.error("Not connected.")
            return
        self.logger.debug("Releasing.")
        for axis in self.axes:
            axis.requested_state = AXIS_STATE_IDLE

    def drive(self, left_motor_val, right_motor_val):
        if not self.driver:
            self.logger.error("Not connected.")
            return
        for axis in self.axes:
            print("setpoint " + str(axis.motor.current_control.Iq_setpoint))
            print("current measured " + str(axis.motor.current_control.Iq_measured))
            print("Torque " + str(8.27 * (axis.motor.current_control.Iq_measured / 250)))

        if (left_motor_val == 0 and right_motor_val == 0):
            self.left_axis.controller.vel_setpoint = 0
            self.right_axis.controller.vel_setpoint = 0

        print("left_motor_val " + str(left_motor_val))
        print("right_motor_val " + str(right_motor_val))
        self.left_axis.controller.vel_setpoint = left_motor_val
        self.right_axis.controller.vel_setpoint = right_motor_val
        
"""