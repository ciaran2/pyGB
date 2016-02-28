import six
import unittest

from gb.cartridge import *

class TestCartridge(unittest.TestCase):

    def setUp(self):
        @six.add_metaclass(CartridgeMeta)
        class base(object):
            pass
        self.base = base

        self.test_romstring = b"\x00" * 0x147 + b"\x01"

    def testCartridgeSelect(self):
        dummy_cartridge = Cartridge()
        self.assertIs(type(dummy_cartridge), DummyCartridge)

        mcb1_cartridge = Cartridge(self.test_romstring)
        self.assertIs(type(mcb1_cartridge), Mbc1Cartridge)

    def testConstructIllegal(self):
        with self.assertRaises(ValueError):
            Cartridge(b"not long enough")
        with self.assertRaises(ValueError):
            Cartridge(b"\x00" * 0x147 + b"\xFF")
        with self.assertRaises(ValueError):
            DummyCartridge()

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
