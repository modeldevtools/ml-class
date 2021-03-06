#!/usr/bin/env python
# encoding: utf-8
"""
Modules to use to construct a learning machine

"""

from __future__ import division

__all__ = ['LearningModule', 'InputModule', 'TestInputModule', 'LinearModule',
        'EuclideanModule', 'BiasModule', 'SigmoidModule', 'SoftMaxModule',
        'CrossEntropyModule', 'RBFModule', 'NegExpModule']

import numpy as np

class LearningModule(object):
    """
    The abstract base class for a module

    Parameters
    ----------
    prev_module : LearningModule
        The module that connects to this one

    dim_in : int, optional
        The dimension of the input. Defaults to the output dimension of prev_module

    dim_out : int, optional
        The output dimension. Defaults to dim_in

    """
    def __init__(self, *args, **kwargs):
        dim_out, dim_in = kwargs.pop('dim_out',None), kwargs.pop('dim_in',None)
        self.prev_module = kwargs.pop('prev_module', None)
        if self.prev_module is None and len(args) >= 1:
            self.prev_module = args[0]
        self.next_module = None

        if self.prev_module is not None:
            # the input dimensions will be set by the previous module's
            # output dimensions
            self.dim_in = self.prev_module.dim_out
            if dim_in is not None:
                assert(dim_in == self.dim_in)
        else:
            self.dim_in = dim_in

        # output dimensions default to the same as dim_in
        if dim_out is not None:
            self.dim_out = dim_out
        else:
            self.dim_out = self.dim_in

        if self.prev_module is not None:
            # connect the previous module
            self.prev_module.connect_module(self)

        self.w  = None                        # W
        self.dw = None                        # dE/dW
        self.x  = np.zeros((self.dim_out, 1)) # X_out
        self.dx = np.zeros((self.dim_in, 1))  # dE/dXin

        self.randomize()

    def __str__(self):
        return type(self).__name__[:-6]

    def randomize(self, **kwargs):
        """
        Randomize the weight vector

        This is an abstract baseclass that subclasses should override.

        """
        pass

    def connect_module(self, next_module):
        """
        Connect the module that will come next in the NN chain

        A pointer to this module is saved as self.next_module.

        Parameters
        ----------
        next_module : LearningModule
            The next module in the chain

        """
        assert(self.dim_out == next_module.dim_in)
        self.next_module = next_module

    def do_fprop(self):
        """
        Perform forward propagation

        Subclasses should override fprop NOT do_fprop (except loss modules).

        """
        self.prev_module.do_fprop()
        self.y = self.prev_module.y
        self.fprop()

    def do_bprop(self):
        """
        Perform back propagation

        Subclasses should override bprop NOT do_bprop (except input modules).

        """
        self.next_module.do_bprop()
        self.dy = self.next_module.dy
        self.bprop()

        # do some basic checks of the dimensions
        assert (self.w is None and self.dw is None) or \
                np.shape(self.dw.T) == np.shape(self.w), repr(self)
        assert np.shape(self.dx) == (1, self.dim_in), repr(self)

    def fprop(self):
        """
        Abstract forward propagation method, overridden by subclasses

        """
        pass

    def bprop(self):
        """
        Abstract back propagation method, overridden by subclasses

        """
        pass

# ================= #
#                   #
#   INPUT MODULES   #
#                   #
# ================= #

class InputModule(LearningModule):
    """
    The base node in a NN chain

    Parameters
    ----------
    dim_x : int
        The dimension of the input vectors

    dim_y : int
        The dimension of the target vectors

    """
    def __init__(self, dim_x, dim_y):
        self.dim_out = dim_x
        self.dim_y   = dim_y
        self.w, self.dw = None, None

    # override default fprop and bprop behaviour
    def do_fprop(self):
        pass

    def do_bprop(self):
        self.next_module.do_bprop()

    def current_sample(self):
        return self.x, self.y

    def set_current_sample(self, x, y):
        # NOTE: this converts the inputs to column vectors
        self.x, self.y = np.atleast_2d(x).T, np.atleast_2d(y).T

class TestInputModule(InputModule):
    def __init__(self, *args, **kwargs):
        super(TestInputModule, self).__init__(*args, **kwargs)
        self.y = np.zeros(self.dim_y)
        self.y[np.random.randint(self.dim_y)] = 1
        self.y = np.atleast_2d(self.y).T

    def randomize(self, **kwargs):
        self.x = np.atleast_2d(np.random.randn(self.dim_out)).T

# ==================== #
#                      #
#   STANDARD MODULES   #
#                      #
# ==================== #

class LinearModule(LearningModule):
    def __init__(self, *args, **kwargs):
        super(LinearModule, self).__init__(*args, **kwargs)
        self.x = np.zeros((self.dim_out, 1))

    def __str__(self):
        return "%s(%d)"%(type(self).__name__[:-6], self.dim_out)

    def randomize(self, **kwargs):
        kz = kwargs.pop('k', 1.0)/np.sqrt(self.dim_in)
        self.shape = (self.dim_out, self.dim_in)
        self.w  = (2*np.random.rand(*(self.shape)) - 1) * kz

    def fprop(self):
        self.x = np.dot(self.w, self.prev_module.x)
        assert(self.x.shape[0] == self.dim_out and self.x.shape[1] == 1)

    def bprop(self):
        self.dw = np.dot(self.next_module.dx.T, self.prev_module.x.T).T
        self.dx = np.dot(self.w.T, self.next_module.dx.T).T
        assert(self.dw.shape == self.shape[::-1])
        assert(self.dx.shape[1] == self.dim_in and self.dx.shape[0] == 1)

class BiasModule(LearningModule):
    def randomize(self, **kwargs):
        self.w = np.random.rand(self.dim_in, 1)

    def fprop(self):
        assert(self.prev_module.x.shape == self.w.shape)
        self.x = self.prev_module.x + self.w

    def bprop(self):
        self.dx = self.next_module.dx
        self.dw = self.next_module.dx

class SigmoidModule(LearningModule):
    def fprop(self):
        self.x = np.tanh(self.prev_module.x)

    def bprop(self):
        # dtanh = 1/cosh^2
        # careful with dimensions
        self.dx = self.next_module.dx/np.cosh(self.prev_module.x.T)**2
        assert(self.dx.shape == self.next_module.dx.shape)

class EuclideanModule(LearningModule):
    def fprop(self):
        assert(self.prev_module.x.shape == self.prev_module.y.shape)
        self.losses = 0.5*(self.prev_module.x-self.prev_module.y)**2
        self.x = np.sum(self.losses.flatten())
        #print self.x

    def do_bprop(self):
        self.dx = (self.prev_module.x - self.y).T
        self.dy = -self.dx

# =============== #
#                 #
#   NEW MODULES   #
#                 #
# =============== #

class SoftMaxModule(LearningModule):
    def randomize(self, **kwargs):
        self.w = np.atleast_2d(np.random.rand())

    def fprop(self):
        self.x = np.exp(-self.w * self.prev_module.x)
        self.x /= np.sum(self.x)

    def bprop(self):
        delta = np.dot(self.x, self.x.T) - np.diagflat(self.x)
        self.dx = self.w*np.sum(self.next_module.dx[0][:,None] * delta, axis=0)

        # expectation value of X_in
        xin = self.prev_module.x
        p = np.exp(-self.w*xin)
        mu = np.sum(xin*p)/np.sum(p)
        self.dw = np.dot(self.next_module.dx, \
                (self.x*mu - self.prev_module.x * self.x))

class CrossEntropyModule(LearningModule):
    """
    Cacluate the KL divergence between the input vector and the desired classification

    NOTE: this should return
        L = SUM_k Y_k log_2 ( Y_k / X_k )
    but for this assignment Y_k is always either 1 or 0, I can simply return
        L = - SUM_k Y_k log_2 ( X_k )

    """
    def fprop(self):
        inds = self.prev_module.y > 0
        self.losses = np.zeros(self.prev_module.x.shape)
        self.losses[inds] = -np.log2(self.prev_module.x[inds])
        self.x = np.sum(self.losses)

    def do_bprop(self):
        inds = self.prev_module.y.T > 0
        self.dx = np.zeros(self.prev_module.x.T.shape)
        self.dx[inds] = -(self.prev_module.y[inds.T] \
                / self.prev_module.x[inds.T]).T/np.log(2)
        self.dy = np.zeros(self.dx.shape)
        self.dy[inds] = -np.log(self.prev_module.x[inds.T])

class RBFModule(LearningModule):
    """
    The RBF module

    Parameters
    ----------
    templates : numpy.ndarray (N_{dim}, N_{templates})
        The matrix of templates for initialization

    """
    def __init__(self, templates, *args, **kwargs):
        super(RBFModule, self).__init__(*args, **kwargs)
        self.w = templates
        self.dim_out = templates.shape[1]
        assert(self.dim_in == templates.shape[0])

    def __str__(self):
        return "%s(%d)"%(type(self).__name__[:-6], self.dim_out)

    def fprop(self):
        self.x = np.atleast_2d(0.5*np.sum((self.prev_module.x-self.w)**2, \
                                             axis=0)).T

    def bprop(self):
        self.dw = (self.next_module.dx*(self.w-self.prev_module.x)).T
        self.dx = -np.atleast_2d(np.sum(self.dw, axis=0))

class NegExpModule(LearningModule):
    def randomize(self, **kwargs):
        self.w = np.atleast_2d(np.random.rand())

    def fprop(self):
        self.x = np.exp(-self.w * self.prev_module.x)

    def bprop(self):
        self.dx = -self.w * self.next_module.dx * self.x.T
        self.dw = -np.dot(self.next_module.dx, self.prev_module.x * self.x)

