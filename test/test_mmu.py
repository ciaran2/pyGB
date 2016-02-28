import unittest

from gb.mem import *
from gb.mmu import *

class TestMmuMethods(unittest.TestCase):

  def setUp(self):
    self.mmu = Mmu(DummyMem(), DummyMem(), DummyMem(), DummyMem())

  def tearDown(self):
    self.mmu = None

  def test_read_bios(self):
    b1 = self.mmu.addr_trans(0x0)[0]
    b2 = self.mmu.addr_trans(0xEE)[0]

    self.assertEqual(b1, b2)

  def test_bios_end(self):
    b1 = self.mmu.addr_trans(0x0)[0]
    b2 = self.mmu.addr_trans(0x100)[0]

    self.assertNotEqual(b1, b2)

  def test_unload_bios(self):
    b1 = self.mmu.addr_trans(0x100)[0]
    b2 = self.mmu.addr_trans(0x0)[0]

    self.assertEqual(b1, b2)

  def test_read_devices(self):
    self.mmu.addr_trans(0x100)

    bank0 = self.mmu.addr_trans(0x100)[0]
    bank0_0 = self.mmu.addr_trans(0x0)[0]
    bank0_1 = self.mmu.addr_trans(0x3FFF)[0]

    self.assertEqual(bank0, bank0_0)
    self.assertEqual(bank0, bank0_1)

    bank1_0 = self.mmu.addr_trans(0x4000)[0]
    bank1_1 = self.mmu.addr_trans(0x7000)[0]

    self.assertEqual(bank1_0, bank1_1)
    self.assertEqual(bank1_0, bank0)

    vram1 = self.mmu.addr_trans(0x8000)[0]
    vram2 = self.mmu.addr_trans(0x9000)[0]

    self.assertEqual(vram1, vram2)
    self.assertNotEqual(vram1, bank0)
    self.assertNotEqual(vram1, bank1_0)

    eram1 = self.mmu.addr_trans(0xA000)[0]
    eram2 = self.mmu.addr_trans(0xB000)[0]

    self.assertEqual(eram1, eram2)
    self.assertEqual(eram1, bank0)
    self.assertEqual(eram1, bank1_0)
    self.assertNotEqual(eram1, vram1)

    wram1 = self.mmu.addr_trans(0xC000)[0]
    wram2 = self.mmu.addr_trans(0xD000)[0]
    wram3 = self.mmu.addr_trans(0xE000)[0]
    wram4 = self.mmu.addr_trans(0xF000)[0]

    self.assertEqual(wram1, wram2)
    self.assertEqual(wram1, wram3)
    self.assertEqual(wram1, wram4)

    self.assertNotEqual(wram1, bank0)
    self.assertNotEqual(wram1, bank1_0)
    self.assertNotEqual(wram1, vram1)
    self.assertNotEqual(wram1, eram1)

    oam1 = self.mmu.addr_trans(0xFE00)[0]
    oam2 = self.mmu.addr_trans(0xFE90)[0]

    self.assertEqual(oam1, oam2)

    self.assertNotEqual(oam1, bank0)
    self.assertNotEqual(oam1, bank1_0)
    self.assertNotEqual(oam1, vram1)
    self.assertNotEqual(oam1, eram1)
    self.assertNotEqual(oam1, wram1)

    io1 = self.mmu.addr_trans(0xFF00)[0]
    io2 = self.mmu.addr_trans(0xFF7F)[0]

    self.assertEqual(io1, io2)

    self.assertNotEqual(io1, bank0)
    self.assertNotEqual(io1, bank1_0)
    self.assertNotEqual(io1, vram1)
    self.assertNotEqual(io1, eram1)
    self.assertNotEqual(io1, wram1)
    self.assertNotEqual(io1, oam1)

    zram1 = self.mmu.addr_trans(0xFF80)[0]
    zram2 = self.mmu.addr_trans(0xFFFF)[0]

    self.assertEqual(zram1, zram2)

    self.assertNotEqual(zram1, bank0)
    self.assertNotEqual(zram1, bank1_0)
    self.assertNotEqual(zram1, vram1)
    self.assertNotEqual(zram1, eram1)
    self.assertNotEqual(zram1, wram1)
    self.assertNotEqual(zram1, oam1)
    self.assertNotEqual(zram1, io1)
