from typing import List
from operator import itemgetter
from pprint import pformat
import time

from .base import InteractionBase
from printer import inc_prtlvl, dec_prtlvl, debug, info, warn, error
import labeling
from chunky import chunks

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains

class InteractionSelenium (InteractionBase):

    ## static

    _TIMEOUT = 15

    ## non-static

    def __init__(self, dologin: bool = False):
        pass

    def calibration(self) -> None:
        info("Initializing Selenium's Chrome webdriver")
        inc_prtlvl()
        debug("initializing self.b = webdriver.Chrome(...)")
        self.b = webdriver.Chrome('./interactions/chromedriver')
        self.b.set_window_size(300,700)
        debug("navigating to minesweeper.online")
        self.b.get('https://minesweeper.online/')
        dec_prtlvl()

    @staticmethod
    def _classes_to_tile(classstring):
        tile = "" #type: str
        # parse classstring into tile
        if('hd_closed' in classstring):
            if('hd_flag' in classstring):
                tile = labeling.FLAG
            else:
                tile = labeling.BLANK
        elif('hd_opened' in classstring):
            types = [
                (0, labeling.EMPTY),
                (1, labeling.DIGIT_1),
                (2, labeling.DIGIT_2),
                (3, labeling.DIGIT_3),
                (4, labeling.DIGIT_4),
                (5, labeling.DIGIT_5),
                (6, labeling.DIGIT_6),
                (7, labeling.DIGIT_7),
                (8, labeling.DIGIT_8),
                (10, labeling.EXPLODED),
                (11, labeling.EXPLODED)
            ]
            for typenum, typetile in types:
                if('hd_type{}'.format(typenum) in classstring):
                    tile = typetile
        # return tile
        if tile == "":
            raise RuntimeError('classstring "{}" could not be parsed into a tile!'.format(classstring))
        debug(inc=True, dec=True, msg='class="{}" -> tile="{}"'.format(classstring, tile))
        return tile

    def get_grid(self) -> List[List[str]]:
        info('getting grid... ', end='')
        # cellelems = self.b.find_elements_by_xpath('//*[@id="A4"]/div[contains(@id,"cell")]')
        cellelems = WebDriverWait(self.b, InteractionSelenium._TIMEOUT).until(
            lambda x: x.find_element_by_xpath('//*[@id="A4"]')
        ).find_elements_by_xpath('./div[contains(@id,"cell")]')
        cells = []
        biggestx: int = 0
        biggesty: int = 0
        for c in cellelems:
            cid = c.get_attribute("id")
            cl = c.get_attribute("class")
            _, cx, cy = cid.split("_")
            cx = int(cx); cy = int(cy)
            if cx > biggestx: biggestx = cx
            if cy > biggesty: biggesty = cy
            cells.append( (cx, cy, cl) )
        cells.sort(key=itemgetter(1,0)) # sort based on y first, then x
        #chunk the cells into sublists of the y; therefore, each sublist is a row
        grid = list(chunks(cells, biggestx+1)) #type: List[List[str]]
        debug(inc=True, dec=True, msg='') # take care of info's end='' above
        debug(inc=True, dec=True, msg='preprocessed grid = \n'+pformat(grid))
        for cell in cells:
            classes = cell[2]
            tile = InteractionSelenium._classes_to_tile(classes)
            grid[cell[1]][cell[0]] = tile
        debug(inc=True, dec=True, msg='postprocessed grid = \n'+pformat(grid))
        info('grid got!')
        return grid

    def _get(self, x, y):
        '''Can raise: selenium.common.exceptions.TimeoutException'''
        return WebDriverWait(self.b, InteractionSelenium._TIMEOUT).until(
            lambda b: b.find_element_by_id('cell_{}_{}'.format(x,y))
        )

    def click(self, x, y) -> None:
        # tile = self._get(x, y)
        # tile.click()
        # TODO: make tile get moved into view? (Does ActionChains' move_to_element already do this?)
        ActionChains(self.b).move_to_element(self._get(x, y)).click().perform()
        time.sleep(0.3) #FIXME: this is to wait out the "refreshing of the screen" that minesweeper.online does!

    def mark(self, x, y) -> None:
        # tile = self._get(x, y)
        # TODO: make tile get moved into view? (Does ActionChains' move_to_element already do this?)
        ActionChains(self.b).move_to_element(self._get(x, y)).context_click().perform()

    def findout(self, x, y) -> str:
        # tile = self._get(x, y)
        return InteractionSelenium._classes_to_tile(self._get(x, y).get_attribute("class"))

    def cleanup(self) -> None:
        self.b.close()
        del self.b