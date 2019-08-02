## code by rodriguezrrp on GitHub
## MIT license

from random import choice as choose, shuffle

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


ARG_NEEDS_STR_MSG = "Argument with value of '{0}' was expected to be a string; found {1}"

NUMBERS    = ('1','2','3','4','5','6','7','8')
FLAG       = 'F'
UNKNOWN    = '-'
EXPLODED   = 'B'
NEEDSFOUND = '?' # for things that need found out, but at least are not 'unknown' ('-')
##EFFECTIVELYUNKNOWN = (UNKNOWN, NEEDSFOUND)

def isnumber(tile):
    if type(tile) != str:
        raise TypeError(ARG_NEEDS_STR_MSG.format(tile, type(tile)))
    return tile in NUMBERS
def isflag(tile):
    if type(tile) != str:
        raise TypeError(ARG_NEEDS_STR_MSG.format(tile, type(tile)))
    return tile == FLAG
def isunknown(tile):
    if type(tile) != str:
        raise TypeError(ARG_NEEDS_STR_MSG.format(tile, type(tile)))
    return tile == UNKNOWN
def isexploded(tile):
    if type(tile) != str:
        raise TypeError(ARG_NEEDS_STR_MSG.format(tile, type(tile)))
    return tile == EXPLODED
def tilenum(tile):
    if type(tile) != str:
        raise TypeError(ARG_NEEDS_STR_MSG.format(tile, type(tile)))
    return int(tile) if isnumber(tile) else None
def needsfound(tile):
    if type(tile) != str:
        raise TypeError(ARG_NEEDS_STR_MSG.format(tile, type(tile)))
    return tile == NEEDSFOUND


## =============================================================== ##


class Tile:

    ##-- 'static' methods & stuff

    ##-- 'instance' methods & stuff

    def isnumber(self):
        return isnumber(self.tile)
    def isflag(self):
        return isflag(self.tile)
    def isunknown(self):
        return isunknown(self.tile)
    def isexploded(self):
        return isexploded(self.tile)
    def tilenum(self):
        return tilenum(self.tile)
    def needsfound(self):
        return needsfound(self.tile)

    def setTile(self, tile):
        self.tile = tile

    def updateSelf(self, rawgrid):
        self.tile = rawgrid[self.y][self.x]
##        self.isnumber = Tile.isnumber(self.tile)
##        self.isflag = Tile.isnumber(self.tile)
##        self.isunknown = Tile.isnumber(self.tile)
##        self.isexploded = Tile.isnumber(self.tile)

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

    
    def __init__(self, rawgrid, x, y):
        self.x = x
        self.y = y
        self.coords = (x, y)
        self.updateSelf(rawgrid)


    def settracked(self, tracked, track=True):
        if       track and self not in tracked:
            tracked.append(self)
        elif not track and self     in tracked:
            tracked.remove(self)


## =============================================================== ##


class AI:

    ##-- 'static' methods & stuff

    defaultunknownchance = 0.17 # rather arbitrary; based off of intermediate to expert

    markingedits = True # if needsmarked can edit the rawgrid (for keeping-up-to-date reasons)

    def reverse(l, rev=True):
        #pylint:disable=no-self-argument,unsubscriptable-object
        '''generator which configurably reverses iteration over list/range/etc.'''
        lr = ( range(len(l)-1,-1,-1) if rev else range(0,len(l)) )
        for i in lr:
            yield l[i]

    ##-- 'instance' methods & stuff

    # NOTE: config variables are:
    # self.verbose              - verbose
    # self.chord                - chord
    # self.totalbombs           - totalBombsCount
    # self.minmouseusage        - minimizeMouseUsage        - sort-of done (?)
    # self.maxpasses            - maxPassesPerIteration
    # self.smartstalledclick    - smartStalledRandomClick
    # self.stalledsubset        - stalledSubsetCheck
    # self.stalledbruteforce    - stalledBruteForceCheck    - TODO
    # self.alternatepass        - alternatePassDirection    - TODO
    # self.mentalflags          - mentallyTrackFlags

    # note that: self.alternatethispass is used in each specific iteration

    # also has:
    # self.tracked   - should be Tile objects
    # self.tofindout - should be tuples
    # self.toclick   - should be tuples
    # self.tomark    - should be tuples
    # self.flags     - should be set of tuples (to prevent duplicates)
    # self.stats     - has statistics info

    def __init__(self, rawgrid,
                 verbose=True, chord=True,
                 totalBombsCount=None,
                 minimizeMouseUsage=False, maxPassesPerIteration=1,
                 smartStalledRandomClick=True,
                 stalledSubsetCheck=False, stalledBruteForceCheck=False,
                 alternatePassDirection=False, mentallyTrackFlags=False):
        # validation stuff
        if maxPassesPerIteration < 1:
            raise ValueError('maxPassesPerIteration must be at least 1!')
        if totalBombsCount!=None and ( type(totalBombsCount)!=int or totalBombsCount<1 ):
            raise ValueError('totalBombsCount must be either None or a positive integer!')
        # config stuff
        self.verbose = verbose
        self.chord = chord
        self.minmouseusage = minimizeMouseUsage
        self.maxpasses = maxPassesPerIteration
        self.smartstalledclick = smartStalledRandomClick
        self.totalbombs = totalBombsCount
        self.stalledsubset = stalledSubsetCheck
        self.stalledbruteforce = stalledBruteForceCheck
        self.alternatepass = alternatePassDirection
        self.mentalflags = mentallyTrackFlags

        self.stats = {
            'iterations': 0,
            'runs': 0,
            'firstiterstalls': 0,
            'maxiters': 0,
            'stallattempts':{},
            'stallsuccesses':{}
            }

        self.parseGrid(rawgrid)


    def parseGrid(self, rawgrid):
        
        '''resets all the data of self that is tracked and related to a rawgrid'''
        if self.verbose:
            print(' parsing grid')
        # grid stuff
        self.height = len(rawgrid)
        if self.height < 1:
            raise ValueError('rawgrid has no height (rows)!')
        self.width = len(rawgrid[0])
        if self.width < 1:
            raise ValueError('rawgrid has no width (columns)!')
        
        # init grid of Tile objects
        if self.verbose:
            print('  initializing tile objects')
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
            
        # update all tiles in tile grid, and track the numbers
        if self.verbose:
            print('  updating and tracking tile objects')
        self.tracked = []
        self.flags = set()
        for row in self.tiles:
            for tile in row:
                tile.updateArounds(self.tiles)
                if tile.isnumber():
                   tile.settracked(self.tracked, True)
                if tile.isflag():
                    self.flags.add(tile.coords)

        # (possibly re-)initialize the needs
        ## TODO move these out of parseGrid? need to? put them in init instead?
        self.tofindout = []
        self.toclick = []
        self.tomark = []

        if self.verbose:
            self.printstate()
            

    
    def updatefinds(self, rawgrid, foundout):
        if len(foundout) < 1:
            if self.verbose:
                print(' updated 0 new finds (none to update)')
            return
        if self.verbose:
            print(' updating ({0}) new finds...'.format(len(foundout)))
        # update themselves
        for coords in foundout:
            x, y = coords
            ftile = self.tiles[y][x]
            ftile.updateSelf(rawgrid)
            if ftile.isexploded():
                raise AIExplodedException('EXPLODED BOMB FOUND! WEE WOO WEE WOO')
            if self.verbose:
                print("  updated {0} to be '{1}'".format(coords,ftile.tile))
                if ftile.isunknown():
                    print("   {0} was unknown!".format(coords))
        # then update their arounds after all selves are updated
        for coords in foundout:
            x, y = coords
            ftile = self.tiles[y][x]
            ftile.updateArounds(self.tiles)
            if ftile.isnumber():
                if ftile not in self.tracked:
                    self.tracked.append(ftile) # track it if it's a number
                else:
                    if self.verbose:
                        print('  {0} was already tracked!'.format(coords))
            if self.verbose:
                print("  updated the arounds of {0} ('{1}'){2}"
                      .format( coords, ftile.tile,
                              " ({0} unknowns, {1} flags)"
                               .format(len(ftile.unknowns), len(ftile.flags))
                               if ftile.isnumber() else ""
                              ))
        print(' updated {0} new finds'.format(len(foundout)))


    def needschorded(self, x, y, findoutcenter=False, _mentalflagsmustoverride=True):
        # if mentalflags is True, then chording won't work in the actual game
        chord = self.chord and (not self.mentalflags or not _mentalflagsmustoverride)
        tup = (x, y)
        tile = self.tiles[y][x]
        # note: if tile is unknown, don't do non-chord strategy, because it likely causes problems (namely with clicking bombs)
        if tile.isunknown():
            chord = True
        # if should chord, mark the center as to be clicked
        if chord and tup not in self.toclick:
            self.toclick.append(tup)
        neighbors = list(tile.neighbors)
        if findoutcenter: # if center needs found too, append it
            neighbors += [ tile ]
        for ctile in neighbors:
            ctup = ctile.coords
            # find out the neighboring tile's new arounds
            if ctile.isunknown() or ctile.isnumber():
                if ctup not in self.tofindout:
                    print(ctup)
                    self.tofindout.append(ctup)
            if ctile.isunknown():
                # if not chord, then click unknowns
                if not chord:
                    self.toclick.append(ctup)
                    #debugging info (for an unexpectedly unregistered unknown)
                    if tile.isnumber() and ctile not in tile.unknowns:
                        print('  debug: {1} was not registered as unknown of {0}'
                              .format(ctile.coords, tup))
                # mark unknowns as find-out, because they won't be unknowns anymore
                ctile.setTile(NEEDSFOUND) # allows for optimization of future iters
        if self.verbose:
            print('  chording',tup)

    def needssingleclicked(self, x, y):
        tup = (x, y)
        if tup not in self.toclick:
            self.toclick.append(tup)
        if tup not in self.tofindout:
            self.tofindout.append(tup)
        self.tiles[y][x].setTile(NEEDSFOUND)
        if self.verbose:
            print('  single-clicking',tup)

    def needsmarked(self, x, y, rawgrid, editrawgrid=True): #TODO self.mentalflags
        tile = self.tiles[y][x]
        tile.setTile(FLAG) # set it prematurely as a flag; we know it will be
        self.flags.add(tile.coords) # track it as a flag
        if editrawgrid: # just a note: even if self.mentalflags is true, this still happens (cause it's before the abort)
            rawgrid[y][x] = FLAG # edit the actual rawgrid to keep it up-to-date
        if self.mentalflags:
            return # abort early if flags are being kept mentally, and not actually clicked
        self.tomark.append(tile.coords)
        if self.verbose:
            print('  marking',tile.coords)


    def stalledclick(self, rawgrid):
        # if not smart, choose completely random
        if not self.smartstalledclick:
##            foundrnd = False
                hl = list(range(0, self.height))
                shuffle(hl)
                wl = list(range(0, self.width))
                shuffle(wl)
                for y in hl:
                    for x in wl:
                        if isunknown(rawgrid[y][x]): # note: using string check, not Tile
##                            foundrnd = True
                            self.needschorded(x, y, findoutcenter=True)
                            print('  AI found new random click at',(x,y))
                            return
##                            break
##                    if foundrnd == True:
##                        break
        
        # if smart, check probabilities
        else:
##            raise RuntimeError('OOPS! self.smartstalledclick functionality not implemented')
            candototalbombcheck = ( self.totalbombs != None )
            candidate = None # will hold the 'best so far' (least likely to be a bomb)
            unknowncandidate = None
            unknownscount = 0
            yrange = range(0, self.height)
            xrange = range(0, self.width)
            for y in yrange:
                for x in xrange:
                    tile = self.tiles[y][x]
                    # ignore it if it's not an unknown
                    if not tile.isunknown():
                        continue
                    unknownscount += 1 # count the unknowns
                    
                    # get max of wrong-ness probability (how likely it is to be a bomb)
                    wrongprobs = []
                    # for each neighboring number:
                    for ctile in tile.neighbors:
                        if ctile.isnumber():
                            # get the neighbor's surrounding flags and unknowns count
                            flags = len(ctile.flags)
                            unknowns = len(ctile.unknowns)
                            # find how many of the unknowns must be unmarked bombs
                            remain = ctile.tilenum() - flags
                            chance = remain / unknowns  if unknowns > 0 else 0
                            if chance > 1: # can't be more than 100% likely
                                raise AIAnalyzeException(
                                    "chance of {0} being a bomb, from {1}, is > 1? ({2})"
                                    .format(tile.coords, ctile.coords, chance)
                                    + ' (was remain > unknowns?)')
                            wrongprobs.append(chance)
                    
                    # get the tile's greatest chance of being a bomb
                    if len(wrongprobs) == 0:
                        # must not have had any numbers nearby
                        if candototalbombcheck:
                            # if we know the total bombs of the grid, save the
                            #   chance calculation for later, when we know total unknowns
                            if unknowncandidate == None: # but don't override any; causes discontinuity with candidate
                                unknowncandidate = tile
                            chance = 1 # ignore it from the regular candidate chances
                        else:
                            chance = AI.defaultunknownchance # go with a default chance
                    else:
                        # must have had numbers nearby; list is populated, so get the max
                        chance = max(wrongprobs)
                    
                    # see if it's a better candidate
                    if candidate == None or chance < candidate.chance:
                        if candidate != None: # clear previous' .chance if possible
                            del candidate.chance # cleanup
                        # save the chance to the Tile object, for easy data correlation
                        tile.chance = chance
                        # save the current unknown tile as the best candidate so far
                        candidate = tile
                    
            # note: if candidate is None by this point, probably no unknown tile was found
            if candidate != None:
                # if there was an unknown with no numbers, calculate chance now
                if unknowncandidate != None:
                    bombsremain = self.totalbombs - len(self.flags)
                    # now that we know unknownscount, we can figure out a probability
                    chance = bombsremain / unknownscount
                    if self.verbose:
                        print('   unknowncandidate from {0} with chance {1}'
                              .format(unknowncandidate.coords, chance))
                    # see if it's a better candidate
                    if chance < candidate.chance:
                        del candidate.chance # cleanup
                        # set the .chance just to prevent errors below
                        unknowncandidate.chance = chance
                        candidate = unknowncandidate
                if self.verbose:
                    print("   final candidate {0} ('{1}') has chance of {2}"
                          .format(candidate.coords, candidate.tile, candidate.chance))
                # click the best candidate!
                self.needschorded(candidate.x, candidate.y, findoutcenter=True)
                print('  AI found new click at {0} with the least chance to be a bomb ({1})'
                      .format( candidate.coords, candidate.chance ))
                del candidate.chance # cleanup the .chance for uselessness reasons
                return
            else:
                if self.verbose:
                    print('  AI failed to find a candidate! unknownscount =',unknownscount)


    def analyzetracked(self, rawgrid):
        ## analyze the tracked numbers
        untrack = []
        for tile in self.tracked:
            tup = tile.coords
            x, y = tup
            if self.verbose:
                print(' analyzing {0}...'.format(tup))
            if not tile.isnumber():
                print(" tracked tile {0} was not a number! ('{1}')".format(tup, tile.tile))
                untrack.append(tile)
                continue
            n = tile.tilenum()
            flags = len(tile.flags)
            unknowns = len(tile.unknowns)

            # if too many bombs around
            if flags > n:
                raise AIAnalyzeException(' OOPSIE there\'s more bombs than should be! {0} (flags={1} n={2})'
                                .format(tile.coords, flags, n))
        
            # just enough bombs around
            elif flags == n:
                # if unknowns remain, click them
                if unknowns > 0:
                    self.needschorded(x, y)
                # if no unknowns remain, all good
                else:
                    pass
                untrack.append(tile)

            # totals up properly; remaining unknowns must be bombs
            elif flags + unknowns == n:
##                for unknown in n:
##                    print('from',tup,'marking',unknown.coords,'as bomb')
##                    self.needsmarked(unknown.x, unknown.y)
                dyrange = range( -1 if y > 0 else 0,  2 if y < self.height-1 else 1 )
                dxrange = range( -1 if x > 0 else 0,  2 if x < self.width-1 else 1 )
                for dy in dyrange:
                    for dx in dxrange:
                        # for each tile around
                        cx = x + dx
                        cy = y + dy
                        ctile = self.tiles[cy][cx]
                        # mark unknowns around
                        if ctile.isunknown():
                            self.needsmarked(cx, cy, rawgrid, AI.markingedits)
                        # recalculate nearby numbers (in the next AI iteration)
                        if ctile.isnumber() and not (dy==0 and dx==0):
                            self.tofindout.append( ctile.coords )
                untrack.append(tile)
        print(' analyzed all ({0}) tracked'.format(len(self.tracked)))

        ## finalize the output
        print(' finalizing - untracking {0} tiles for which actions have been generated...'
              .format(len(untrack)))
        for tile in untrack:
            if self.verbose:
                print('  untracking {0} ...'.format(tile.coords))
            self.tracked.remove(tile)
            if tile.coords in self.tofindout:
                if self.verbose:
                    print('   removing {0} from tofindout also ...'.format(tile.coords))
                self.tofindout.remove(tile.coords)


    def stalledsubsetcheck(self, rawgrid):
        print(' checking possibility subsets...')
        trackedsubsets = []
        
        ## fill up the subset list with data
        for num in self.tracked:
            # create data of { bombs remaining, and the set of unknowns around }
            numinfo = ( num.tilenum()-len(num.flags), {u.coords for u in num.unknowns} )
            # insert intelligently
            inserted = False
            for i in range(0, len(trackedsubsets)):
                ni = trackedsubsets[i]
                if ni == numinfo: # already in list; don't append
                    inserted = True
                    break
                if ni[1] == numinfo[1]: # subsets the same; keep the one with lower remain
                    if ni[0] > numinfo[0]: # check if numinfo has a lower remain count
                        trackedsubsets[i] = numinfo
                        inserted = True
                        break
            if not inserted:
                trackedsubsets.append(numinfo) # if new subset group, insert it
                
        ## "whittle down" the list
        toremove = [None]
        toappend = [None]
        # keep going while there's stuff still found to do
        while len(toremove) != 0 or len(toappend) != 0:
            # clear the action lists
            toremove = []
            toappend = []
            
            # for each info:
            for info1 in trackedsubsets:
                # for each other info:
                for info2 in trackedsubsets:
                    # make sure they're not the same data item
                    # also make sure they're not "removed"
                    if info1 != info2 and (info1 not in toremove and info2 not in toremove):
                        
                        # if info's set is a subset of info2's set:
                        if info1[1].issubset(info2[1]):
                            if len(info1[1]) == len(info2[1]): # just to make sure
                                raise RuntimeError('two infos got past the same-subset'
                                                   +' insertion checking! ( {0} and {1} )'
                                                   .format(info1, info2))
                            # split the subsets up into mutually exclusive subsets;
                            #  one part is the initial subsetted data (info1),
                            #  and sub2 is the remainder subset, with the remaining bombs
                            # note that we're implicitly keeping info1 in the data list
                            sub2 = ( info2[0]-info1[0], info2[1].difference(info1[1]) )
                            toremove.append(info2)
                            toappend.append(sub2) # extra note: sub2 might contain no bombs; therefore, it's then an empty group
            
            # perform the queued actions
            for tr in toremove:
                trackedsubsets.remove(tr)
            for ta in toappend:
                trackedsubsets.append(ta)
        
        ## deal with the list's contents
        for info in trackedsubsets:
##            if len(info[1]) == 1: # just a singular tile - can be clicked
##                if info[0] != 1: # 'integrity check' to make sure bombs in group == 1
##                    raise RuntimeError('a group-of-1 had non-1 bombs! {0}'.format(info))
##                x, y = info[1][0] # unpack the single tile's coords
##                self.needschorded(x, y, findoutcenter=False)
##                continue
            if len(info[1]) == info[0]: # is a filled group; mark all
                if self.verbose:
                    print('   marking all in full group - {0}'.format(info))
                for x, y in info[1]: # for each coords in set
                    self.needsmarked(x, y, rawgrid, AI.markingedits)
                continue
            if info[0] == 0: # is an empty group; click all
                if self.verbose:
                    print('   single-clicking all in empty group - {0}'.format(info))
                for x, y in info[1]: # for each coords in set
                    self.needssingleclicked(x, y)
                continue

    
    def recstat(self, name):
        self.stats['stallattempts'][name] = (self.stats['stallattempts'][name] + 1 if name in self.stats['stallattempts'] else 1)
    def recsucc(self, name, success=True):
        self.stats['stallsuccesses'][name] = (self.stats['stallsuccesses'][name] if name in self.stats['stallsuccesses'] else 0) + (1 if success else 0)

    def dealwithstalling(self, rawgrid, isfirstiter): # return False to stop iteration
        if len(self.tomark) == 0 and len(self.toclick) == 0 and len(self.tofindout) == 0:
##            if len(self.tofindout) != 0:
##                print('',end='',flush=True)
##                print(' NOTICE: AI is stalled but has',len(self.tofindout),'in tofindout!',
##                      flush=True,file=sys_stderr)
##                self.printstate()
##                print()
            # stalled due to AI having no idea what to do next
            print(' AI stalling...')

            if not isfirstiter:
                # prevent tofindout and stuff getting overridden in parseGrid
                print('  not first iteration; stalling will cease to resolve'
                      + '\n   until tomark, toclick, and tofindout are dealt with')
                return False

            self.stats['firstiterstalls'] += 1

##            if self.verbose:
##                print('  tofindout has',len(self.tofindout),'items')

            ## try to find a missed number (or bomb) somewhere

            print('  parsing entire grid again to refresh tracked data...')

            self.parseGrid(rawgrid)

            self.recstat('analyzetracked')
            self.analyzetracked(rawgrid)

            if len(self.toclick) > 0 or len(self.tomark) > 0:
                self.recsucc('analyzetracked')
                print('  analyzetracked found {0} clicks and {1} marks!'
                      .format(len(self.toclick),len(self.tomark)))
                return False

            ## if failed, try to figure out clicks by deduction (if enabled)

            # 'process of elimination' or 'grouping' deduction
            if self.stalledsubset:
##                raise RuntimeError('OOPS! self.stalledsubset functionality not implemented')
                self.recstat('stalledsubset')
                self.stalledsubsetcheck(rawgrid)

                if len(self.toclick) > 0 or len(self.tomark) > 0:
                    self.recsucc('stalledsubset')
                    print('  stalledsubset found {0} clicks and {1} marks!'
                          .format(len(self.toclick),len(self.tomark)))
                    return False

            # 'trial-and-error' or 'brute force' deduction
            if self.stalledbruteforce:
                self.recstat('stalledbruteforce')
                raise RuntimeError('OOPS! self.stalledbruteforce functionality not implemented')

                if len(self.toclick) > 0 or len(self.tomark) > 0:
                    self.recsucc('stalledbruteforce')
                    print('  stalledbruteforce found {0} clicks and {1} marks!'
                          .format(len(self.toclick),len(self.tomark)))
                    return False
            
            ## if failed, try to find a random click
            
            print(' trying to find random click position...')

            self.recstat('stalledrandomclick')
            self.stalledclick(rawgrid)

            ## if failed, welp guess it's done or something
            
            if len(self.tomark) == 0 and len(self.toclick) == 0 and len(self.tofindout) == 0:
                # still stalled
                raise AIStalledException('AI has no idea what to do next; stalled!')

            self.recsucc('stalledrandomclick')
            
            return False # found something to do; needs to be done

        return True # nothing needed done; continue iteration(s)


    def cleanupmouseusage(self): ## TODO make it put everything in a 2d array first & then do optimized comparisons via the 5x5 square around it, so it's more like O(25*n) instead of nearly O(n^2), and also you can combine the neighbors in the 5x5 and test if any of them overlap it, not one-by-one
        if not self.chord:
            print('AI: click cleaning is deemed useless because chording is disabled')
        if len(self.toclick) < 1:
            print('AI: no clicks to clean')
            return
        cleanedcount = 0
        print('AI finalizing - cleaning mouse clicks...')
        rev = range(len(self.toclick)-1,-1,-1)
        for i in rev:
            click = self.toclick[i]
            ctile = self.tiles[click[1]][click[0]]
            if not ctile.isnumber():
                if self.verbose:
                    print('  skipping non-number {0}'.format(click))
                continue
            for other in self.toclick:
                if other == click: # if they're the same click pos
                    continue
                otile = self.tiles[other[1]][other[0]]
                if not otile.isnumber():
                    continue
                # remove click if the other's unknowns include all of click's unknowns
                if ctile.unknowns.issubset(otile.unknowns):
##                    print('subset', ctile.unknowns, ' -in- ', otile.unknowns)
                    if self.verbose:
                        print('  removing click at {0}'.format(click))
                    self.toclick.pop(i)
                    cleanedcount += 1
                    break

        print(' removed {0} redundant clicks'.format(cleanedcount))
    

    def iterate(self, rawgrid, foundout, isfirstiter,
                altPassDirection=False,): #return False to stop iter
        self.alternatethispass = ( bool(altPassDirection) == True ) TODO self.alternatethispass
        print('AI iterating...')
        if self.verbose:
            print(' alternatethispass =',self.alternatethispass)
        
        # if nothing new was found out, search for new stuff
        if len(foundout) < 1:
            if not isfirstiter:
                # prevent tofindout and stuff getting overridden in parseGrid
                print('  no new foundout; also not first iteration; will avoid parsing grid'
                      + '\n   until tomark, toclick, and tofindout are dealt with')
                return False
            print(' no new foundout; parsing whole grid for information')
            self.parseGrid(rawgrid)
            if len(self.tracked) < 1:
                print(' no numbers found; clicking random')
                rx = choose(range(0, self.width))
                ry = choose(range(0, self.height))
                self.needschorded(rx, ry, findoutcenter=True)
                return False # returning false to prevent further redundant iterations

        # TODO will updating finds on non-first iterations cause problems??
        # skip this? use tofindout somewhere? as tracked? or is tracked good?
        self.updatefinds(rawgrid, foundout)

        self.analyzetracked(rawgrid)

        ## check for AI stalling
            
        stalledsuccess = self.dealwithstalling(rawgrid, isfirstiter)
        
        if not (stalledsuccess==True or stalledsuccess==False):
            raise ValueError('stalledsuccess ({0}) was not explicitly True or False'
                             .format(stalledsuccess))

##        ## if enabled, cleanup useless mouse usage ----- moved to end of run()
##
##        if self.minmouseusage:
##            self.cleanupmouseusage()
            
##        if len(tomark) == 0 and len(toclick) == 0 and len(tofindout) == 0:
##            # still stalled
##            raise AIStalledException('AI has no idea what to do next; stalled!')
        
        del self.alternatethispass # cleanup
        print('AI completed iteration')
        return stalledsuccess


    def run(self, rawgrid, foundout=None):
        if foundout == None:
            foundout = []
##        # reset some per-run variables
##        self.tomark = []
##        self.toclick = []
##        self.tofindout = []
        self.stashtomark = []
        self.stashtoclick = []
        self.stashtofindout = []

        print('AI running...')
        itercount = 0
        keepgoing = True
        while keepgoing and itercount < self.maxpasses:
            altpass = ( self.alternatepass and itercount % 2 == 1 ) # alternate when odd
            if self.verbose:
                print('itercount =',itercount)
                print('altpass =',altpass)
                
            # reset some per-iteration variables
            self.tomark = []
            self.toclick = []
            self.tofindout = []
            
            keepgoing = self.iterate(rawgrid, foundout, itercount==0,
                                     altPassDirection=altpass)

            # 'stash' the to-be-done items so each iteration can see
            #   how many new things that it has created, not what other iterations have
            print('stashing {0} marks, {1} clicks, and {2} findouts'
                  .format(len(self.tomark), len(self.toclick), len(self.tofindout)))
            self.stashtomark += self.tomark
            self.stashtoclick += self.toclick
            self.stashtofindout += self.tofindout
            
            itercount += 1
        if self.verbose:
            print('AI ran {0} iterations (out of {1})'.format( itercount, self.maxpasses ))
            print('keepgoing was',keepgoing)
        else:
            print('AI ran {0} iterations'.format( itercount ))

        self.stats['iterations'] += itercount
        self.stats['runs'] += 1
        if itercount >= self.maxpasses:
            self.stats['maxiters'] += 1

        # 'unstash' & remove duplicates via set
        if self.verbose:
            print('AI unstashing actions & removing duplicates')
        self.tomark = list(set( self.stashtomark ))
        self.toclick = list(set( self.stashtoclick ))
        self.tofindout = list(set( self.stashtofindout ))

        if self.minmouseusage:
            self.cleanupmouseusage()
        
        return self.tomark, self.toclick, self.tofindout


    def tilestostr(self, title, foreachtile):
        s = '\n' + title
        for row in self.tiles:
            s += '\n'
            for tile in row:
                s += str(foreachtile(tile)) + ' '
        return s

    def printstate(self):
        print('printing AI state...')
        state = ''
        state += self.tilestostr('tiles:',lambda t: t.tile) #pylint:disable=no-member
        state += self.tilestostr('tracked:',lambda t: 'x' if t in self.tracked else '.')
        state += self.tilestostr('unknowns around:',
                            lambda t: len(t.unknowns) if hasattr(t, 'unknowns') else '.')
        state += self.tilestostr('flags around:',
                            lambda t: len(t.flags) if hasattr(t, 'flags') else '.')
        state += '\ntomark = ' + str(self.tomark)
        state += '\ntoclick = ' + str(self.toclick)
        state += '\ntofindout = ' + str(self.tofindout)
        print(state)


    def printstats(self):
        print('printing AI stats...')
        print()
        runs = self.stats['runs']
        iters = self.stats['iterations']
        maxiters = self.stats['maxiters']
        fis = self.stats['firstiterstalls']
        print('total runs: {0}'
              .format(runs))
        print('total iterations: {0} (average {1:.2f} per run)'
              .format(iters, iters/runs))
        print('runs hit the max iteration limit {0} times ({1:.2%} of all runs) (limit={2})'
              .format(maxiters, maxiters/runs, maxiters))
        print()
        print('AI\'s normal algorithm stalled {0} times (first-iters) ({1:.2%} of all runs)'
              .format(fis, fis/runs))
        print(' stalling algorithm success:')
        for key, atts in self.stats['stallattempts'].items():
            succs = self.stats['stallsuccesses'][key] if key in self.stats['stallsuccesses'] else 0
            print(" algorithm '{0}': solved {1:.2%} of stalls ({2:.1%} self; {3}/{4} s/a)"
                  .format(key, succs/fis, succs/atts, succs, atts))
        

## =============================================================== ##
#####################################################################
#####################################################################
#####################################################################
#####################################################################

