class Cpu(object):
  def __init__(self, mmu):
    self.mmu = mmu
    self.pc = 0
