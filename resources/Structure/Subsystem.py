from resources import configs


class Subsystem:
    '''
    A class that is called periodically by the main robot
    You should inherit this and then overwrite periodic
    '''
    def __init__(self):
        configs.main_robot._substems.append(self)

    def periodic(self):
        pass

