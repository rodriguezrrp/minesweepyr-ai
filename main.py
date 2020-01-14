from driver import Driver
from interactions.selenium import InteractionSelenium

if __name__ == "__main__":

    ## Initialize the driver
    _interactor = InteractionSelenium()
    driver = Driver(_interactor)

    ## GO TIME! :D
    driver.play()