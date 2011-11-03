#!/usr/bin/env python
# encoding: utf-8
"""
Test the backprop algorithms of the modules.

"""

import numpy as np

from modules import *

class Tests:
    def setUp(self):
        self.dim_in  = 5
        self.dim_out = 3

        self.dx      = 1e-7
        self.dw      = 1e-7

    def test_linear_module(self):
        self.do_module(LinearModule, kwargs={'dim_out': self.dim_out})

    def test_sigmoid_module(self):
        self.dim_out = self.dim_in
        self.do_module(SigmoidModule)

    def test_bias_module(self):
        self.dim_out = self.dim_in
        self.do_module(BiasModule)

    def test_softmax_module(self):
        self.dim_out = self.dim_in
        self.do_module(SoftMaxModule)

    def do_module(self, module, args=(), kwargs={}):
        mods = [TestInputModule(self.dim_in, self.dim_out)]
        mods[0].randomize()
        mods.append(module(*args, prev_module=mods[-1], **kwargs))
        mods.append(EuclideanModule(prev_module=mods[-1]))

        mods[-1].do_fprop()
        mods[0].do_bprop()
        dEdx0 = mods[1].dx.flatten()
        if mods[1].dw is not None:
            dEdW0 = mods[1].dw

        dEdx = np.zeros(self.dim_in)
        for i in xrange(self.dim_in):
            mods[0].x[i] += self.dx
            mods[-1].do_fprop()
            mods[0].do_bprop()
            E2 = mods[-1].x
            mods[0].x[i] -= 2*self.dx
            mods[-1].do_fprop()
            mods[0].do_bprop()
            E1 = mods[-1].x
            mods[0].x[i] += self.dx

            dEdx[i] = (E2-E1)/(2.0*self.dx)

        # print dEdx0,dEdx
        # print np.sum(np.abs(dEdx0-dEdx))/self.dim_in
        assert np.sum(np.abs(dEdx0-dEdx))/self.dim_in < self.dx, \
                "backprop to X_in fails for %s"%(repr(module))

        if mods[1].dw is not None:
            shape = np.shape(dEdW0)
            N = np.prod(shape)
            dEdW = np.zeros(shape[::-1])
            for i in xrange(N):
                mods[1].w.flat[i] += self.dw
                mods[-1].do_fprop()
                mods[0].do_bprop()
                E2 = mods[-1].x
                mods[1].w.flat[i] -= 2*self.dw
                mods[-1].do_fprop()
                mods[0].do_bprop()
                E1 = mods[-1].x
                mods[1].w.flat[i] += self.dw

                dEdW.flat[i] = (E2-E1)/(2.0*self.dw)

            dEdW = dEdW.T

            assert np.sum(np.abs(dEdW0-dEdW))/N < self.dx, \
                "backprop to W fails for %s"%(repr(module))

if __name__ == '__main__':
    tests = Tests()
    tests.setUp()
    tests.test_linear_module()
    tests.test_sigmoid_module()
    tests.test_bias_module()
    tests.test_softmax_module()

