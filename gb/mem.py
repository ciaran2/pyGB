class DummyMem(object):
  def __getitem__(self,addr):
    return 0
  def __setitem(self,addr,value):
    pass


class Rom(DummyMem):
  def __init__(self, data):
    self.data = bytearray(data)

  def __getitem__(self, addr):
    return self.data[addr]
