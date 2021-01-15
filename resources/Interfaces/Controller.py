from resources.configs import main_robot


class Button:
    '''
    A boolean wrapper class that can hold a bool or bool function
    Includes listener for press / release
    '''
    def __init__(self, val=False):
        self.value = val
        self._click = []
        self._release = []

    def _get(self):
        return self.value if type(self.value) == bool else self.value()  # allow button to be a getter function

    def on_click(self, func):
        self._click.append(func)

    def on_release(self, func):
        self._release.append(func)

    def __setattr__(self, key, value):
        if key == "value" and type(value) == bool:
            previous = self._get()
            toggle = value != previous
            if toggle:
                l = self._click if value else self._release
                for func in l:
                    func()
        super(Button, self).__setattr__(key, value)

    def __bool__(self):
        return self._get()


class Axis:
    '''
    A float wrapper that can apply control configs to allow for more sensitive controls
    '''
    def __init__(self, val=0.0):
        self.rate = 1
        self.expo = 0
        self.super_rate = 0
        self.dead_band = 0
        self.value = val

    def _get(self):  # this is fancy control thing i copied from kyber
        command = self.value() if callable(self.value) else self.value

        if command > self.dead_band:
            command = (1 / (1 - self.dead_band)) * command - (self.dead_band / (1 - self.dead_band))
        elif command < -self.dead_band:
            command = (1 / (1 - self.dead_band)) * command - (self.dead_band / (1 - self.dead_band))
        else: return 0
        retval = (1 + 0.01 * self.expo * (command * command - 1.0)) * command
        retval = (retval * (self.rate + (abs(retval) * self.rate * self.superRate * 0.01)))
        return retval

    def __float__(self):
        return self._get()


class Controller:
    '''
    Abstract class for any type of controller using Axes and Buttons
    '''
    def __init__(self, number):
        self.name = "Controller" + number
        main_robot.messenger.on_receive(self.name, )

    def _update(self, new_vals):  # passes a dictionary
        for input in new_vals:
            self.inputs[input].value = new_vals[input]

    def __setattr__(self, key, value):
        t = type(value)
        if t == Button or t == Axis:
            self.inputs[key] = value
        super(Controller, self).__setattr__(key, value)


class XboxController(Controller):
    '''
    Controller that is setup with Xbox buttons and axes
    '''
    def __init__(self, number):
        super(XboxController, self).__init__(number)
        buttons = ['a', 'x', 'y', 'b',
                   'rightBumper', 'leftBumper', 'leftStickButton', 'rightStickButton',
                   'guide', 'back', 'start'
                   'up', 'down', 'left', 'right'
        ]
        axes = [
            "leftX", "leftY", "rightX", "rightY",
            "leftTrigger", "rightTrigger"
        ]
        for b in buttons:
            self.__setattr__(b, Button())
        for a in axes:
            self.__setattr__(a, Axis())