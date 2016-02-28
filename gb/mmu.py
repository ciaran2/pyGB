from gb.mem import *
from gb.cartridge import *


class Mmu(object):
  def __init__(self, bios, vram, oam, io):
    self.wram = bytearray(0xE000 - 0xC000)
    self.zram = bytearray(0x10000 - 0xFF80)

    self.bios = bios
    self.vram = vram
    self.oam = oam
    self.io = io

    self.cartridge = Cartridge()

    self.in_bios = True

  def addr_trans(self, addr):
    if addr < 0x0000 or addr > 0xFFFF:
      raise KeyError("Invalid memory address")

    dig1 = addr & 0xF000

    if dig1 < 0x1000:
      if self.in_bios:
        if addr < 0x0100:
          return self.bios, addr
        elif addr == 0x0100:
          self.in_bios = False

      return self.cartridge, addr

    if dig1 < 0x4000:
      return self.cartridge, addr

    if dig1 < 0x8000:
      return self.cartridge, addr

    if dig1 < 0xA000:
      return self.vram, (addr - 0x8000)

    if dig1 < 0xC000:
      return self.cartridge, (addr - 0xA000 + 0x8000)

    if dig1 < 0xF000:
      return self.wram, (addr - 0xC000)

    else:
      dig2 = addr & 0x0F00

      if dig2 < 0xE00:
        return self.wram, (addr - 0xF000)

      elif dig2 == 0xE00:
        return self.oam, (addr - 0xFE00)

      else:
        if addr >= 0xFF80:
          return self.zram, (addr - 0xFF80)
        else:
          return self.io, (addr - 0xFF00)

  def __getitem__(self, addr):
    device, device_addr = self.addr_trans(addr)
    return device[device_addr]

  def __setitem__(self, addr, value):
    self.addr_trans(addr)[addr] = value

  def reset(self):
    self.wram.clear()
    self.zram.clear()

    self.vram.clear()
    self.oam.clear()

    self.cartridge.eram.clear()

  def load_cartridge(self, cartridge):
    self.cartridge = cartridge

  def unload_cartridge(self, cartridge):
    self.cartridge = Cartridge()
