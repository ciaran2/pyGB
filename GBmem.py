class DummyMem:
  def __getitem__(this,addr):
    return 0
  def __setitem(this,addr,value):
    pass

class RAM(DummyMem):

  def __init__(this, min_addr, max_addr):
    pass
