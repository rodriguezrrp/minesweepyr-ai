## code by rodriguezrrp on GitHub
## MIT license

import time
from itertools import chain

import pyscreenshot as ImageGrab

import pyautogui as pygui

from numpy import asarray as numpy_asarray

from minesweeperai import AI, AIStalledException

if __name__ == '__main__':


    ## ================== CONFIG ================== ##

    ## Specifies the style of grid for the image parser to expect

    # 1 = minesweeper.online's style
    # no others implemented currently
    GRIDSTYLE = 1


    ## Some delay options

    # mouse-moving duration
    MOVEDUR = 0.0
    # delay between marks
    MARKDELAY = 0.03
    # delay between moving to mark and actually marking
    WAITTOMARK = 0.01
    # delay between clicks
    CLICKDELAY = 0.07
    # delay between moving to click and actually clicking
    WAITTOCLICK = 0.07
    # delay between all marking and all clicking and etc.
    BETWEENDELAY = 0.02

    # pause between performing all the mouse actions and running the AI
    ITERATIONSLEEP = 1.3

    # delay between calibration point detection
    caldelay = 2.5
    

    ## More debug info!
    
    VERBOSE = False

    ## ============================================ ##

    showprecalimage = False

    inp = None
    onlyparseimage = False
    
    customaiconfig = True # note to self: this should init as False probably
    configopts = {
        'verbose': VERBOSE,
        'chord': True,
        'minimizeMouseUsage': True,
        'maxPassesPerIteration': 15,
        'smartStalledRandomClick': True,
        'stalledSubsetCheck': True,
        'stalledBruteForceCheck': False,
        'alternatePassDirection': False,
        'mentallyTrackFlags': False
        }
    # cast these to int instead of bool
    configoptsints = sorted([
        'maxPassesPerIteration'
        ])

    while True:

        inp = input("""type 'config' to go through config settings before running AI,
                'image' to only parse image and not run AI,
                or anything else (or just pressing Enter) to run AI
                > """)

        if inp == 'config':
            customaiconfig = True
            print('note: for each config setting, entering nothing will set it to default')
            
            for config, val in configopts.items(): # for each key:value pair in configopts
                inp = input(' {0}: '.format(config))
                if inp != '':
                    if config in configoptsints:
                        newval = int(inp)
                    else:
                        newval = bool(inp)
                    configopts[config] = newval
                print(' {0} = {1}'.format(config, newval))
            break
        
        elif inp == 'image':
            onlyparseimage = True
            break
        
        else:
            break


    ai = None

    def instantiateAI(rawgrid, totalbombs=None):
        global ai
        if customaiconfig:
            ai = AI(rawgrid,
                    verbose = configopts['verbose'],
                    chord = configopts['chord'],
                    totalBombsCount = totalbombs,
                    minimizeMouseUsage       = configopts['minimizeMouseUsage'],
                    maxPassesPerIteration    = configopts['maxPassesPerIteration'],
                    smartStalledRandomClick  = configopts['smartStalledRandomClick'],
                    stalledSubsetCheck       = configopts['stalledSubsetCheck'],
                    stalledBruteForceCheck   = configopts['stalledBruteForceCheck'],
                    alternatePassDirection   = configopts['alternatePassDirection'],
                    mentallyTrackFlags       = configopts['mentallyTrackFlags']
                    )
        else:
            ai = AI(rawgrid, verbose=VERBOSE, totalBombsCount=totalbombs)



    # width and height of the minesweeper board, in tiles
    # beginner: 9x9; intermediate: 16x16; expert = 30x16;
    gamewidth = int(input('input width (in tiles): > '))
    gameheight = int(input('input height (in tiles): > '))
    # bombs of the minesweeper board (useful for AI)
    if not onlyparseimage:
        totalbombs = input('input total bomb count (optional): > ')
        try:
            totalbombs = int(totalbombs, 10)
        except ValueError:
            print(' ok, total bomb count will not be set')
            totalbombs = None
    

    ## get positions and calibrate

    print('\nCalibration starting!')

    print('waiting',caldelay,'secs for first corner...')
    time.sleep(caldelay)
    print('getting first corner')
    pos1 = pygui.position()
    print(pos1)

    print('waiting',caldelay,'secs for second corner...')
    time.sleep(caldelay)
    print('getting second corner')
    pos2 = pygui.position()
    print(pos2)

    ## find and use initial calibration image

    # buffer so the program has enough image to find the exact edges of the grid
    calbuf = int((pos2.x - pos1.x) / gamewidth) # should be approx. 1 tile size
    if VERBOSE:
        print('calbuf =', calbuf)
    bufbbox = (pos1.x-calbuf, pos1.y-calbuf, pos2.x+calbuf, pos2.y+calbuf)

    im = ImageGrab.grab(bbox=bufbbox, childprocess=False)
    if VERBOSE:
        print(im)
        print(im.size)
    if showprecalimage:
        im.show()

    ## go ahead and define the main colors to check for

    def hexcol(hexstr):
        return ( int(hexstr[0:2],16), int(hexstr[2:4],16), int(hexstr[4:6],16) )

    def coleq(col1, col2):
        return col1[0]==col2[0] and col1[1]==col2[1] and col1[2]==col2[2]
    
    if GRIDSTYLE == 1: # minesweeper.online
        LIGHT = hexcol('ffffff')
        GRAY  = hexcol('c0c0c0')
        DARK  = hexcol('808080')
        COL_1 = hexcol('0000ff')
        COL_2 = hexcol('008000')
        COL_3 = hexcol('ff0000')
        COL_4 = hexcol('000080')
        COL_5 = hexcol('800000')
        COL_6 = hexcol('008080')
        COL_7 = hexcol('000000')
        COL_8 = hexcol('808080')
    else:
        raise ValueError('GRIDSTYLE must be an int between 1 and 1 (inclusive)')

    ## parse calibration

    # the positions will be relative to the top left of the scrot image
    calx = calbuf
    caly = calbuf
    calx2 = im.size[0] - calbuf
    caly2 = im.size[1] - calbuf

    impx = numpy_asarray(im)
    if VERBOSE:
        print('got im pixels numpy_asarray')

    ## move calx and caly into top left of top left tile

    # do calx
##    while not coleq(impx[caly][calx], GRAY): # move x left until gray is found (should get out of any numbers?)
####        print('not gray',calx,caly)
##        calx -= 1
    while coleq(impx[caly][calx], GRAY): # move x left until edge of gray
##        print('gray',calx,caly)
        calx -= 1
    while not coleq(impx[caly][calx], LIGHT): # move until light found
##        print('not light',calx,caly)
        # finding dark before light would mean that the tile was a clicked tile
        if coleq(impx[caly][calx], DARK):
            calx -= 1 # for calx post-readjustment
            break
        calx -= 1
    while coleq(impx[caly][calx], LIGHT): # move until edge of light
##        print('light',calx,caly)
        calx -= 1
    calx += 1

    # do caly
##    while not coleq(impx[caly][calx], GRAY):
##        caly -= 1
    while coleq(impx[caly][calx], GRAY):
        caly -= 1
    while not coleq(impx[caly][calx], LIGHT):
        if coleq(impx[caly][calx], DARK):
            caly -= 1
            break
        caly -= 1
    while coleq(impx[caly][calx], LIGHT):
        caly -= 1
    caly += 1


    ## move calx2 and caly2 into bottom right of bottom right tile

    # do calx2
##    while not coleq(impx[caly2][calx2], GRAY):
####        print('not gray',calx2,caly2)
##        calx2 += 1
    while coleq(impx[caly2][calx2], GRAY):
##        print('gray',calx2,caly2)
        calx2 += 1
    while not coleq(impx[caly2][calx2], DARK):
##        print('not dark',calx2,caly2)
        if coleq(impx[caly2][calx2], LIGHT):
            calx2 += 1
            break
        calx2 += 1
    while coleq(impx[caly2][calx2], DARK):
##        print('dark',calx2,caly2)
        calx2 += 1
    calx2 -= 1

    # do caly2
##    while not coleq(impx[caly2][calx2], GRAY):
####        print('not gray',calx2,caly2)
##        caly2 += 1
    while coleq(impx[caly2][calx2], GRAY):
##        print('gray',calx2,caly2)
        caly2 += 1
    while not coleq(impx[caly2][calx2], DARK):
##        print('not dark',calx2,caly2)
        if coleq(impx[caly2][calx2], LIGHT):
            caly2 += 1
            break
        caly2 += 1
    while coleq(impx[caly2][calx2], DARK):
##        print('dark',calx2,caly2)
        caly2 += 1
##    caly2 -= 1
    calx2 += 1 # don't scoot y, and scoot x forward again, so crop 'looks nice'

    ## get new cropped image

    calbbox = (pos1.x-calbuf+calx, pos1.y-calbuf+caly,
              pos1.x-calbuf+calx2, pos1.y-calbuf+caly2)

    print('calibration bounding box =',calbbox)

    def capturenewimage(show = False):
        # get the im and impx variables from outside, so reassignment works
        global im
        global impx
        if VERBOSE:
            print('capturing new image')
##        print(' calbbox =', calbbox)
        im = ImageGrab.grab(bbox=calbbox, childprocess=False)
        if VERBOSE:
            print(im)
##        print(im.size)
        if show == True:
            im.show()
        impx = numpy_asarray(im)
##        return (im, impx)

    capturenewimage(onlyparseimage or VERBOSE)

    ## parse cropped image into tiles

    rawgrid = []
    for y in range(0, gameheight):
        rawgrid.append([])
        for x in range(0, gamewidth):
            rawgrid[y].append('-')

    def printrawgrid():
        tstr = '\n'
        for row in rawgrid:
            for x in row:
                tstr += str(x) + ' '
            tstr += '\n'
        print(tstr)

##    if VERBOSE:
##        printrawgrid()

    if VERBOSE:
        print('(im.size[0] = {0}) / (gamewidth = {1}) = {2}'
              .format(im.size[0], gamewidth, im.size[0]/gamewidth))
    tilesize = im.size[0] / gamewidth
    print('tile size:', tilesize, '(' + str(int(tilesize)) + ', ' + str(tilesize) + ')')
##    tilesize = int(tilesize)


    def parsetile(x, y, impx):
        # get tile's center
        pxx = int( (x + 0.5) * tilesize )
        pxy = int( (y + 0.5) * tilesize )
        # whatever the tile is determined to be
        tile = '.'

        ## test for number tile

        # test a few pixels around the center to get good coverage
        pxradius = int(tilesize/4)
        for x1 in range(pxx-pxradius, pxx+pxradius+1):
            for y1 in range(pxy-pxradius, pxy+pxradius+1):
                xycol = impx[y1][x1]
                if coleq(xycol, COL_1):
                    tile = '1'
                    break
                elif coleq(xycol, COL_2):
                    tile = '2'
                    break
                elif coleq(xycol, COL_3):
                    # note: tends to label clicked bombs (ones with Xs) as '3'
                    if coleq(impx[pxy][pxx], COL_3): # if center is also red, it's 3
                        tile = '3'
                    else:
                        tile = 'B'
                    break
                elif coleq(xycol, COL_4):
                    tile = '4'
                    break
                elif coleq(xycol, COL_5):
                    tile = '5'
                    break
                elif coleq(xycol, COL_6):
                    tile = '6'
                    break
                elif coleq(xycol, COL_7):
                    # special case; check BR for red if exploded bomb
                    EXP_BOMB_RED = hexcol('ff0000')
                    for x2 in range(int((x+0.6)*tilesize),
                                    int((x+0.9)*tilesize)+2):
                        for y2 in range(int((y+0.6)*tilesize),
                                        int((y+0.9)*tilesize)+2):
                            if coleq(impx[y2][x2], EXP_BOMB_RED):
                                tile = 'B'
                                break
                        if tile == 'B':
                            break
                    if tile != 'B': # if failed to find it as exploded bomb
                        # special; check TL corner for black if it's not a flag
                        # note: tends to label non-red visible bombs as '7'
                        for x2 in range(int(x*tilesize)+1,
                                        int((x+0.4)*tilesize)+2):
                            for y2 in range(int(y*tilesize)+1,
                                            int((y+0.4)*tilesize)+2):
                                if coleq(impx[y2][x2], COL_7):
                                    tile = '7'
                                    break
                            if tile == '7':
                                break
                            if tile != '7': # if failed to find it as 7
                                tile = 'F' # must be flag
                    break
                elif coleq(xycol, COL_8):
                    tile = '8'
                    break
                else:
                    continue
            if tile != '.':
##                break
                rawgrid[y][x] = tile
                return
            
##        if tile != '.':
##            rawgrid[y][x] = tile
##            return

        ## test for unknown (unclicked) tile

        # get tile's upper left corner
        pxx = int( x * tilesize )
        pxy = int( y * tilesize )
##        print('')
##        print(coleq(xycol, LIGHT))
##        print(coleq(xycol, GRAY))
##        print(coleq(xycol, DARK))
        if coleq(impx[pxy][pxx], LIGHT):
            tile = '-'
##        elif coleq(xycol, DARK):
##            tile = ' '

##        for x1 in range(0, tilesize):
##            pass
        
        rawgrid[y][x] = tile
        

    ## parse each tile in the image
        
    for x in range(0, gamewidth):
        for y in range (0, gameheight):
            parsetile(x, y, impx)

    print('printing rawgrid...', flush=True)
    printrawgrid()


    if onlyparseimage == True: # stop here if parsing the image was the only task
        print()
        print('waiting a moment for picture')
        time.sleep(2)
        print('done')
    else:
        if VERBOSE or 'image' == input(
                " type 'image' if you want to see the image before AI starts > "):
            if not VERBOSE: # then input was successful instead
                im.show()
            print('waiting a moment for picture to show')
            time.sleep(1.5)
            input('type anything (or just Enter) to start the AI when ready')

        instantiateAI(rawgrid, totalbombs=totalbombs) # 'start up' the AI

        ## define mouse interaction functions
        
        def tiletomouse(coords):
            return ( calbbox[0] + (coords[0] + 0.5) * tilesize,
                     calbbox[1] + (coords[1] + 0.5) * tilesize )
        def leftclick(coords, duration=0.0, clickwait=0.0):
            pygui.moveTo(coords[0], coords[1], duration)
            if VERBOSE:
                print('   waiting',clickwait,'secs before click')
            time.sleep(clickwait)
            pygui.click()
        def rightclick(coords, duration=0.0, clickwait=0.0):
            pygui.moveTo(coords[0], coords[1], duration)
            if VERBOSE:
                print('   waiting',clickwait,'secs before rightclick')
            time.sleep(clickwait)
##            pygui.click(button='right')
            pygui.rightClick()
            

        ## setup mouse interactivity via AI output

        def mark(tomark):
            print('\nmarking all ({0}) in tomark...'.format(len(tomark)))
            for mark in tomark:
                if VERBOSE:
                    print('  marking',mark,'...')
                rightclick(tiletomouse(mark), MOVEDUR, WAITTOMARK)
                time.sleep(MARKDELAY)
            print('marked all in tomark'.format())

        def click(toclick):
            print('\nclicking all ({0}) in toclick...'.format(len(toclick)))
            for click in toclick:
                if VERBOSE:
                    print('  clicking',click,'...')
                leftclick(tiletomouse(click), MOVEDUR, WAITTOCLICK)
                time.sleep(CLICKDELAY)
            print('clicked all in toclick')

        def findout(rawgrid, tofindout):
            print('\nfinding all (>={0}) in tofindout...'.format(len(tofindout)))
            for find in tofindout:
                if VERBOSE:
                    print('  finding',find,'...', end='')
                parsetile(find[0], find[1], impx)
                tile = rawgrid[find[1]][find[0]]
                if VERBOSE:
                    print('  found out {0} as \'{1}\''.format(find, tile))
                if tile == '.':
                    x, y = find
                    if VERBOSE:
                        print("   tile was blank ('.') - queueing neighbors")
                    for dy in range( -1 if y > 0 else 0,
                                      2 if y < len(rawgrid)-1 else 1 ):
                        for dx in range( -1 if x > 0 else 0,
                                          2 if x < len(rawgrid[0])-1 else 1 ):
                            cx = x + dx
                            cy = y + dy
                            c = (cx, cy)
                            if c not in tofindout:
                                tofindout.append(c)
            print('found all ({0}) in tofindout'.format(len(tofindout)))


        # make initial click just outside the top left to ensure window is focused
        leftclick( (calbbox[0]-3, calbbox[1]-3), MOVEDUR, WAITTOCLICK )

        ## Do the things

        print('VERBOSE =',VERBOSE)

        tomark, toclick, tofindout = ai.run(rawgrid, foundout=None)

        if VERBOSE:
            ai.printstate()

        while True:

            print('\nsleeping between iterations')
            time.sleep(ITERATIONSLEEP)

            mark(tomark)
            time.sleep(BETWEENDELAY)
            click(toclick)
            time.sleep(BETWEENDELAY)
            capturenewimage(False)
            if VERBOSE:
                print('new im =',im)
            findout(rawgrid, tofindout)
            time.sleep(BETWEENDELAY)
            print()

            try:
                tomark, toclick, tofindout = ai.run(rawgrid, foundout=tofindout)
##            except AIStalledException:
            except:
                print()
                print('A FATAL ERROR OCCURED!')
                ai.printstats()
                print('',flush=True) # flush print, then re-raise
                raise

            if VERBOSE:
                ai.printstate()


        print('\ndone')
