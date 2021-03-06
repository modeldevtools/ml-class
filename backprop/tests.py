#!/usr/bin/env python
# encoding: utf-8
"""
Test the backprop algorithms of the modules.

"""

import numpy as np

from modules import *

class Tests:
    def setUp(self):
        self.dim_in  = 20
        self.dim_out = 5

        self.dx      = 1e-7
        self.dw      = 1e-7
        self.tol     = 1.

    def test_linear_module(self):
        self.dim_in, self.dim_out = 20, 5
        self.dx, self.dw = 1e-7, 1e-7
        self.do_module(LinearModule, kwargs={'dim_out': self.dim_out})

    def test_sigmoid_module(self):
        self.dim_out = self.dim_in
        self.dx, self.dw = 1e-7, 1e-7
        self.do_module(SigmoidModule)

    def test_bias_module(self):
        self.dim_out = self.dim_in
        self.dx, self.dw = 1e-7, 1e-7
        self.do_module(BiasModule)

    def test_softmax_module(self):
        self.dim_out = self.dim_in
        self.dx, self.dw = 1e-7, 1e-7
        self.do_module(SoftMaxModule)

    def test_euclidean_module(self):
        self.dim_out = self.dim_in
        self.dx, self.dw = 1e-7, 1e-7
        self.do_module()

    def test_cross_entropy_module(self):
        self.dim_out = self.dim_in
        self.dx, self.dw = 1e-8, 1e-8
        self.do_module(loss_module=CrossEntropyModule)

    def test_rbf_module(self):
        templates = np.random.randn(self.dim_out*self.dim_in).reshape(self.dim_in, self.dim_out)
        self.dx, self.dw = 1e-4, 1e-4
        self.do_module(RBFModule, args=[templates])

    def test_negexp_module(self):
        self.dim_out = self.dim_in
        self.dx, self.dw = 1e-4, 1e-4
        self.do_module(NegExpModule)

    def do_module(self, module=None, args=(), kwargs={},
            loss_module=None, loss_args=(), loss_kwargs={}):
        mods = [TestInputModule(self.dim_in, self.dim_out)]
        mods[0].randomize()
        if module is not None:
            mods.append(module(*args, prev_module=mods[-1], **kwargs))
        else:
            mods[0].x = np.abs(mods[0].x)
            mods[0].x /= np.sum(mods[0].x)
        if loss_module is None:
            mods.append(EuclideanModule(prev_module=mods[-1]))
        else:
            mods.append(loss_module(*loss_args, prev_module=mods[-1], **loss_kwargs))

        mods[-1].do_fprop()
        mods[0].do_bprop()
        dEdx0 = mods[1].dx.flatten()
        if mods[1].dw is not None:
            dEdW0 = mods[1].dw

        dEdx = np.zeros(self.dim_in)
        for i in xrange(self.dim_in):
            mods[0].x[i] += self.dx
            mods[-1].do_fprop()
            E2 = mods[-1].x
            mods[0].x[i] -= 2*self.dx
            mods[-1].do_fprop()
            E1 = mods[-1].x
            mods[0].x[i] += self.dx

            dEdx[i] = (E2-E1)/(2.0*self.dx)

        assert np.sum(np.abs(dEdx0-dEdx))/self.dim_in < self.tol*self.dx, \
                "backprop to X_in fails for %s"%(str(mods[1]))

        if mods[1].dw is not None:
            shape = np.shape(dEdW0)
            N = np.prod(shape)
            dEdW = np.zeros(shape[::-1])
            for i in xrange(N):
                mods[1].w.flat[i] += self.dw
                mods[-1].do_fprop()
                E2 = mods[-1].x
                mods[1].w.flat[i] -= 2*self.dw
                mods[-1].do_fprop()
                E1 = mods[-1].x
                mods[1].w.flat[i] += self.dw

                dEdW.flat[i] = (E2-E1)/(2.0*self.dw)

            dEdW = dEdW.T

            assert np.sum(np.abs(dEdW0-dEdW))/N < self.tol*self.dx, \
                "backprop to W fails for %s"%(str(module))

if __name__ == '__main__':
    tests = Tests()
    tests.setUp()
    tests.test_negexp_module()
    tests.test_rbf_module()
    tests.test_cross_entropy_module()
    tests.test_linear_module()
    tests.test_sigmoid_module()
    tests.test_bias_module()
    tests.test_softmax_module()

