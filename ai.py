from aidatastructs import positions_around, TileIsland, TileGroup, ChordContext
from printer import get_prtlvl as getprt, set_prtlvl as setprt, inc_prtlvl as incprt, dec_prtlvl as decprt, out, debug, info, warn, error
import labeling
from typing import List, Set, Tuple, Union, Iterable
import copy.deepcopy
# inc = incprt # more aliasing
# dec = decprt # more aliasing
_print = print
print = out # override default print


###################################
## AI

class AI (object):

    ## static stuff

    ## non-static stuff

    # self.islands   -- a list of TileIslands comprising the grid
    

    def __init__(self, grid: List[List[str]]):
        #
        self.chordpolicy = True
        #
        # self.grid = copy.deepcopy(grid)
        self._reparse_grid(grid)


    def _reparse_grid(self, grid: List[List[str]]):
        self.grid = copy.deepcopy(grid)
        try:
            debug('AI: parsing grid...'); incprt()
            # from data structs create the tileislands
            self.islands: List[TileIsland] = []
            expectedwidth = len(grid[0])
            for y in range(0,len(grid)):
                rowlen = len(grid[y])
                # verify grid is rectangular row-by-row
                if(rowlen != expectedwidth):
                    raise ValueError("grid must be rectangular, not jagged! width at y={} was {}, expected {}".format(y,rowlen,expectedwidth))
                # for each row's item, if it's a number, make a TileGroup out of it
                for x in range(0,rowlen):
                    self._insert_tilegroup_from_tile(grid, x, y)
            decprt()
        except:
            # TODO: clear all the "dirtied" data?
            # restore the printer indent level, for good measure?
            raise


    def _insert_tilegroup_from_tile(self, grid: List[List[str]], x: int, y: int):
        centerpos = (x,y)
        tile = grid[y][x] # type: str
        if(labeling.is_digit(tile)):
            # make the new group
            newgroup = TileGroup(
                centerpos,
                {p for p in positions_around(x, y, radius=1) if (
                    p != centerpos and labeling.is_unknown(grid[p[1]][p[0]]))},
                labeling.digit_of(tile))
            # add that new group into self.islands if possible, merging if needed, etc.
            TileIsland.insertInto(self.islands, newgroup)


    ## run an iteration, with a specified island
    def _iter_island(self, curisland: TileIsland) -> Tuple[Iterable[Tuple[int,int]],Iterable[Tuple[int,int]],Iterable[Tuple[int,int]]]:
        # get all groups
        groups = list(curisland.get_groups())
        # resolve against neighbors first
        for group in groups:
            group.resolve_against_neighbors() #TODO will this method's implementation cause any dirtying and desyncing of the looping?
        # prepare for dissolving deterministic groups
        dissolvehappened = False
        toclickmixed = set() #type: Set[Union[Tuple[int,int],ChordContext]]
        tomark = set() #type: Set[Tuple[int,int]]
        tofindout = set() #type: Set[Tuple[int,int]]
        for group in groups:
            group.attempt_self_dissolve(self.chordpolicy, toclick=toclickmixed, tomark=tomark, tofindout=tofindout)
        # if something got added to the lists, then a dissolve happened
        dissolvehappened = ( len(toclickmixed) > 0 or len(tomark) > 0 or len(tofindout) > 0 )
        # if none happened, do a guessing strategy
        if not dissolvehappened:
            self._handle_stall(groups, toclick=toclickmixed, tomark=tomark, tofindout=tofindout)
        # handle the toclick, tomark, and tofindout
        #TODO (this is where you convert the toclicks and then return all lists)
        toclick: List[Tuple[int,int]] = ChordContext.to_pos_list(toclickmixed)
        return toclick, tomark, tofindout


    def _handle_stall(self, groups: Iterable[TileGroup], toclick: Set[Union[Tuple[int,int],ChordContext]], tomark: Set[Tuple[int,int]], tofindout: Set[Tuple[int, int]]) -> None:
        # if it's stalled, figure out all unknown tiles equally least likely to be bombs
        candidates = set() #type: Set[Tuple[int,int]]
        candidateschance = 1 #type: float
        for group in groups:
            chance = group.chance()
            if(chance == candidateschance):
                candidates.update(group.unknowns)
            elif(chance < candidateschance):
                candidateschance = chance
                candidates.clear()
                candidates.update(group.unknowns)
        # randomly click one
        if(len(candidates) == 0): raise RuntimeError("Uh oh! No random-click candidates were found! Are we done with this island?") #TODO: would _reparse_grid need to be called following this?
        if(candidateschance == 0): warn(inc=True, dec=True, msg="NOTICE: _handle_stall compiled a list of random-click candidates whose chance was 0;"
                + "_handle_stall's chance should theoretically not reach 0, as that situation would have been dealt with by regular dissolving!")


    def _iter_all_islands(self: AI) -> Tuple[Iterable[Tuple[int,int]],Iterable[Tuple[int,int]],Iterable[Tuple[int,int]]]:
        toclick = set() #type: Set[Tuple[int,int]]
        tomark = set() #type: Set[Tuple[int,int]]
        tofindout = set() #type: Set[Tuple[int,int]]
        for island in self.islands:
            #TODO can an iter_island call mutate self.islands? Probably do a check/assertion before & after just to see?
            _toclick, _tomark, _tofindout = self._iter_island(island)
            toclick.update(_toclick)
            tomark.update(_tomark)
            tofindout.update(_tofindout)
        return toclick, tomark, tofindout
    

    # parameter foundout is a list of pairs of info: each pair has a coordinate and a tile value
    # returns the toclick, tomark, and tofindout
    def iterate(self: AI, foundout: List[Tuple[Tuple[int,int],str]]) -> Tuple[Iterable[Tuple[int,int]],Iterable[Tuple[int,int]],Iterable[Tuple[int,int]]]:
        # update foundouts (FIXME: remember in the driver to chain unknowns from tofindouts, when the empty spaces open up bigly)
        for found in foundout:
            coords, newtile = found
            cx, cy = coords
            debug(inc=True, dec=True, msg='Replacing found tile at {} - from "{}" to "{}"'.format(coords, self.grid[cy][cx], newtile))
            self.grid[cy][cx] = newtile
            self._insert_tilegroup_from_tile(self.grid, cx, cy)
        # iterate through all the islands to find out the toclick, tomark, and tofindout
        return self._iter_all_islands()