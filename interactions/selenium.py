from .base import InteractionBase
from printer import inc_prtlvl, dec_prtlvl, debug, info, warn, error

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains

class InteractionSelenium (InteractionBase):

    ## static

    _TIMEOUT = 15

    ## non-static

    def __init__(self, esfs):
        pass

    def calibration(self) -> None:
        info("Initializing Selenium's Chrome webdriver")
        inc_prtlvl()
        debug("initializing self.b = webdriver.Chrome('./chromedriver')")
        self.b = webdriver.Chrome('./chromedriver')
        debug("navigating to minesweeper.online")
        self.b.get('https://minesweeper.online/')
        dec_prtlvl()

    def _get(self, x, y):
        '''Can throw: selenium.common.exceptions.TimeoutException'''
        return WebDriverWait(self.b, InteractionSelenium._TIMEOUT).until(
            lambda x: x.find_element_by_id('cell_{}_{}'.format(x,y))
        )

    def click(self, x, y) -> None:
        tile = self._get(x, y)
        # tile.click()
        # TODO: make tile get moved into view? (Does ActionChains' move_to_element already do this?)
        ActionChains(self.b).move_to_element(tile).click().perform()

    def mark(self, x, y) -> None:
        tile = self._get(x, y)
        # TODO: make tile get moved into view? (Does ActionChains' move_to_element already do this?)
        ActionChains(self.b).move_to_element(tile).context_click().perform()

    def findout(self, x, y) -> str:
        raise NotImplementedError

    def cleanup(self) -> None:
        self.b.close()
        del self.b