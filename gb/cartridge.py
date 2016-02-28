import six
from six.moves import xrange

from gb.mem import *

ROM_TYPE_BYTES = 0x147

class CartridgeError(Exception):
  """Base exception for this module."""
  pass

class RegistrationError(CartridgeError):
  """Error raised when a cartridge tries to register itself with an illegal state."""
  pass

class CartridgeMeta(type):
  """Metaclass for cartridges, causing automatic registration of subclasses."""

  def __init__(cls, name, bases, dct):
    """Add a registry to base classes, and register any class that provides "ids"."""
    if not hasattr(cls, '_cartridge_registry'):
      # Add a registry to the class if it doesn't have one. This would imply that it's a
      # base class.
      cls._cartridge_registry = {}
    if hasattr(cls, 'ids'):
      # iterate over the ids presented by the class and register it to each id given.
      for i in cls.ids:
        if i in cls._cartridge_registry:
          raise RegistrationError(
            "Cartridge class %s registers id %x which is already registered by %s" %
            (cls, i, cls._cartridge_registry[i]))
        cls._cartridge_registry[i] = cls

    super(CartridgeMeta, cls).__init__(name, bases, dct)

@six.add_metaclass(CartridgeMeta)
class Cartridge(object):

  def __new__(cls, romstring=b''):
    """Instantiate the appropriate cartridge subtype automatically, given the romstring. If
    the romstring is empty, instantiate a DummyCartridge.

    """
    if cls is Cartridge:
      if not romstring:
        cls = DummyCartridge
      else:
        if len(romstring) < ROM_TYPE_BYTES:
          raise ValueError(
            "Unable to read cartridge type: cartridge type located at byte %d, but "
            "romstring was only %d bytes long." % (ROM_TYPE_BYTES, len(romstring)))
        # 2/3 evil index function which we have to use because Python 2 is evil and has
        # "bytes" as an alias of "str" and indexing a "str" returns a 1 character "str".
        cart_type = six.indexbytes(romstring, ROM_TYPE_BYTES)

        if cart_type in Cartridge._cartridge_registry:
          cls = Cartridge._cartridge_registry[cart_type]
        else:
          raise ValueError("Unsupported Cartridge type.")
    else:
      raise ValueError("You have subclassed Cartridge incorrectly, somehow.")

    return super(Cartridge, cls).__new__(cls)

class DummyCartridge(Cartridge):

  def __init__(self):
    pass

  def __getitem__(self, addr):
    return 0

  def __setitem__(self, addr, value):
    pass


class Mbc1Cartridge(Cartridge):

  ids = [0x1, 0x2, 0x3]

  def __init__(self, romstring):
    self.ram_enable = 0
    self.rom_select = 1
    self.bankset_select = 0
    self.mode_select = 0

    self.rombanks = [Rom(romstring[x:x+0x4000]) for x in xrange(0, len(romstring), 0x4000)]
    self.rombanks.insert(32, self.rombanks[0])
    self.rombanks.insert(64, self.rombanks[0])
    self.rombanks.insert(96, self.rombanks[0])
    if len(self.rombanks) < 128:
      self.rombanks = self.rombanks + [Rom(0x4000)] * (128 - len(self.rombanks))
    self.rambanks = 4 * [bytearray(8192)]

  def __getitem__(self, addr):
    if addr < 0x0 or addr > 0x9FFF:
      raise KeyError("Invalid cartridge memory address.")
    if addr < 0x4000:
      return self.rombanks[0][addr]
    elif addr < 0x8000:
      return self.rombanks[
        self.rom_select + (1-self.mode_select)*(self.bankset_select << 5)][addr-0x4000]
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
    # 2/3: Python 2's "bytes" type is useless, so we have to use a bytearray to get the
    # behavior we want.
    romstring = f.read()

  return Cartridge(romstring)
