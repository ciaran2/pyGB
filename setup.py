#!/usr/bin/env python

import os
from setuptools import setup

def read(fname):
  return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
  name = "pyGB",
  version = "0.0.1",
  author = "Ciaran Cain",
  author_email = "ciaran2@umbc.edu",
  description = "A simple GameBoy emulator written in python",
  license = "MIT",
  url = "http://github.com/ciaran2/pyGB/blob/master/LICENSE",
  long_description=read("README.md"),
  packages=["gb"],
  test_suite="test",
)
