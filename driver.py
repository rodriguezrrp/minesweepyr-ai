from interactionbase import InteractionBase

class Driver:

    def __init__(self, interact: InteractionBase):
        self.interact = interact #type: InteractionBase
        interact.calibration()