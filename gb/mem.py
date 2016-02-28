class DummyMem(object):
  def __getitem__(self,addr):
    return 0
  def __setitem(self,addr,value):
    pass


class Rom(DummyMem):
  def __init__(self, data=b''):
    self.data = bytearray(data)
    if len(self.data) < 0x4000:
      self.data += bytearray([0x0]) * (0x4000 - len(self.data))
    assert len(self.data) == 0x4000

  def __getitem__(self, addr):
    return self.data[addr]
