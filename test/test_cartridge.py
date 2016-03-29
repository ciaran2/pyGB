import six
import struct
import unittest

from gb.cartridge import *

class TestCartridgeMeta(unittest.TestCase):

  def setUp(self):
    @six.add_metaclass(CartridgeMeta)
    class base(object):
      pass
    self.base = base

    self.test_romstring = b"\x00" * ROM_TYPE_BYTE + b"\x01"

  def testConstruct(self):
    # These constructions should result in subclass delegation
    dummy_cartridge = Cartridge()
    self.assertIs(type(dummy_cartridge), DummyCartridge)

    mbc1_cartridge = Cartridge(self.test_romstring)
    self.assertIs(type(mbc1_cartridge), Mbc1Cartridge)

    # Ensure that subclasses can still be constructed directly
    DummyCartridge()
    Mbc1Cartridge(self.test_romstring)

    # these constructions are illegal and should fail.
    with self.assertRaises(ValueError):
      Cartridge(b"not long enough")
    with self.assertRaises(ValueError):
      Cartridge(b"\x00" * ROM_TYPE_BYTE + b"\xFF")

  def testIllegalRegistration(self):
    class derived1(self.base):
      ids = [0x0]

    with self.assertRaises(RegistrationError):
      class derived2(self.base):
        ids = [0x0]

  def testRegistration(self):
    class derived1(self.base):
      ids = [0x0]
    self.assertIs(self.base._cartridge_registry[0x0], derived1)

    class derived2(self.base):
      ids = [0x1, 0x2]

    self.assertIs(self.base._cartridge_registry[0x1], derived2)
    self.assertIs(self.base._cartridge_registry[0x1], derived2)

class TestMbc1Cartridge(unittest.TestCase):
  def setUp(self):
    # Use [i + 5] to avoid missed errors from defaulting to zero.
    self.full_cartridge_string = bytearray().join([
      bytearray([i + 5]) * 0x4000 if i not in [32, 64, 96] else bytearray()
      for i in range(128)
    ])
    self.partial_cartridge_string = bytearray().join([
      bytearray([i + 5]) * 0x4000 if i not in [32, 64, 96] else bytearray()
      for i in range(48)
    ])

  def testConstruct(self):
    cart = Mbc1Cartridge(self.full_cartridge_string)
    self.assertEqual(len(cart.rombanks), 128)

    cart = Mbc1Cartridge(self.partial_cartridge_string)
    self.assertEqual(len(cart.rombanks), 128)

  def testReadBanks(self):
    cart = Mbc1Cartridge(self.full_cartridge_string)

    for i in range(0x4000):
      self.assertEqual(cart[i], 5)

    # Test with mode_select = 0
    for i in range(128):
      # Skip the inaccessible banks at 0, 32, 64, 96
      if i % 32 == 0:
        continue
      cart.rom_select = i & 0x1F
      cart.bankset_select = i >> 5

      # Test every 100th byte and the last byte (checking every byte is possible but
      # slower).
      for k in range(0x4000, 0x8000, 0x100):
        self.assertEqual(cart[k], i + 5)
      self.assertEqual(cart[0x7FFF], i + 5)

    cart.mode_select = 1
    for i in range(128):
      # Skip the inaccessible banks at 0, 32, 64, 96
      if i % 32 == 0:
        continue
      cart.rom_select = i & 0x1F
      cart.bankset_select = i >> 5

      # Test every 100th byte and the last byte (checking every byte is possible but
      # slower).
      for k in range(0x4000, 0x8000, 0x100):
        # we should get a different bank from i because the mode select is different.
        self.assertEqual(cart[k], i % 32 + 5)
      self.assertEqual(cart[0x7FFF], i % 32 + 5)

  def testReadRam(self):
    cart = Mbc1Cartridge(self.full_cartridge_string)
    # i + 5 so that we avoid weird errors from, for example, defaulting to zero.
    cart.rambanks = [bytearray([i + 5]) * 8192 for i in range(4)]

    cart.ram_enable = 0xA
    cart.mode_select = 1
    for i in range(4):
      cart.bankset_select = i
      for k in range(0x8000, 0xA000, 0x100):
        self.assertEqual(cart[k], i + 5)
      self.assertEqual(cart[0x9FFF], i + 5)

    # Same test, but with cart mode set to rom.
    cart.mode_select = 0
    for i in range(4):
      cart.bankset_select = i
      for k in range(0x8000, 0xA000, 0x100):
        self.assertEqual(cart[k], 5)
      self.assertEqual(cart[0x9FFF], 5)

    # Repeat again with ram_enable turned off to make sure this is all zero. (This is why
    # we use i+5 in the other tests).
    cart.ram_enable = 0
    cart.mode_select = 1
    for i in range(4):
      cart.bankset_select = i
      for k in range(0x8000, 0xA000, 0x100):
        self.assertEqual(cart[k], 0)
      self.assertEqual(cart[0x9FFF], 0)

    # Same test, but with cart mode set to rom.
    cart.mode_select = 0
    for i in range(4):
      cart.bankset_select = i
      for k in range(0x8000, 0xA000, 0x100):
        self.assertEqual(cart[k], 0)
      self.assertEqual(cart[0x9FFF], 0)

  def testWriteRam(self):
    for enable, select in (
        # Test with ram enabled/disabled and rom select on/off
        (0xA, 1),
        (0, 1),
        (0xA, 0),
        (0, 0)):
      cart = Mbc1Cartridge(self.full_cartridge_string)
      cart.ram_enable = enable
      cart.mode_select = select
      for i in range(4):
        cart.bankset_select = i
        for k in range(0x8000, 0xA000, 0x100):
          cart[k] = i + 5 if select else 5

      for i, bank in enumerate(cart.rambanks):
        for k in range(0, 0x2000, 0x100):
          if enable and (select or i == 0):
            self.assertEqual(bank[k], i + 5)
          else:
            self.assertEqual(bank[k], 0)
          # ensure both that the bank was written and that other slots weren't
          self.assertEqual(bank[k+1], 0)

  def testWriteControls(self):
    for addr, val, ram, rom, bank, mode in (
        # Ram Enable 0-1FFF, mask: F
        (0x0, 0x10, 0x0, 0x1, 0x0, 0x0), # Value outside bitmask
        (0x0, 0x13, 0x3, 0x1, 0x0, 0x0), # Value partially outside bitmask
        (0x0, 0xA, 0xA, 0x1, 0x0, 0x0), # Enable value
        (0x1037, 0xA, 0xA, 0x1, 0x0, 0x0), # At a different address
        (0x1037, 0x4, 0x4, 0x1, 0x0, 0x0), # Setting a different value
        # Rom Select 2000-3FFF, mask: 1F
        (0x2000, 0x2F, 0x0, 0xF, 0x0, 0x0), # Partially outside bitmask
        (0x2000, 0x20, 0x0, 0x1, 0x0, 0x0), # Fully outside bitmask
        (0x2000, 0x9, 0x0, 0x9, 0x0, 0x0), # Valid value
        (0x3498, 0x17, 0x0, 0x17, 0x0, 0x0), # Valid value full width, different address
        (0x2000, 0x0, 0x0, 0x1, 0x0, 0x0), # Setting to zero
        # Bankset Select 4000-5FFF, mask: 3
        (0x4000, 0x4, 0x0, 0x1, 0x0, 0x0), # Outside bitmask
        (0x4000, 0x5, 0x0, 0x1, 0x1, 0x0), # Partially outside bitmask
        (0x4000, 0x2, 0x0, 0x1, 0x2, 0x0), # Valid value
        (0x5836, 0x2, 0x0, 0x1, 0x2, 0x0), # Different address
        # Mode Select 6000-7FFF, mask: 1
        (0x6000, 0x2, 0x0, 0x1, 0x0, 0x0), # Outside bitmask
        (0x6000, 0x3, 0x0, 0x1, 0x0, 0x1), # Partially outside bitmask
        (0x6000, 0x1, 0x0, 0x1, 0x0, 0x1), # Valid value
        (0x7836, 0x1, 0x0, 0x1, 0x0, 0x1)): # Different address
      cart = Mbc1Cartridge(self.full_cartridge_string)
      cart[addr] = val
      self.assertEqual(cart.ram_enable, ram)
      self.assertEqual(cart.rom_select, rom)
      self.assertEqual(cart.bankset_select, bank)
      self.assertEqual(cart.mode_select, mode)
