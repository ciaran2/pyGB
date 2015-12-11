from gb.mem import *
from gb.cartridge import *

class Mmu:
  def __init__(this, bios, vram, oam, io):
    this.wram = RAM(0xDFFF, 0xC000)
    this.zram = RAM(0xFFFF, 0xFF80)

    this.bios = bios
    this.vram = vram
    this.oam = oam
    this.io = io

    this.cartridge = DummyCartridge()

    this.in_bios = True

  def device_select(this, addr):
    if addr < 0x0000 or addr > 0xFFFF:
      raise KeyError("Invalid memory address")

    dig1 = addr & 0xF000

    if dig1 == 0x0000:
      if this.in_bios:
        if addr < 0x0100:
          return this.bios
        elif addr == 0x0100:
          this.in_bios = False

      return this.cartridge.rom0

    if dig1 >= 0x1000 and dig1 <= 0x3000:
      return this.cartridge.rom0

    if dig1 >= 0x4000 and dig1 <= 0x7000:
      return this.cartridge.rom1

    if dig1 >= 0x8000 and dig1 <= 0x9000:
      return this.vram

    if dig1 >= 0xA000 and dig1 <= 0xB000:
      return this.cartridge.eram

    if dig1 >= 0xC000 and dig1 <= 0xE000:
      return this.wram

    if dig1 == 0xF000:
      dig2 = addr & 0x0F00

      if dig2 >= 0x000 and dig2 <= 0xD00:
        return this.wram

      if dig2 == 0xE00:
        return this.oam

      if dig2 == 0xF00:
        if addr >= 0xFF80:
          return this.zram
        else:
          return this.io

  def __getitem__(this, addr):
    return this.device_select(addr)[addr]

  def __setitem__(this, addr, value):
    this.device_select(addr)[addr] = value

  def reset(this):
    this.wram.clear()
    this.zram.clear()

    this.vram.clear()
    this.oam.clear()

    this.cartridge.eram.clear()

  def load_cartridge(this, cartridge):
    this.cartridge = cartridge

  def unload_cartridge(this, cartridge):
    this.cartridge = DummyCartridge()