import unittest

from gb.mmu import *

class TestMmuMethods(unittest.TestCase):

  def setUp(this):
    this.mmu = Mmu(DummyMem(), DummyMem(), DummyMem(), DummyMem())

  def tearDown(this):
    this.mmu = None

  def test_read_bios(this):
    b1 = this.mmu.device_select(0x0)
    b2 = this.mmu.device_select(0xEE)

    this.assertEqual(b1, b2)

  def test_bios_end(this):
    b1 = this.mmu.device_select(0x0)
    b2 = this.mmu.device_select(0x100)

    this.assertNotEqual(b1, b2)

  def test_unloda_bios(this):
    b1 = this.mmu.device_select(0x100)
    b2 = this.mmu.device_select(0x0)

    this.assertEqual(b1, b2)

  def test_read_devices(this):
    this.mmu.device_select(0x100)

    bank0 = this.mmu.device_select(0x100)
    bank0_0 = this.mmu.device_select(0x0)
    bank0_1 = this.mmu.device_select(0x3FFF)

    this.assertEqual(bank0, bank0_0)
    this.assertEqual(bank0, bank0_1)

    bank1_0 = this.mmu.device_select(0x4000)
    bank1_1 = this.mmu.device_select(0x7000)

    this.assertEqual(bank1_0, bank1_1)
    this.assertNotEqual(bank1_0, bank0)

    vram1 = this.mmu.device_select(0x8000)
    vram2 = this.mmu.device_select(0x9000)

    this.assertEqual(vram1, vram2)
    this.assertNotEqual(vram1, bank0)
    this.assertNotEqual(vram1, bank1_0)

    eram1 = this.mmu.device_select(0xA000)
    eram2 = this.mmu.device_select(0xB000)

    this.assertEqual(eram1, eram2)
    this.assertNotEqual(eram1, bank0)
    this.assertNotEqual(eram1, bank1_0)
    this.assertNotEqual(eram1, vram1)

    wram1 = this.mmu.device_select(0xC000)
    wram2 = this.mmu.device_select(0xD000)
    wram3 = this.mmu.device_select(0xE000)
    wram4 = this.mmu.device_select(0xF000)

    this.assertEqual(wram1, wram2)
    this.assertEqual(wram1, wram3)
    this.assertEqual(wram1, wram4)

    this.assertNotEqual(wram1, bank0)
    this.assertNotEqual(wram1, bank1_0)
    this.assertNotEqual(wram1, vram1)
    this.assertNotEqual(wram1, eram1)

    oam1 = this.mmu.device_select(0xFE00)
    oam2 = this.mmu.device_select(0xFE90)

    this.assertEqual(oam1, oam2)

    this.assertNotEqual(oam1, bank0)
    this.assertNotEqual(oam1, bank1_0)
    this.assertNotEqual(oam1, vram1)
    this.assertNotEqual(oam1, eram1)
    this.assertNotEqual(oam1, wram1)

    io1 = this.mmu.device_select(0xFF00)
    io2 = this.mmu.device_select(0xFF7F)

    this.assertEqual(io1, io2)

    this.assertNotEqual(io1, bank0)
    this.assertNotEqual(io1, bank1_0)
    this.assertNotEqual(io1, vram1)
    this.assertNotEqual(io1, eram1)
    this.assertNotEqual(io1, wram1)
    this.assertNotEqual(io1, oam1)

    zram1 = this.mmu.device_select(0xFF80)
    zram2 = this.mmu.device_select(0xFFFF)

    this.assertEqual(zram1, zram2)

    this.assertNotEqual(zram1, bank0)
    this.assertNotEqual(zram1, bank1_0)
    this.assertNotEqual(zram1, vram1)
    this.assertNotEqual(zram1, eram1)
    this.assertNotEqual(zram1, wram1)
    this.assertNotEqual(zram1, oam1)
    this.assertNotEqual(zram1, io1)
