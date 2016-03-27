REG_A = 0b111
REG_B = 0b000
REG_C = 0b001
REG_D = 0b010
REG_E = 0b011
REG_H = 0b100
REG_L = 0b101

class Cpu(object):
  def __init__(self, mmu):
    self.mmu = mmu

    self.pc = 0
    self.sp = 0

    self.gp_regs = {0b111:0, 0b000:0, 0b001:0, 0b010:0, 0b011:0, 0b100:0, 0b101:0}
    self.f = 0

    self.stopped = False
    self.halted = False
    self.interrupts_enabled = False

  def execute_instr(self):
    if (self.halted and self.interrupts_enabled) or self.stopped:
      return

    opcode = self.mmu[self.pc]
    if not self.halted:
      self.pc = (self.pc + 1) % 0x10000

    if opcode == 0x0:
      return

    if opcode == 0x10:
      self.stopped = True
      return

    if opcode == 0x08:
      self.save_sp()
      return

    hi2 = (opcode & 0b11000000) >> 6

    #register loads
    if hi2 == 0b01:
      reg1, reg2 = (opcode & 0xb111000) >> 3, opcode & 0b111
      if reg1 == 0x110 and reg2 == 0x110:
        self.halt()
      else:
        self.load8_reg(reg1, reg2)

    #arithmetic ops
    elif hi2 == 0b10:
      op = (opcode & 0b00111000) >> 3
      self.arithmetic_ops8[op](opcode & 0b111)

    elif hi2 == 0b00:
      lo3 = opcode & 0b111
      if lo3 == 0b100:
        self.inc8((opcode >> 3) & 0b111)
      elif lo3 == 0b101:
        self.dec8((opcode >> 3) & 0b111)
      elif lo3 == 0b110
        self.load8_imm((opcode >> 3) & 0b111)
      elif lo3 == 0b011:
        if (opcode >> 3) & 0b1:
          self.dec16((opcode >> 4) & 0b11)
        else:
          self.inc16((opcode >> 4) & 0b11)
      elif lo3 == 0b001:
        if opcode & 0b1000:
          self.add16((opcode >> 4) & 0b11)
        else:
          self.load16_imm((opcode >> 4) & 0b11)
      elif lo3 == 0b010:
        if opcode & 0b1000:
          self.load_fr_addr((opcode >> 4) & 0b11)
        else:
          self.load_to_addr((opcode >> 4) & 0b11)
      elif lo3 == 0b000:
        
