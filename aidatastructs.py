import traceback
from typing import Dict, Tuple, Set, Union, List, Any, Optional, Iterable
import itertools

from printer import inc_prtlvl, dec_prtlvl, debug, info, warn, error

## aidatastructs provides the underlying data structures that the ai uses

def positions_around(x: int, y: int, maxx: Optional[int], maxy: Optional[int],
                    radius: int=1, minx: Optional[int]=0, miny: Optional[int]=0):
    radius=abs(radius)
    lx = x-radius   if minx is None else max(x-radius,  minx)
    hx = x+radius+1 if maxx is None else min(x+radius+1,maxx)
    ly = y-radius   if miny is None else max(y-radius,  miny)
    hy = y+radius+1 if maxy is None else min(y+radius+1,maxy)
    _xrange = range(lx,hx)
    _yrange = range(ly,hy)
    return itertools.product(_xrange,_yrange)

#############################
## TileIsland
# serves as a graphlike structure of the 2d-mapped groups inside it
#   (each group's "children" are all the groups whose unknowns intersect with it)
#
#TODO: a static method for creating TileIsland objects (which takes in a generator object?)
#TODO: a self method for removing pairs? NEEDS TO HAVE GOOD ISLAND-BREAKUP DETECTION...

class TileIsland (object):

    ## static methods

    # may MUTATE the islands parameter, when inserting newgroup into islands or none at all:
    #   if insertion is successful:
    #           this method will merge any other successful islands; and
    #           will remove those islands from the islands parameter (MUTATING the parameter!)
    #   and if insertion was not successful:
    #           this method will add the new island to the islands parameter (MUTATING the parameter!)
    @staticmethod
    def insertInto(islands: List['TileIsland'], newgroup: 'TileGroup') -> None:
        firstsuccess: Optional['TileIsland'] = None
        toremove = []
        for island in islands:
            # will be true if successful (if it found a group that intersects)
            if(island.try_to_insert(newgroup, require_intersection=True)):
                if not firstsuccess:
                    firstsuccess = island
                else: # if we've found another island that also accepts it, those islands could be merged
                    firstsuccess.merge_incoming_island(island)
                    toremove.append(island)
        for island in toremove:
            islands.remove(island) # MUTATING the parameter! Removing all islands which were merged with it
        if(firstsuccess == None):
            inc_prtlvl()
            debug('previous insertion into islands list failed; creating a new island and adding it to list')
            dec_prtlvl()
            newisland = TileIsland(groups=[newgroup])
            # print("newisland = " + str(newisland))
            print("newisland groups: " + str(list(newisland.get_groups()))) #TODO remove these two print()s, they're just debugging
            islands.append(newisland)

    ## non-static methods

    def __init__(self, groups=None):
        if(groups == None):
            groups = []
        # elif(type(groups) in {list, set, tuple}):
        #     pass
        else:
            groups = [g for g in groups] # clone the list, just in case
        # self.groups_list: List[TileGroup] = []
        self.groups_map: List[List[Optional[TileGroup]]] = []
        self.groups_x_offset: int = 0
        self.groups_y_offset: int = 0
        # self.groups_map_width: int = 0 <- removed because jaggedness is not supported after all
        # self.groups_map_height: int = 0
        
        # self
        # for g in groups[1:]:
        #     self._put_group()
        for g in groups:
            print('trying to insert group {}...'.format(g))
            self.try_to_insert(g, require_intersection=False)
            print("this island's group list: " + str(list(self.get_groups())))
    

    def _ensure_room_for_group(self, absx, absy):
        # group must be allowed +/-1 in x and y directions, for its neighbors
        if(self.groups_map == None or len(self.groups_map) == 0):
            self.groups_map = [[None for _x in range(3)] for _y in range(3)]
            self.groups_x_offset = absx-1
            self.groups_y_offset = absy-1
        else:
            relx, rely = self._scaled_pos(absx, absy)
            if (relx > len(self.groups_map[0])): # expand right
                dist = len(self.groups_map[0])-relx+1 # distance to expand
                for i in range(len(self.groups_map)):
                    self.groups_map[i] = self.groups_map[i] + [None] * dist # append to right
            elif (relx < 0): # expand left
                dist = len(self.groups_map[0])-relx+1 # distance to expand
                for i in range(len(self.groups_map)):
                    self.groups_map[i] = [None] * dist + self.groups_map[i] # prepend to left
            if (rely > len(self.groups_map)): # expand down
                dist = len(self.groups_map)-rely+1 # distance to expand
                widthOfRow = len(self.groups_map[0])
                for _ in range(dist):
                    self.groups_map = self.groups_map + [None for _ in range(width)] # append to bottom
            elif (rely < 0): # expand up
                dist = 0-rely+1 # distance to expand
                widthOfRow = len(self.groups_map[0])
                for _ in range(dist):
                    self.groups_map = [None for _ in range(width)] + self.groups_map # prepend to top

    # # returns adjusted coordinates based on the self.groups_map's offsets, for retrieving internally
    # def _scaled_pos(self, absx: int, absy: int) -> Tuple[int, int]:
    #     relx = absx-self.groups_x_offset
    #     rely = absy-self.groups_y_offset
    #     # if not self.groups_map: raise RuntimeError("self.groups_map was None while attempting to call _scaled_pos")
    #     if( (0<=rely and rely<len(self.groups_map)) ):
    #         if( (0<=relx and relx<len(self.groups_map[rely])) ):
    #             return relx, rely
    #         else:
    #             raise ValueError("relative x is not within self.groups_map[rely]'s length! relx: {}, absx: {}, self.groups_x_offset: {}, rely: {}"
    #                         .format(relx, absx, self.groups_x_offset, rely))
    #     else:
    #         raise ValueError("relative y is not within self.groups_map's length! rely: {}, absy: {}, self.groups_y_offset: {}"
    #                     .format(rely, absy, self.groups_y_offset))
    # def _checked_scaled_pos(self, absx: int, absy: int) -> Union[Tuple[int,int], Tuple[None,None]]:
    #     try:
    #         return self._scaled_pos(absx, absy)
    #     except ValueError:
    #         traceback.print_exc() # catch the exception and print it, but just return None pair
    #         return None,None

    # returns adjusted coordinates based on the self.groups_map's offsets, for retrieving internally
    def _scaled_pos(self, absx: int, absy: int) -> Tuple[int, int]:
        relx = absx-self.groups_x_offset
        rely = absy-self.groups_y_offset
        return relx, rely
    def _bounded_scaled_pos(self, absx: int, absy: int) -> Tuple[Optional[int], Optional[int]]:
        relx, rely = self._scaled_pos(absx, absy) #type: Tuple[Any,Any]
        if( not (0<=rely and rely<len(self.groups_map)) ):
            rely = None
        if( not (0<=relx and len(self.groups_map)>0 and relx<len(self.groups_map[0])) ):
            relx = None
        return relx, rely

    # could return None, if there's no group at those positions
    def get_group(self, absx: int, absy: int) -> Optional['TileGroup']:
        relx, rely = self._bounded_scaled_pos(absx, absy)
        if(relx is None or rely is None): return None
        return self.groups_map[rely][relx]
    
    # returns an iterator which goes through self.groups_map and yields all which are not none
    def get_groups(self):
        return itertools.filterfalse(
                lambda x: x==None,
                itertools.chain.from_iterable(self.groups_map))

    # returns true if merge was successful; returns false if merge could not happen (the newgroup was completely disconnected from this island)
    #   MODIFIES newgroup's myisland and islandneighbors, but ONLY IF insertion was successful (at least one group intersected with newgroup)
    def try_to_insert(self, newgroup: 'TileGroup', require_intersection: bool=True) -> bool:
        gx, gy = newgroup.centerpos
        # self._ensure_room_for_group(gx, gy)
        if self.get_group(gx, gy) is not None: #NOTE: is this assertion necessary, or should it just overwrite anyway?
            raise ValueError("trying to insert newgroup, but a group already existed at centerpos ({}, {})!".format(gx, gy))
        print('        [try_to_insert] require_intersection={}'.format(require_intersection))
        # for group in self.groups_list:
        found_connection = False # used to help track when to set newgroup.myisland
        for pos in positions_around(gx, gy, maxx=None, maxy=None, radius=1, minx=None, miny=None): # only check the ones that would be next to it - its potential neighbors
            x, y = pos
            group = self.get_group(x, y)
            print('          group at ({}, {}) is {}'.format(x, y, group))
            if require_intersection and not group: continue # if there was no group at those coords, then try the next
            # see if the group intersects with newgroup
            ignore_intersection = not require_intersection
            if(ignore_intersection or group.intersects_with(newgroup)):  #type: ignore
                if(not found_connection):
                    self._ensure_room_for_group(gx, gy)
                    found_connection = True
                    newgroup.myisland = self  # declare self as newgroup's new island
                    newgroup.islandneighbors.clear()  # reset newgroup's neighbors
                    relgx, relgy = self._scaled_pos(gx, gy)
                    self.groups_map[relgy][relgx] = newgroup
                if group: # if this wasn't done via ignore_intersection, then pair the intersecting group
                    TileGroup._connect_groups(newgroup, group)  # pair them up as neighbors
        return found_connection

    # def force_insert(self, newgroup: 'TileGroup') -> bool:

    # def reassess_neighbors(self, oldgroup: TileGroup):
    #     if()

    # Merges the incomingisland into self. Does not modify incomingisland. Modifies self.
    def merge_incoming_island(self, incomingisland: 'TileIsland'):
        info('trying to merge incoming island...')
        for newgroup in incomingisland.get_groups():
            self.try_to_insert(newgroup, require_intersection=False)

    def remove_group(self, group: 'TileGroup'):
        if(group.myisland is not self): raise ValueError("trying to remove group from self, but group.myisland was not self!")
        TileGroup._disconnect_all_neighbors(group)
        group.myisland = None

    # turns this object into a displayable matrix
    def __str__(self):
        strout = '\n'.join(' '.join(' ' if x==None else str(x) for x in row) for row in self.groups_map)
        # strout = ""
        # for row in range():
        #     strout += ' '.join([' ' if x==None else str(x) for x in row])
        #     for col in range():
        #         strout += '  ' if col==None else '{} '
        #     strout += '\n'
        return strout



#############################
## ChordContext
# for the TileGroup, when specifying a potential chording's effect; used for removing redundant chording
#

class ChordContext (object):

    ## static methods

    @staticmethod
    def to_pos_list(mixedelems: Iterable[Union[Tuple[int, int], 'ChordContext']]) -> List[Tuple[int, int]]:
        contexts: List[ChordContext] =       [] #list(e for e in mixedelems if isinstance(e, ChordContext))
        noncontexts: List[Tuple[int, int]] = [] #list(e for e in mixedelems if not isinstance(e, ChordContext))
        for e in mixedelems:
            if isinstance(e, ChordContext):
                contexts.append(e)
            else:
                noncontexts.append(e)
        ChordContext.remove_redundants(contexts)
        contextscoords: List[Tuple[int, int]] = list(e.centerpos for e in contexts)
        return contextscoords + noncontexts

    @staticmethod
    def remove_redundants(contexts: List['ChordContext']) -> None:
        # flatten the x,y coords from all the unknowns sets from all the contexts
        coords = list( itertools.chain.from_iterable((p for p in cxt.unknowns) for cxt in contexts) )
        # Setup the dictionary which tracks which coords are duplicated
        repeats: Dict[Tuple[int,int], bool] = dict()
        for pos in coords:
            if pos not in repeats: # it's a new one; it has no repeat yet, initialize to False
                repeats[pos] = False
            else: # seen before; set repeat to True now
                repeats[pos] = True
        

    ## non-static methods

    def __init__(self, centerpos: Tuple[int, int], unknowns: Set[Tuple[int, int]]):
        self.centerpos = centerpos #type: Tuple[int, int]
        self.unknowns = unknowns #type: Set[Tuple[int, int]]



#############################
## TileGroup
#
# self.centerpos --
# self.unknowns  -- coords of unknowns in this group    (len must be >= self.bombs)
# self.bombs     -- possible bombs in this group    (must be < self.unknowns)
#
# self.chance()  -- impl: self.bombs/len(self.unknowns)    (must be <= 1; but if it's 1, it can be dissolved to all-flags)
# self.attemptdissolve() --

class TileGroup (object):

    ## static methods
    
    @staticmethod
    def _connect_groups(group1: 'TileGroup', group2: 'TileGroup') -> None:
        group1.islandneighbors.add(group2)
        group2.islandneighbors.add(group1)

    @staticmethod
    def _disconnect_groups(group1: 'TileGroup', group2: 'TileGroup') -> None:
        group1.islandneighbors.remove(group2)
        group2.islandneighbors.remove(group1)
    
    @staticmethod
    def _disconnect_all_neighbors(group: 'TileGroup') -> None:
        for neighbor in group.islandneighbors:
            neighbor.islandneighbors.remove(group)
        group.islandneighbors.clear()

    ## non-static methods
    
    def __init__(self, centerpos, unknowns, bombs, myisland=None):
        self.centerpos = centerpos #type: Tuple[int,int]
        self.unknowns = unknowns #type: Set[Tuple[int,int]]
        self.bombs = bombs #type: int
        self.myisland = myisland #type: Optional[TileIsland]
        self.islandneighbors = set() #type: Set[TileGroup]
    

    # def get_myisland(self) -> Optional[TileIsland]:
    #     return self.myisland

    # def set_myisland(self, island: TileIsland):
    #     # if(self.myisland == None): self.myisland = island
    #     # else: raise ValueError("TileGroup's island is already set! Cannot override an existing island association")
    #     self.myisland = island

    # def get_myneighbors(self) -> List[TileGroup]:
    #     return self.islandneighbors

    # def set_myneighbors(self,)

    def chance(self) -> float:
        return self.bombs/len(self.unknowns)


    # def can_dissolve(self) -> None:
    #     raise NotImplementedError()


    # def attempt_dissolve(self):

    # TODO: this needs to happen after all attempt_intersect_resolves, to allow neighbors to get properly updated (partitioned)?
    #       extra NOTE: this may not matter, if dissolving and resolving happen repeatedly...
    def attempt_self_dissolve(self: 'TileGroup', chordpolicy: bool,
            toclick: Set[Union[Tuple[int,int],ChordContext]], tomark: Set[Tuple[int,int]],
            tofindout: Set[Tuple[int, int]]) -> None:
        if not self.myisland: raise RuntimeError("tried to dissolve self in self.myisland, but myisland was not yet set!")
        if self.bombs < 0: raise RuntimeError("self.bombs was less than 0; should never happen!")
        if self.bombs > len(self.unknowns): raise RuntimeError("self.bombs was greater than self.unknowns length; should never happen!")
        # all of self.unknowns are bombs; mark them
        if self.bombs == len(self.unknowns):
            # note that chording doesn't apply in this case
            tomark.update(self.unknowns)
            self.myisland.remove_group(self)
        # all of self.unknowns are guaranteed empty; click them
        elif self.bombs == 0:
            if chordpolicy:  # chord
                toclick.add(ChordContext(self.centerpos, self.unknowns))
            else:  # don't chord
                toclick.update(self.unknowns)
            tofindout.update(self.unknowns)
            self.myisland.remove_group(self)

    def resolve_against_neighbors(self: 'TileGroup') -> None:
        for othergroup in self.islandneighbors:
            self.attempt_intersect_resolve(othergroup)

    def attempt_intersect_resolve(self: 'TileGroup', othergroup: 'TileGroup') -> None:
        # input validation...
        if(self is othergroup): return #TODO maybe output debug msg, for self being other?
        if not self.myisland: raise RuntimeError("tried to resolve self with othergroup, but self.myisland was not yet set!")
        if not othergroup.myisland: raise RuntimeError("tried to resolve self with othergroup, but othergroup.myisland was not yet set!")
        if self.myisland is not othergroup.myisland: raise ValueError("tried to resolve self with othergroup, but self.myisland != othergroup.myisland!")
        if (self.unknowns == othergroup.unknowns): # both self and other encompass the same unknowns
            if(self.bombs != othergroup.bombs): raise ValueError(
                    "tried to resolve self with othergroup, but othergroup had same unknowns ({}), but different bomb counts! (self: {}, other: {})"
                    .format(self.unknowns, self.bombs, othergroup.bombs))
            othergroup.myisland.remove_group(othergroup)
            return #FIXME output debug msg, for self being an unexpected duplicate of othergroup <- NOTE: what if centerpos is different?
        # attempt the intersection
        intersection = self.unknowns.intersection(othergroup.unknowns)
        # if intersection is equivalent to self's unknowns, then self is subset of other;
        #   self is untouched and othergroup gets compartmentalized (MODIFIES: other)
        if intersection == self.unknowns:
            othergroup.unknowns.difference_update(self.unknowns) # partition away self's elements
            othergroup.bombs -= self.bombs # partition away self's bombs (this could leave othergroup with 0 bombs)
        # if intersection is equivalent to othergroup's unknowns, then other is subset of self;
        #   othergroup is untouched and self gets compartmentalized (MODIFIES: self)
        elif intersection == othergroup.unknowns:
            self.unknowns.difference_update(othergroup.unknowns) # partition away other's elements
            self.bombs -= othergroup.bombs # partition away other's bombs (this could leave self with 0 bombs)
        #TODO more cases...?

    # def intersects_with_group(self, othergroup: TileGroup) -> bool:
    #     return

    def intersects_with(self, othergroup: 'TileGroup') -> bool:
        intersection = self.unknowns.intersection(othergroup.unknowns)
        return len(intersection) > 0

    def __str__(self) -> str:
        return 'TileGroup(centerpos={},unknowns={},bombs={})'.format(self.centerpos,self.unknowns,self.bombs)