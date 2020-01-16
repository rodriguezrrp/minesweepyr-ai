from typing import List

class InteractionBase (object):

    def calibration(self) -> None:
        return

    def get_grid(self) -> List[List[str]]:
        raise NotImplementedError

    def click(self, x, y) -> None:
        raise NotImplementedError

    def mark(self, x, y) -> None:
        raise NotImplementedError

    def findout(self, x, y) -> str:
        raise NotImplementedError

    def cleanup(self) -> None:
        return