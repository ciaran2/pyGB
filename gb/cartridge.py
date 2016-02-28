import six
from six.moves import xrange

from gb.mem import *

ROM_TYPE_BYTE = 0x147


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
  """Base class for Cartridges. Calling the Cartridge constructor with a romstring
  automatically constructs the appropriate child class, if a child class exists which has
  the cartridge type id in its "ids" variable.

  """

  def __new__(cls, *args, **kwargs):
    """Instantiate the appropriate cartridge subtype automatically, given the romstring. If
    the romstring is empty, instantiate a DummyCartridge.

    Take *args and **kwargs to allow subclasses to override with different arguments,
    without having to implement New.

    """
    if cls is Cartridge:
      # Use *staring to automatically get arg/kwargs correction.
      return cls._new(*args, **kwargs)
    else:
      # Construct whatever class we were given and return it.
      return super(Cartridge, cls).__new__(cls)

  @classmethod
  def _new(cls, romstring=b""):
    """Implementation of __new__ for when cls is Cartridge. If cls is not cartridge, it means
    that a subclass was being constructed directly. That means that the default operation
    is performed, in __new__.

    """
    assert cls is Cartridge, "Only __new__ should call this!"

    if not romstring:
      cls = DummyCartridge
    else:
      # 2/3: convert to bytearry to ensure uniform indexing. Could also use
      # six.indexbytes, but that doesn't work on existing bytearrays, so we would still
      # need a conversion, and we might as well use python builtins if we can.
      romstring = bytearray(romstring)
      if len(romstring) < ROM_TYPE_BYTE:
        raise ValueError(
          "Unable to read cartridge type: cartridge type located at byte %d, but "
          "romstring was only %d bytes long." % (ROM_TYPE_BYTE, len(romstring)))
      cart_type = romstring[ROM_TYPE_BYTE]

      if cart_type in Cartridge._cartridge_registry:
        cls = Cartridge._cartridge_registry[cart_type]
      else:
        raise ValueError("Unsupported Cartridge type.")

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

    # Note(zstewar1): This is how I think this works: there are 128 rom banks. All four of
    # the banks that would be accessible with rom_select = 0, regardless of
    # bankset_select, are mapped to the fixed (zeroth) rom bank. Instead, rom_select = 0
    # becomes rom_select = 1, and the fixed rom is only accessible from address 0x4000 and
    # the rest are only accessible from 0x8000.
    #
    # So here we load all of the rom banks from a file and insert them into a list. Then
    # Then we fill out the list with empty rom banks until it's 125 banks long. Then we
    # fill in the remaining three spaces by re-inserting bank 0
    #
    # This assumes that the romstring *does not* already contain data in the sections for
    # the repeated bank 0.
    self.rombanks = [
      Rom(romstring[x:x+0x4000]) for x in xrange(0, len(romstring), 0x4000)]
    if len(self.rombanks) < 125:
      self.rombanks = self.rombanks + [Rom()] * (125 - len(self.rombanks))
    # Insert the fixed bank into appropriate indices in the rombank. Note: Not sure if the
    # cartridge file already contains these repeated chunks or not.
    self.rombanks.insert(32, self.fixedbank)
    self.rombanks.insert(64, self.fixedbank)
    self.rombanks.insert(96, self.fixedbank)
    self.rambanks = [bytearray(8192) for _ in range(4)]

  @property
  def fixedbank(self):
    """Property for the fixed rom bank, to clarify intent -- compare `self.rombanks[0]` to
    `self.fixedbank`.

    """
    return self.rombanks[0]

  @property
  def rom_bank(self):
    rom_bank = self.rom_select
    if not self.mode_select:
      # Note: should the bankset actually get sent back to 0 when the mode is set to ram?
      # In the example code at github.com/Two9A/jsGB, the bank stays wherever it was set
      # previously, though that may be incorrect behavior.
      rom_bank |= self.bankset_select << 5
    return rom_bank

  @property
  def ram_bank(self):
    if self.mode_select:
      # Note: in the example code at github.com/Two9A/jsGB, the ram bank stays wherever it
      # was set perviously and does not return to bank zero when mode is changed to
      # rom. Not sure if that is correct behavior, so will retain this behavior for now.
      return self.bankset_select
    return 0

  def __getitem__(self, addr):
    if addr < 0x0 or addr > 0x9FFF:
      raise KeyError("Invalid cartridge memory address.")
    if addr < 0x4000:
      return self.fixedbank[addr]
    elif addr < 0x8000:
      return self.rombanks[self.rom_bank][addr-0x4000]
    elif self.ram_enable == 0xA:
      return self.rambanks[self.ram_bank][addr-0x8000]
    else:
      return 0

  def __setitem__(self, addr, value):
    if addr < 0x0 or addr > 0x9FFF:
      raise KeyError("Invalid cartridge memory address.")
    if addr < 0x2000:
      self.ram_enable = 0x0F & value
    elif addr < 0x4000:
      self.rom_select = 0x1F & value
      if not self.rom_select:
        self.rom_select = 1
    elif addr < 0x6000:
      self.bankset_select = 0x3 & value
    elif addr < 0x8000:
      self.mode_select = 0x1 & value
    elif self.ram_enable == 0xA:
      self.rambanks[self.ram_bank][addr-0x8000] = value

def load_rom_from_file(path):
  with open(path, "rb") as f:
    romstring = f.read()

  return Cartridge(romstring)
