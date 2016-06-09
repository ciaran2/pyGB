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

    ops = { 0x00: self.nop,
            0x10: self.stop,
            0x76: self.halt,
            0xCB: self.ext,
            #set up A for BCD, whatever that entails
            0x27: self.daa,
            #set the carry flag (why?)
            0x37: self.scf,
            #complement the carry flag (again, I ask, why?)
            0x3F: self.ccf,
            0x2F: self.cpl,
            #enable/disable interrupts
            0xF3: self.int_switch, 0xFB: self.int_switch,
            #shift ops
            0x07: self.rlca,
            0x17: self.rla,
            0x0F: self.rrca,
            0x1f: self.rra,
            #8-bit immediate loads
            0x06: self.load8_imm, 0x16: self.load8_imm, 0x26: self.load8_imm, 
              0x36: self.load_imm, 0x0E: self.load8_imm, 0x1E: self.load8_imm,
              0x2E: self.load8_imm, 0x3E: self.load8_imm, 
            #16-bit immediate loads
            0x01: self.load16_imm, 0x11: self.load16_imm, 0x21: self.load16_imm,
              0x31: self.load16_imm,
            #8-bit register loads
            0x40: self.load8_reg, 0x41: self.load8_reg, 0x42: self.load8_reg, 
              0x43: self.load8_reg, 0x44: self.load8_reg, 0x45: self.load8_reg, 
              0x46: self.load8_reg, 0x47: self.load8_reg, 0x48: self.load8_reg, 
              0x49: self.load8_reg, 0x4A: self.load8_reg, 0x4B: self.load8_reg, 
              0x4C: self.load8_reg, 0x4D: self.load8_reg, 0x4E: self.load8_reg, 
              0x4F: self.load8_reg, 0x50: self.load8_reg, 0x51: self.load8_reg, 
              0x52: self.load8_reg, 0x53: self.load8_reg, 0x54: self.load8_reg, 
              0x55: self.load8_reg, 0x56: self.load8_reg, 0x57: self.load8_reg, 
              0x58: self.load8_reg, 0x59: self.load8_reg, 0x5A: self.load8_reg, 
              0x5B: self.load8_reg, 0x5C: self.load8_reg, 0x5D: self.load8_reg, 
              0x5E: self.load8_reg, 0x5F: self.load8_reg, 0x60: self.load8_reg, 
              0x61: self.load8_reg, 0x62: self.load8_reg, 0x63: self.load8_reg, 
              0x64: self.load8_reg, 0x65: self.load8_reg, 0x66: self.load8_reg, 
              0x67: self.load8_reg, 0x68: self.load8_reg, 0x69: self.load8_reg, 
              0x6A: self.load8_reg, 0x6B: self.load8_reg, 0x6C: self.load8_reg, 
              0x6D: self.load8_reg, 0x6E: self.load8_reg, 0x6F: self.load8_reg, 
              0x70: self.load8_reg, 0x71: self.load8_reg, 0x72: self.load8_reg, 
              0x73: self.load8_reg, 0x74: self.load8_reg, 0x75: self.load8_reg, 
              0x77: self.load8_reg, 0x78: self.load8_reg, 0x79: self.load8_reg, 
              0x7A: self.load8_reg, 0x7B: self.load8_reg, 0x7C: self.load8_reg, 
              0x7D: self.load8_reg, 0x7E: self.load8_reg, 0x7F: self.load8_reg,
            #Memory loads from/to non HL addresses
            0x02: self.load_to_mem, 0x12: self.load_to_mem,
            0x0A: self.load_fr_mem, 0x1A: self.load_fr_mem,
            #HL loads with inc/dec
            0x22: self.ldi_to, 0x32: self.ldd_to,
            0x2A: self.ldi_fr, 0x3A: self.ldd_fr,
            #Loads to/from the upper half of memory
            0xE0: self.ldh_imm_to, 0xF0: self.ldh_imm_fr, 0xE2: self.ldh_c,
            #Loads to/from immediate memory addresses
            0xEA: self.load_imm_to, 0xFA: self.load_imm_fr,
            #Dump HL to SP
            0xF9: self.load_to_sp,
            #Save offset from SP
            0xF8: self.load_sp_with_offset,
            #Save SP to memory
            0x08: self.load_sp_to_mem,
            #ARITHMETIC OPS
            #16-bit increments
            0x03: self.inc16, 0x13: self.inc16, 0x23: self.inc16, 0x33: self.inc16,
            #16-bit decrements
            0x0B: self.dec16, 0x1B: self.dec16, 0x2B: self.dec16, 0x3B: self.dec16,
            #8-bit increments
            0x04: self.inc8, 0x14: self.inc8, 0x24: self.inc8, 0x34: self.inc8,
              0x0C: self.inc8, 0x1C: self.inc8, 0x2C: self.inc8, 0x3C: self.inc8,
            #8-bit decrements
            0x50: self.dec8, 0x51: self.dec8, 0x52: self.dec8, 0x53: self.dec8,
              0x0D: self.dec8, 0x1D: self.dec8, 0x2D: self.dec8, 0x3D: self.dec8,
            #8-bit add
            0x80: self.add8, 0x81: self.add8, 0x82: self.add8, 0x83: self.add8,
              0x84: self.add8, 0x85: self.add8, 0x86: self.add8, 0x87: self.add8,
            #8-bit add w/ carry
            0x88: self.adc8, 0x89: self.adc8, 0x8A: self.adc8, 0x8B: self.adc8,
              0x8C: self.adc8, 0x8D: self.adc8, 0x8E: self.adc8, 0x8F: self.adc8, 
            #8-bit subtract
            0x90: self.sub8, 0x91: self.sub8, 0x92: self.sub8, 0x93: self.sub8,
              0x94: self.sub8, 0x95: self.sub8, 0x96: self.sub8, 0x97: self.sub8,
            #8-bit subtract w/ carry
            0x98: self.sbc8, 0x99: self.sbc8, 0x9A: self.sbc8, 0x9B: self.sbc8,
              0x9C: self.sbc8, 0x9D: self.sbc8, 0x9E: self.sbc8, 0x9F: self.sbc8, 
            #8-bit and
            0xA0: self.and8, 0xA1: self.and8, 0xA2: self.and8, 0xA3: self.and8,
              0xA4: self.and8, 0xA5: self.and8, 0xA6: self.and8, 0xA7: self.and8,
            #8-bit xor
            0xA8: self.xor8, 0xA9: self.xor8, 0xAA: self.xor8, 0xAB: self.xor8,
              0xAC: self.xor8, 0xAD: self.xor8, 0xAE: self.xor8, 0xAF: self.xor8, 
            #8-bit or
            0xB0: self.or8, 0xB1: self.or8, 0xB2: self.or8, 0xB3: self.or8,
              0xB4: self.or8, 0xB5: self.or8, 0xB6: self.or8, 0xB7: self.or8,
            #8-bit compare
            0xB8: self.cp8, 0xB9: self.cp8, 0xBA: self.cp8, 0xBB: self.cp8,
              0xBC: self.cp8, 0xBD: self.cp8, 0xBE: self.cp8, 0xBF: self.cp8, 
            #8-bit immediate arithmetic
            0xC6: self.add8_imm, 0xD6: self.sub8_imm, 0xE6: self.and8_imm,
              0xF6: self.or8_imm, 0xCE: self.adc8_imm, 0xDE: self.sbc_imm,
              0xEE: self.xor8_imm, 0xFE: self.cp8_imm,
            #STACK OPS AND BRANCHES
            #Push
            0xC5: self.push, 0xD5: self.push, 0xE5: self.push, 0xF5: self.push,
            #Pop
            0xC1: self.pop, 0xD1: self.pop, 0xE1: self.pop, 0xF1: self.pop,
            #Fixed location calls
            0xC7: self.rst, 0xCF: self.rst, 0xD7: self.rst, 0xDF: self.rst,
              0xE7: self.rst, 0xEF: self.rst, 0xF7: self.rst, 0xFF: self.rst,
            #Variable location calls
            0xC4: self.callnz, 0xD4: self.callnc, 0xCC: self.callz, 0xDC: callc,
              0xCD: self.call,
            #Returns
            0xC0: self.retnz, 0xD0: self.retnc, 0xC8: self.retz, 0xD8: self.retc,
              0xC9: self.ret, 0xD9: self.reti,
            #Relative jumps
            0x20: self.jrnz, 0x30: self.jrnc, 0x18: self.jr, 0x28: self.jrz,
              0x38: self.jrc,
            #Garbage instructions
            0xF2:self.ill, 0xD3: self.ill, 0xE3: self.ill, 0xE4: self.ill,
              0xF4: self.ill, 0xDB: self.ill, 0xEB: self.ill, 0xEC: self.ill,
              0xFC: self.ill, 0xDD: self.ill, 0xED: self.ill, 0xFD: self.ill 
          }
    self.ext_ops = { 0x00: self.rlc, 0x01: self.rlc, 0x02: self.rlc, 0x03: self.rlc, 
              0x04: self.rlc, 0x05: self.rlc, 0x06: self.rlc, 0x07: self.rlc, 
              #rotate right w/ carry
              0x08: self.rrc, 0x09: self.rrc, 0x0A: self.rrc, 0x0B: self.rrc, 
              0x0C: self.rrc, 0x0D: self.rrc, 0x0E: self.rrc, 0x0F: self.rrc, 
              #rotate left
              0x10: self.rlc, 0x11: self.rlc, 0x12: self.rlc, 0x13: self.rlc, 
              0x14: self.rlc, 0x15: self.rlc, 0x16: self.rlc, 0x17: self.rlc, 
              #rotate right
              0x18: self.rrc, 0x19: self.rrc, 0x1A: self.rrc, 0x1B: self.rrc, 
              0x1C: self.rrc, 0x1D: self.rrc, 0x1E: self.rrc, 0x1F: self.rrc, 
              #shift left
              0x20: self.sla, 0x21: self.sla, 0x22: self.sla, 0x23: self.sla, 
              0x24: self.sla, 0x25: self.sla, 0x26: self.sla, 0x27: self.sla, 
              #shift right
              0x28: self.sra, 0x29: self.sra, 0x2A: self.sra, 0x2B: self.sra, 
              0x2C: self.sra, 0x2D: self.sra, 0x2E: self.sra, 0x2F: self.sra, 
              #swap nybbles
              0x30: self.swap, 0x31: self.swap, 0x32: self.swap, 0x33: self.swap, 
              0x34: self.swap, 0x35: self.swap, 0x36: self.swap, 0x37: self.swap, 
              #shift right without preserving sign
              0x38: self.srl, 0x39: self.srl, 0x3A: self.srl, 0x3B: self.srl, 
              0x3C: self.srl, 0x3D: self.srl, 0x3E: self.srl, 0x3F: self.srl, 
              #test nth bit
              0x40: self.bit, 0x41: self.bit, 0x42: self.bit, 0x43: self.bit, 
              0x44: self.bit, 0x45: self.bit, 0x46: self.bit, 0x47: self.bit, 
              0x48: self.bit, 0x49: self.bit, 0x4A: self.bit, 0x4B: self.bit, 
              0x4C: self.bit, 0x4D: self.bit, 0x4E: self.bit, 0x4F: self.bit, 
              0x50: self.bit, 0x51: self.bit, 0x52: self.bit, 0x53: self.bit, 
              0x54: self.bit, 0x55: self.bit, 0x56: self.bit, 0x57: self.bit, 
              0x58: self.bit, 0x59: self.bit, 0x5A: self.bit, 0x5B: self.bit, 
              0x5C: self.bit, 0x5D: self.bit, 0x5E: self.bit, 0x5F: self.bit, 
              0x60: self.bit, 0x61: self.bit, 0x62: self.bit, 0x63: self.bit, 
              0x64: self.bit, 0x65: self.bit, 0x66: self.bit, 0x67: self.bit, 
              0x68: self.bit, 0x69: self.bit, 0x6A: self.bit, 0x6B: self.bit, 
              0x6C: self.bit, 0x6D: self.bit, 0x6E: self.bit, 0x6F: self.bit, 
              0x70: self.bit, 0x71: self.bit, 0x72: self.bit, 0x73: self.bit, 
              0x74: self.bit, 0x75: self.bit, 0x76: self.bit, 0x77: self.bit, 
              0x78: self.bit, 0x79: self.bit, 0x7A: self.bit, 0x7B: self.bit, 
              0x7C: self.bit, 0x7D: self.bit, 0x7E: self.bit, 0x7F: self.bit, 
              #clear nth bit
              0x80: self.res, 0x81: self.res, 0x82: self.res, 0x83: self.res, 
              0x84: self.res, 0x85: self.res, 0x86: self.res, 0x87: self.res, 
              0x88: self.res, 0x89: self.res, 0x8A: self.res, 0x8B: self.res, 
              0x8C: self.res, 0x8D: self.res, 0x8E: self.res, 0x8F: self.res, 
              0x90: self.res, 0x91: self.res, 0x92: self.res, 0x93: self.res, 
              0x94: self.res, 0x95: self.res, 0x96: self.res, 0x97: self.res, 
              0x98: self.res, 0x99: self.res, 0x9A: self.res, 0x9B: self.res, 
              0x9C: self.res, 0x9D: self.res, 0x9E: self.res, 0x9F: self.res, 
              0xA0: self.res, 0xA1: self.res, 0xA2: self.res, 0xA3: self.res, 
              0xA4: self.res, 0xA5: self.res, 0xA6: self.res, 0xA7: self.res, 
              0xA8: self.res, 0xA9: self.res, 0xAA: self.res, 0xAB: self.res, 
              0xAC: self.res, 0xAD: self.res, 0xAE: self.res, 0xAF: self.res, 
              0xB0: self.res, 0xB1: self.res, 0xB2: self.res, 0xB3: self.res, 
              0xB4: self.res, 0xB5: self.res, 0xB6: self.res, 0xB7: self.res, 
              0xB8: self.res, 0xB9: self.res, 0xBA: self.res, 0xBB: self.res, 
              0xBC: self.res, 0xBD: self.res, 0xBE: self.res, 0xBF: self.res, 
              #set nth bit
              0xC0: self.set, 0xC1: self.set, 0xC2: self.set, 0xC3: self.set, 
              0xC4: self.set, 0xC5: self.set, 0xC6: self.set, 0xC7: self.set, 
              0xC8: self.set, 0xC9: self.set, 0xCA: self.set, 0xCB: self.set, 
              0xCC: self.set, 0xCD: self.set, 0xCE: self.set, 0xCF: self.set, 
              0xD0: self.set, 0xD1: self.set, 0xD2: self.set, 0xD3: self.set, 
              0xD4: self.set, 0xD5: self.set, 0xD6: self.set, 0xD7: self.set, 
              0xD8: self.set, 0xD9: self.set, 0xDA: self.set, 0xDB: self.set, 
              0xDC: self.set, 0xDD: self.set, 0xDE: self.set, 0xDF: self.set, 
              0xE0: self.set, 0xE1: self.set, 0xE2: self.set, 0xE3: self.set, 
              0xE4: self.set, 0xE5: self.set, 0xE6: self.set, 0xE7: self.set, 
              0xE8: self.set, 0xE9: self.set, 0xEA: self.set, 0xEB: self.set, 
              0xEC: self.set, 0xED: self.set, 0xEE: self.set, 0xEF: self.set, 
              0xF0: self.set, 0xF1: self.set, 0xF2: self.set, 0xF3: self.set, 
              0xF4: self.set, 0xF5: self.set, 0xF6: self.set, 0xF7: self.set, 
              0xF8: self.set, 0xF9: self.set, 0xFA: self.set, 0xFB: self.set, 
              0xFC: self.set, 0xFD: self.set, 0xFE: self.set, 0xFF: self.set}


  def execute_instr(self):
    if (self.halted and self.interrupts_enabled) or self.stopped:
      return

    opcode = self.mmu[self.pc]
    if not self.halted:
      self.pc = (self.pc + 1) % 0x10000

    self.ops[opcode](opcode)
