from resources import configs


class Subsystem:
    def __init__(self):
        configs.main_robot._substems.append(self)

    def periodic(self):
        pass

