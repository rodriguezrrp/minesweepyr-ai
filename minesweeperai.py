## code by rodriguezrrp on GitHub
## MIT license

from random import choice, shuffle

##from sys import stderr as sys_stderr



class AIException(Exception):
    pass
class AIStalledException(AIException):
    pass
class AIExplodedException(AIException):
    pass
class AIAnalyzeException(AIException):
    pass


## =============================================================== ##


_ARG_NEEDS_STR_MSG = "Argument with value of '{0}' was expected to be a string; found {1}"

NUMBERS    = ('1','2','3','4','5','6','7','8')
FLAG       = 'F'
UNKNOWN    = '-'
EXPLODED   = 'B'
NEEDSFOUND = '?' # for things that need found out, but at least are not 'unknown' ('-')

def tileisnumber(tile):
    if type(tile) != str:
        raise TypeError(_ARG_NEEDS_STR_MSG.format(tile, type(tile)))
    return tile in NUMBERS
def tileisflag(tile):
    if type(tile) != str:
        raise TypeError(_ARG_NEEDS_STR_MSG.format(tile, type(tile)))
    return tile == FLAG
def tileisunknown(tile):
    if type(tile) != str:
        raise TypeError(_ARG_NEEDS_STR_MSG.format(tile, type(tile)))
    return tile == UNKNOWN
def tileisexploded(tile):
    if type(tile) != str:
        raise TypeError(_ARG_NEEDS_STR_MSG.format(tile, type(tile)))
    return tile == EXPLODED
def tiletilenum(tile):
    if type(tile) != str:
        raise TypeError(_ARG_NEEDS_STR_MSG.format(tile, type(tile)))
    return int(tile) if tileisnumber(tile) else None
def tileneedsfound(tile):
    if type(tile) != str:
        raise TypeError(_ARG_NEEDS_STR_MSG.format(tile, type(tile)))
    return tile == NEEDSFOUND


## =============================================================== ##


class Tile:

    ##-- 'static' methods & stuff

    ##-- 'instance' methods & stuff

    ## values:
    # self.tile - a character from rawgrid
    # self.x - column index within rawgrid
    # self.y - row index within rawgrid
    # self.coords - tuple of (x, y)
    # self.isnumber
    # self.isflag
    # self.isunknown
    # self.isexploded
    # self.unknowns - set of neighboring tiles which are unknowns
    # self.flags - set of neighboring tiles which are flags
    # self.neighbors - set of all (8) neighboring tiles

    def isnumber(self):
        return tileisnumber(self.tile)
    def isflag(self):
        return tileisflag(self.tile)
    def isunknown(self):
        return tileisunknown(self.tile)
    def isexploded(self):
        return tileisexploded(self.tile)
    def tilenum(self):
        return tiletilenum(self.tile)
    def needsfound(self):
        return tileneedsfound(self.tile)

    def setTile(self, tile):
        self.tile = tile

    
    def __init__(self, rawgrid, x, y):
        self.x = x
        self.y = y
        self.coords = (x, y)
        self.updateSelf(rawgrid)

    def updateSelf(self, rawgrid):
        self.tile = rawgrid[self.y][self.x]
        self.isnumber = Tile.isnumber(self.tile)
        self.isflag = Tile.isnumber(self.tile)
        self.isunknown = Tile.isnumber(self.tile)
        self.isexploded = Tile.isnumber(self.tile)

    def updateArounds(self, tilegrid):      
        x = self.x; y = self.y
        dyrange = range( -1 if y > 0 else 0,  2 if y < len(tilegrid)-1 else 1 )
        dxrange = range( -1 if x > 0 else 0,  2 if x < len(tilegrid[0])-1 else 1 )
        neighbors = []
        # if self's a number, update its arounds
        if self.isnumber():
            unknowns = []
            flags = []
            for dy in dyrange:
                for dx in dxrange:
                    # if not center, analyze it
                    if not (dy==0 and dx==0):
                        dtile = tilegrid[y+dy][x+dx]
                        neighbors.append(dtile) # count as neighbor
                        if dtile.isunknown():
                            unknowns.append(dtile)
                        if dtile.isflag():
                            flags.append(dtile)
##            self.neighbors = set(neighbors) taken care of below
            self.unknowns = set(unknowns)
            self.flags = set(flags)
        # if not a number, still get its neighbors
        else:
            for dy in dyrange:
                for dx in dxrange:
                    # if not center, count it as neighbor
                    if not (dy==0 and dx==0):
                        dtile = tilegrid[y+dy][x+dx]
                        neighbors.append(dtile) # count as neighbor
        self.neighbors = set(neighbors)


    # def settracked(self, tracked, track=True):
    #     if       track and self not in tracked:
    #         tracked.append(self)
    #     elif not track and self     in tracked:
    #         tracked.remove(self)


## =============================================================== ##


class TileGroup:

    def __init__(self, initialset, expected):
        self.tileset = initialset # the set of the tiles in this group
        self.size = len(initialset) # the size of the tile set
        self.expected = expected # num of expected bombs in this group
        self.chance = expected / size

    def resolve(group):
        '''attempt to resolve against another group'''
        # TODO will return None if no changes to make; else,
        # return a list of groups to put in place of this & clashing group

    def __eq__(other):
        if isinstance(other, TileGroup):
            return self.tileset equals other.tileset ## TODO find proper equals comparison
        return False


## =============================================================== ##


class Island:
    '''Defines a region of the minesweeper grid;
    used to conceptually divide it into separate areas
    ("islands" in the "sea" of blank (clicked) tiles) which can
    be individually iterated through. Hopefully helps to avoid
    the cases where guessing is left to the last minute, wasting time'''

    def __init__(self, ):

    def addGroup(self, tilegroup):

    def tryToSplit(self):



## =============================================================== ##


class AI:

    ## options:
    # self.verbose          - verbose
    # self.chord            - chord
    # self.totalbombs       - totalBombsCount
    # self.maxpasses        - maxPassesPerIter

    ## other values:
    # self.tofindout
    # self.toclick
    # self.tomark
    #

    def __init__(self, rawgrid,
                 verbose=True, chord=True,
                 totalBombsCount=None,
                 maxPassesPerIter=10):
        # validation stuff
        if maxPassesPerIter < 1:
            raise ValueError('maxPassesPerIteration must be at least 1!')
        if totalBombsCount!=None and ( type(totalBombsCount)!=int or totalBombsCount<1 ):
            raise ValueError('totalBombsCount must be either None or a positive integer!')
        # config stuff
        self.verbose = verbose
        self.chord = chord
        self.totalbombs = totalBombsCount
        self.maxpasses = maxPassesPerIter

        self.parseGrid(rawgrid)

    
    def parseGrid(self, rawgrid):
        '''resets all the data of self that is tracked and related to a rawgrid'''
        if self.verbose:
            print(' parsing rawgrid')
        # grid stuff
        self.height = len(rawgrid)
        if self.height < 1:
            raise ValueError('rawgrid has no height (rows)!')
        self.width = len(rawgrid[0])
        if self.width < 1:
            raise ValueError('rawgrid has no width (columns)!')
        
        # init self stuff
        self.tiles = []
        yrange = range(0, self.height)
        xrange = range(0, self.width)
        reqxlen = len(xrange)
        for y in yrange:
            # perform jagged array check one row ahead to ensure Tile() init won't fail
            if y < self.height-1 and len(rawgrid[y+1]) != reqxlen:
                   raise ValueError('rawgrid is a jagged array! Must be an even rectangle!'
                                    +' row {0} had length of {1}; expected {2}'
                                    .format(y+1, len(rawgrid[y+1]), reqxlen))
            trow = []
            for x in xrange:
                trow.append(Tile(rawgrid, x, y))
            self.tiles.append(trow)

        # update all tiles in tile grid, and group them
        if self.verbose:
            print('  updating and grouping tile objects')
        self.tilegroups = []
        self.flags = set()
        for row in self.tiles:
            for tile in row:
                tile.updateArounds(self.tiles)
                self.tilegroups.append(sefesf)
                # if tile.isnumber():
                #    tile.settracked(self.tracked, True)
                if tile.isflag():
                    self.flags.add(tile.coords)

        



## =============================================================== ##
#####################################################################
#####################################################################
#####################################################################
#####################################################################

