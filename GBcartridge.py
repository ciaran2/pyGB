from GBmem import *

class DummyCartridge:

  def __init__(self):
    pass

  def __getitem__(self, addr):
    return 0

  def __setitem__(self, addr, value):
    pass


class MBC1Cartridge:

  ids = set(['\x01','\x02','\x03'])

  def __init__(self, romstring):
    self.ram_enable = 0
    self.rom_select = 1
    self.bankset_select = 0
    self.mode_select = 0

    self.rombanks = [ROM(romstring[x:x+0x4000]) for x in xrange(0, len(romstring), 0x4000)]
    self.rombanks.insert(32, self.rombanks[0])
    self.rombanks.insert(64, self.rombanks[0])
    self.rombanks.insert(96, self.rombanks[0])
    if len(self.rombanks) < 128:
      self.rombanks = self.rombanks + [ROM(0x4000)] * (128 - len(self.rombanks))
    self.rambanks = 4 * [bytearray(8192)]

  def __getitem__(self, addr):
    if addr < 0x0 or addr > 0x9FFF:
      raise KeyError("Invalid cartridge memory address.")
    if addr < 0x4000:
      return self.rombanks[0][addr]
    elif addr < 0x8000:
      return self.rombanks[self.rom_select + (1-self.mode_select)*(self.bankset_select << 5)][addr-0x4000]
    elif self.ram_enable == 0xA:
        return self.rambanks[self.mode_select * self.bankset_select][addr-0x8000]

  def __setitem__(self, addr, value):
    if addr < 0x0 or addr > 0x9FFF:
      raise KeyError("Invalid cartridge memory address.")
    if addr < 0x2000:
      self.ram_enable = 0xF & value
    elif addr < 0x4000:
      self.rom_select = 0x1F & value
      self.rom_select = 1 if self.rom_select == 0 else self.rom_select
    elif addr < 0x6000:
      self.bankset_select = 0x3 & value
    elif addr < 0x8000:
      self.mode_select = 0x1 & value
    elif self.ram_enable == 0xA:
      self.rambanks[self.mode_select * self.bankset_select][addr-0x8000] = value

def load_rom_from_file(path):
  with open(path, "rb") as f:
    romstring = f.read()

  cart_type = romstring[0x147]

  if cart_type in MBC1Cartridge.ids:
    return MBC1Cartridge(romstring)
  else:
    raise ValueError("Cartridge of unsupported type.")
