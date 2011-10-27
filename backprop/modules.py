#!/usr/bin/env python
# encoding: utf-8
"""
Modules to use to construct a learning machine

"""

from __future__ import division

__all__ = ['LearningModule', 'InputModule', 'LinearModule', 'EuclideanModule',
        'BiasModule', 'SigmoidModule']

import numpy as np
import numpy.linalg

class LearningModule(object):
    """
    The abstract base class for a module

    Parameters
    ----------
    prev_modules : LearningModule
        The module that connects to this one

    """
    def __init__(self, prev_module=None):
        self.prev_module = prev_module
        self.next_module = None
        self.prev_module.connect_module(self)

        s = self.prev_module.x.shape[0]
        self.w  = None
        self.dw = None
        self.x  = np.zeros(s)
        self.dx = np.zeros(s)

        self.randomize()

    def randomize(self, **kwargs):
        pass

    def connect_module(self, next_module):
        self.next_module = next_module

    def do_fprop(self):
        self.prev_module.do_fprop()
        self.fprop()

    def do_bprop(self):
        self.next_module.do_bprop()
        self.bprop()

class InputModule(LearningModule):
    def __init__(self, x, y):
        self._data_x, self._data_y = x, y
        self.w, self.dw = None, None
        self.index = 0
        self.x = self._data_x[self.index]
        self.y = self._data_y[self.index]

    def do_fprop(self):
        self.x = self._data_x[self.index]
        self.y = self._data_y[self.index]
        self.index += 1
        self.index = self.index%self._data_x.shape[0]

    def do_bprop(self):
        self.next_module.do_bprop()

class LinearModule(LearningModule):
    """
    A linear module

    Parameters
    ----------
    out_dim : int
        Dimension of output

    """
    def __init__(self, out_dim, *args, **kwargs):
        self.out_dim = out_dim

        super(LinearModule, self).__init__(*args, **kwargs)

        # initialize the weight vector randomly
        self.x  = np.zeros(out_dim)

    def randomize(self, **kwargs):
        z2 = self.prev_module.x.shape[0]
        kz = kwargs.pop('k', 1.0)/np.sqrt(z2)

        self.shape = (self.out_dim, z2)
        self.w  = 2*kz*np.random.rand(*(self.shape))-kz

    def fprop(self):
        self.x = np.dot(self.w, self.prev_module.x)

    def bprop(self):
        self.dx = np.dot(self.w.T, self.next_module.dx)
        self.dw = np.dot(self.dx, self.prev_module.x.T)

class EuclideanModule(LearningModule):
    def __init__(self, y, *args, **kwargs):
        super(EuclideanModule, self).__init__(*args, **kwargs)
        self.y = y
        self.x = 0.0

    def fprop(self):
        self.x = 0.5*np.linalg.norm(self.prev_module.x-self.y)**2

    def do_bprop(self):
        self.dx = self.prev_module.x-self.y
        self.dy = -self.dx

class BiasModule(LearningModule):
    def randomize(self, **kwargs):
        self.w = np.random.rand(*(self.x.shape))

    def fprop(self):
        self.x = self.prev_module.x.T + self.w

    def bprop(self):
        self.dx = self.next_module.dx
        self.dw = self.next_module.dx

class SigmoidModule(LearningModule):
    def fprop(self):
        self.x = np.tanh(self.prev_module.x)

    def bprop(self):
        # dtanh = 1/cosh^2
        self.dx = self.next_module.dx/np.cosh(self.prev_module.x)**2

if __name__ == '__main__':
    pass

