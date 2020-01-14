

class InteractionBase (object):

    def calibration(self) -> None:
        return

    def click(self, x, y) -> None:
        raise NotImplementedError

    def mark(self, x, y) -> None:
        raise NotImplementedError

    def findout(self, x, y) -> str:
        raise NotImplementedError