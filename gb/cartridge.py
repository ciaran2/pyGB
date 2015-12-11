from gb.mem import *

class DummyCartridge:

  def __init__(this):
    this.rom0 = DummyMem()
    this.rom1 = DummyMem()
    this.eram = DummyMem()
