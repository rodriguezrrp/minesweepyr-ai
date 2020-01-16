from typing import List, Iterable, Tuple, Set
import time

import labeling
from printer import inc_prtlvl, dec_prtlvl, set_prtlvl, debug, info, warn, error
from interactions.base import InteractionBase
from ai import AI

class Driver:

    def __init__(self, interact: InteractionBase):
        self.interact = interact #type: InteractionBase
        interact.calibration()
        grid: List[List[str]] = interact.get_grid()
        self.ai = AI(grid, chordpolicy=True)
        self.toclick = set() #type: Set[Tuple[int,int]]
        self.tomark = set() #type: Set[Tuple[int,int]]
        self.tofindout = set() #type: Set[Tuple[int,int]]
        self.foundout = set() #type: Set[Tuple[Tuple[int,int],str]]

    def play(self) -> None:
        while(True):
            set_prtlvl(0)
            info()
            info()
            info('sleeping before iteration...')
            time.sleep(2)
            info('iterating!')
            inc_prtlvl()
            # iterate ai, and get back the new actions
            _res = self.ai.iterate(self.foundout)
            self.toclick, self.tomark, self.tofindout = _res
            dec_prtlvl()
            # perform the new actions
            self._perform_self_actions()

    def _perform_self_actions(self) -> None:
        self.foundout = set()
        info('performing marking, clicking, and finding actions...')
        inc_prtlvl()
        # mark all in tomark
        info('marking all ({})...'.format(len(self.tomark)))
        for x, y in self.tomark:
            debug(inc=True, dec=True, msg='marking ({},{})'.format(x,y))
            self.interact.mark(x, y)
        # click all in toclick
        info('clicking all ({})...'.format(len(self.toclick)))
        for x, y in self.toclick:
            debug(inc=True, dec=True, msg='clicking ({},{})'.format(x,y))
            self.interact.click(x, y)
        # find out all
        info('finding out all ({})...'.format(len(self.tofindout)))
        for x, y in self.tofindout:
            debug(inc=True, dec=True, msg='finding ({},{})'.format(x,y), end='')
            tile = self.interact.findout(x, y) #type: str
            debug(prtlvl=0, msg=' as "{}"'.format(tile))
            # if it is empty, then you must enqueue its neighbors for chain reaction
            if labeling.is_empty(tile):
                self.tofindout.add((x, y))
            # if it's a bomb... wee woo!
            if labeling.is_exploded(tile):
                raise RuntimeError('WEE WOO WEE WOO! Exploded bomb found at ({}, {})!'.format(x, y))
            # add it as found-out
            self.foundout.add( ((x,y),tile) )
        info('done performing actions!')
        dec_prtlvl()

    def cleanup(self):
        self.interact.cleanup()
        del self.ai
        del self.interact