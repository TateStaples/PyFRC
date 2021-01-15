from resources.Communications.Messenger import Messenger
import resources.configs
from threading import Thread


class Robot:
    _auto = False
    _teleop = False
    _running = True
    _subsystems = []

    def __init__(self):
        self._client = Messenger()  # establish wifi connection
        self._setup_listeners()  # allow user to send commands
        self.robot_init()  # call overwrittable function
        resources.configs.main_robot = self

    # setup listeners for when to trigger events
    def _setup_listeners(self):
        self._client.on_receive("enable", self._begin)
        self._client.on_receive("disable", self._stop)
        self._client.on_receive("auto", self._begin_auto)
        self._client.on_receive("teleop", self._begin_teleop)

    # main loop threads
    def _loops(self):
        while self._running:
            self.robot_periodic()
            if self._auto: self.auto_periodic()
            elif self._teleop: self.telop_periodic()

    def _subsystems(self):
        while self._running:
            for subsystem in self._subsystems:
                subsystem.periodic()

    # enable / disable robot
    def _begin(self):
        self._running = True
        self.on_enable()
        Thread(target=self._loops).start()
        Thread(target=self._subsystems).start()


    def _stop(self):
        self._running = False
        self.on_disable()

    # init and run loop for auto/teleop
    def _begin_auto(self):
        self._auto = True
        self.auto_init()
        self._teleop = False

    def _begin_teleop(self):
        self._auto = False
        self._teleop = True
        self._begin_teleop()

    # --- overwritten functions ---
    def robot_init(self):
        pass

    def robot_periodic(self):
        pass

    def on_enable(self):
        pass

    def on_disable(self):
        pass

    def teleop_init(self):
        pass

    def telop_periodic(self):
        pass

    def auto_init(self):
        pass

    def auto_periodic(self):
        pass