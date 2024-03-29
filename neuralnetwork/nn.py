"""
implement conv layer
"""



import numpy as np

from scipy.linalg import circulant


from scipy import ndimage


def init_w(shape):
    return np.random.normal(0, 1. / np.product(shape), shape)


def circulant_check():
    for N in [512, 1024, 2048, 4096, 8192, 16384, 32768, 65536]:
      r = init_w(N)
      x = init_w(N)
      d = np.fft.ifft( np.fft.fft(r) * np.fft.fft(x) ) - np.dot(circulant(r), x)
      print N, np.mean(np.abs(d)), np.linalg.norm(d)
    for N in [512, 1024, 2048, 4096, 8192, 16384, 32768, 65536]:
      r = init_w(N)
      x = init_w([N/4, N])
      d = np.fft.ifft( np.fft.fft(x) * np.fft.fft(r) ).T - np.dot(circulant(r), x.T)
      print N, np.mean(np.abs(d)), np.linalg.norm(d)


"""
class CircFC(object):
    def __init__(self, I, H, name=None):
        # I : input size
        # H : hidden size
        self.k = max(I, H) # r is now padded
        self.r = init_w( self.k )
        self.dr = np.zeros(self.k)
        self.mapping = np.roll(np.arange(self.k)[::-1], 1) # for shifting x
        self.name = name
        self.H = H # desired output size

    def forward(self, x):
        # a = dot(x, R.T), shape=(b, H)
        if self.k > x.shape[1]: # then self.k = self.H
            # pad data
            # http://docs.scipy.org/doc/numpy/reference/generated/numpy.pad.html
            # http://stackoverflow.com/questions/19349410/how-to-pad-with-zeros-a-tensor-along-some-axis-python
            assert self.k == self.H
            new_x = np.pad(x, [(0,0), (0, self.k-x.shape[1])], 'constant', constant_values=0)
            a = np.fft.ifft( np.fft.fft(new_x) * np.fft.fft(self.r) )[:,:self.H]
        else:
            a = np.fft.ifft( np.fft.fft(x) * np.fft.fft(self.r) )[:, :self.H]
        if __debug__:
            if self.k > x.shape[1]:
                new_x = np.pad(x, [(0,0), (0, self.k-x.shape[1])], 'constant', constant_values=0)
                check_a = np.dot(new_x, circulant(self.r).T)[:, :self.H]
            else:
                check_a = np.dot(x, circulant(self.r).T)[:, :self.H]
            assert np.linalg.norm( a - check_a ) < 1e-6
            print self.name, "forward", x.shape, "to", a.shape
        return np.real(a)

    def backward(self, x, d_a):
        if self.k > x.shape[1]:
            # pad data, don't forget to change form of x
            assert self.k == self.H
            new_x = np.pad(x, [(0,0), (0, self.k-x.shape[1])], 'constant', constant_values=0)[:, self.mapping]
            self.dr = np.sum( np.fft.ifft(np.fft.fft(new_x)*np.fft.fft(d_a)), axis=0 )
            d_x = np.fft.ifft( np.fft.fft(d_a) * np.fft.fft(self.r[self.mapping]) )[:,:x.shape[1]]
        else:
            new_x = x[:, self.mapping]
            new_d_a = np.pad(d_a, [(0,0), (0, self.k-d_a.shape[1])], 'constant', constant_values=0)
            self.dr = np.sum( np.fft.ifft(np.fft.fft(new_x)*np.fft.fft(new_d_a)), axis=0 )
            d_x = np.fft.ifft( np.fft.fft(new_d_a) * np.fft.fft(self.r[self.mapping]) )[:,:x.shape[1]]
        if __debug__:
            if self.k > x.shape[1]:
                check_d_x = np.dot(d_a, circulant(self.r))[:, :x.shape[1]]
            else:
                new_d_a = np.pad(d_a, [(0,0), (0, self.k-d_a.shape[1])], 'constant', constant_values=0)
                check_d_x = np.dot(new_d_a, circulant(self.r))[:, :x.shape[1]]
            diff_norm = np.linalg.norm( d_x - check_d_x )
            print self.name, "backward", d_a.shape, "to", d_x.shape, diff_norm
            assert diff_norm < 1e-9
        self.dr = np.real(self.dr)
        return np.real(d_x)

    def update(self, lr=0.01):
        self.r = self.r - lr * self.dr
        self.dr.fill(0.)
"""



"""
# This is for the version where A=Z1, q=n
class DisplaceFC(object):
    def __init__(self, I, H, name=None):
        # I : input size
        # H : hidden size
        assert I == H # currently only support square ones
        self.n = I
        self.g = init_w([self.n, 1])
        self.dg = np.zeros(self.g.shape)
        self.h = init_w([self.n, 1])
        self.dh = np.zeros(self.h.shape)

        self.c = init_w([self.n, 1])
        self.dc = np.zeros(self.c.shape)

        tmp = np.arange(self.n) / float(self.n) 
        self.B = np.diag( tmp )
        # assume self.A is Z1
        self.coe = np.diag( 1. / (1. - tmp ** self.n) ) 

        self.name = name

    def forward(self, x):
        self.w = 0
        Bi = np.identity(self.n)
        for i in xrange(self.n):
            index = np.roll( np.arange(self.n), i )
            self.w += self.g.dot(self.h.T).dot(Bi)[index,:]
            Bi = Bi.dot(self.B)
        self.w = self.w.dot(self.coe)
        a = np.dot(x, self.w.T) + self.c.T # a = wx + c
        if __debug__:
            index = np.roll(np.arange(self.n), 1)
            assert np.allclose(
                self.g.dot(self.h.T),
                self.w - self.w.dot(self.B)[index,:]
            )
            print self.name, "forward", x.shape, "to", a.shape
        return a

    def backward(self, x, d_a):
        self.dc = np.dot(d_a.T, np.ones([x.shape[0], 1]))
        d_x = np.dot(d_a, self.w) # this is for next backpropagate layer

        dw = np.dot(d_a.T, x)
        Bi = np.identity(self.n)
        for i in xrange(self.n):
            index = np.roll( np.arange(self.n), (self.n-i)%self.n )
            tmp = Bi.dot(self.coe).T
            self.dg += dw[index,:].dot( tmp ).dot(self.h)
            self.dh += self.g.T.dot(dw[index,:]).dot( tmp ).T
            Bi = Bi.dot(self.B)
        if __debug__:
            print self.name, "backward", d_a.shape, "to", d_x.shape
        return d_x

    def update(self, lr=0.01):
        self.g = self.g - lr * self.dg
        self.dg.fill(0.)
        self.h = self.h - lr * self.dh
        self.dh.fill(0.)
        self.c = self.c - lr * self.dc
        self.dc.fill(0.)
"""




#"""
class DisplaceFC(object):
    def __init__(self, I, H, name=None):
        assert I == H # currently only support square ones
        self.n = I
        self.g = init_w([self.n, 1])
        self.dg = np.zeros(self.g.shape)
        self.h = init_w([self.n, 1])
        self.dh = np.zeros(self.h.shape)
        self.c = init_w([self.n, 1])
        self.dc = np.zeros(self.c.shape)
        tmp = np.arange(I) / float(I) 
        self.B = np.diag( tmp )
        self.coe = np.diag( 1. / (1. - tmp) ) # (I , aB^q)^{-1} 
        self.name = name

    def forward(self, x):
        self.w = self.g.dot(self.h.T).dot(self.coe)
        a = np.dot(x, self.w.T) + self.c.T # a = wx + c
        if __debug__:
            assert np.allclose(
                self.g.dot(self.h.T),
                self.w - self.w.dot(self.B)
            )
            print self.name, "forward", x.shape, "to", a.shape
        return a

    def backward(self, x, d_a):
        # for accumulation in block-displace-fc
        #self.dc = np.dot(d_a.T, np.ones([x.shape[0], 1]))
        self.dc += np.dot(d_a.T, np.ones([x.shape[0], 1]))
        d_x = np.dot(d_a, self.w) # this is for next backpropagate layer

        dw = np.dot(d_a.T, x)
        #self.dg = dw.dot(self.coe.T).dot(self.h)
        #self.dh = self.g.T.dot(dw).dot(self.coe).T
        # for accumulation in block-displace-fc
        self.dg += dw.dot(self.coe.T).dot(self.h)
        self.dh += self.g.T.dot(dw).dot(self.coe).T
        if __debug__:
            print self.name, "backward", d_a.shape, "to", d_x.shape
        return d_x

    def update(self, lr=0.01):
        self.g = self.g - lr * self.dg
        self.dg.fill(0.)
        self.h = self.h - lr * self.dh
        self.dh.fill(0.)
        self.c = self.c - lr * self.dc
        self.dc.fill(0.)
#"""



class BlockDisplaceFC(object):
    def __init__(self, I, H, k=None, name=None):
        # I : input size
        # H : hidden size
        self.I = I
        self.H = H
        def gcd(a, b): 
            return gcd(b, a % b) if b else a
        if k is None:
            self.k = gcd(self.I, self.H)
        else:
            self.k = k
            self.I = ((I + k - 1) / k) * k
            self.H = ((H + k - 1) / k) * k
            self.desired_output = H
        assert self.I % self.k == 0 and self.H % self.k == 0

        self.B = [[DisplaceFC(self.k, self.k, 'tmp_%d_%d' % (i,j)) 
                    for j in xrange(self.H/self.k)] 
                    for i in xrange(self.I/self.k)]
        self.name = name
        print "ATTENTION: You are using BlockDisplaceFC", I, H, self.k

    def forward(self, x):
        tmp_x = np.zeros([((x.shape[0]+self.k-1)/self.k)*self.k, 
                          ((x.shape[1]+self.k-1)/self.k)*self.k])
        tmp_x[:x.shape[0], :x.shape[1]] = x
        a = np.zeros([tmp_x.shape[0], self.H])
        for i in xrange(a.shape[0] / self.k): #B
            for j in xrange(a.shape[1] / self.k): #H
                for k in xrange(self.I / self.k): #I
                    # x[i,k] * b[k,j]
                    a[i*self.k:(i+1)*self.k, j*self.k:(j+1)*self.k] += self.B[k][j].forward(tmp_x[i*self.k:(i+1)*self.k, k*self.k:(k+1)*self.k])
        if __debug__:
            print self.name, "forward", x.shape, "to", a.shape
        return a[:x.shape[0], :self.desired_output]

    def backward(self, x, d_a):
        tmp_x = np.zeros([((x.shape[0]+self.k-1)/self.k)*self.k, 
                          ((x.shape[1]+self.k-1)/self.k)*self.k])
        tmp_x[:x.shape[0], :x.shape[1]] = x
        tmp_d_a = np.zeros([((d_a.shape[0]+self.k-1)/self.k)*self.k,
                            ((d_a.shape[1]+self.k-1)/self.k)*self.k])
        tmp_d_a[:d_a.shape[0], :d_a.shape[1]] = d_a
        d_x = np.zeros(tmp_x.shape)
        for k in xrange(self.I/self.k): #I
            for j in xrange(self.H/self.k): #H
                for i in xrange(tmp_x.shape[0]/self.k): #B
                    d_x[i*self.k:(i+1)*self.k, k*self.k:(k+1)*self.k] += self.B[k][j].backward(
                            tmp_x[i*self.k:(i+1)*self.k, k*self.k:(k+1)*self.k],
                            tmp_d_a[i*self.k:(i+1)*self.k, j*self.k:(j+1)*self.k])
        if __debug__:
            print self.name, "backward", d_a.shape, "to", d_x.shape
        return d_x[:x.shape[0], :x.shape[1]]

    def update(self, lr=0.01):
        for bi in self.B:
            for bij in bi:
                bij.update(lr)


class DisplaceFC2(object):
    def __init__(self, I, H, name=None):
        assert I == H # currently only support square ones
        self.I = I
        self.H = H
        self.n = np.max([I, H])
        self.g = init_w([self.n, 1])
        self.dg = np.zeros(self.g.shape)
        self.h = init_w([self.n, 1])
        self.dh = np.zeros(self.h.shape)
        self.c = init_w([self.n, 1])
        self.dc = np.zeros(self.c.shape)
        tmp = np.arange(self.n) / float(self.n) 
        self.B = np.diag( tmp )
        self.coe = np.diag( 1. / (1. - tmp) ) # (I , aB^q)^{-1} 
        self.name = name

    def forward(self, x):
        if x.shape[1] < self.n:
            new_x = np.zeros([x.shape[0], self.n])
            new_x[:x.shape[0], :x.shape[1]] = x
        else:
            new_x = x
        self.w = self.g.dot(self.h.T).dot(self.coe)
        a = np.dot(new_x, self.w.T) + self.c.T # a = wx + c
        if __debug__:
            assert np.allclose(
                self.g.dot(self.h.T),
                self.w - self.w.dot(self.B)
            )
            print self.name, "forward", x.shape, "to", a.shape
        return a[:x.shape[0], :self.H]

    def backward(self, x, d_a):
        if d_a.shape[1] < self.n:
            new_d_a = np.zeros([d_a.shape[0], self.n])
            new_d_a[:d_a.shape[0],:d_a.shape[1]] = d_a
        else:
            new_d_a = d_a
        # for accumulation in block-displace-fc
        self.dc = np.dot(new_d_a.T, np.ones([x.shape[0], 1]))
        d_x = np.dot(new_d_a, self.w) # this is for next backpropagate layer

        if x.shape[1] < self.n:
            new_x = np.zeros([x.shape[0], self.n])
            new_x[:x.shape[0], :x.shape[1]] = x
        else:
            new_x = x
        dw = np.dot(new_d_a.T, new_x)
        self.dg = dw.dot(self.coe.T).dot(self.h)
        self.dh = self.g.T.dot(dw).dot(self.coe).T
        if __debug__:
            print self.name, "backward", d_a.shape, "to", d_x.shape
        return d_x[:x.shape[0], :x.shape[1]]

    def update(self, lr=0.01):
        self.g = self.g - lr * self.dg
        self.dg.fill(0.)
        self.h = self.h - lr * self.dh
        self.dh.fill(0.)
        self.c = self.c - lr * self.dc
        self.dc.fill(0.)

 






class NeatCircFC(object):
    # This implementation saves the efforts of padding
    def __init__(self, I, H, name=None):
        # I : input size
        # H : hidden size
        self.k = max(I, H) # r is now padded
        self.r = init_w( self.k )
        self.dr = np.zeros(self.k)
        self.mapping = np.roll(np.arange(self.k)[::-1], 1) # for shifting x
        self.name = name
        self.H = H # desired output size

    def forward(self, x):
        a = np.fft.irfft(np.fft.rfft(x, n=self.k) * np.fft.rfft(self.r, n=self.k), n=self.k)[:, :self.H]
        return np.real(a)

    def backward(self, x, d_a):
        new_x = np.pad(x, [(0, 0), (0, self.k - x.shape[1])], 'constant', constant_values=0)[:, self.mapping]
        self.dr = np.sum(np.fft.irfft(np.fft.rfft(new_x, n=self.k) * np.fft.rfft(d_a, n=self.k), n=self.k), axis=0)
        d_x = np.fft.irfft(np.fft.rfft(d_a, n=self.k) * np.fft.rfft(self.r[self.mapping], n=self.k), n=self.k)[:, :x.shape[1]]
        return d_x

    def update(self, lr=0.01):
        self.r = self.r - lr * self.dr
        self.dr.fill(0.)


CircFC = NeatCircFC




class CircFC_fft(object):
    # This implementation saves the efforts of padding, and fft
    def __init__(self, I, H, name=None):
        # I : input size
        # H : hidden size
        self.k = max(I, H) # r is now padded
        self.r = np.fft.rfft( init_w( self.k ), n=self.k )
        self.dr = np.copy(self.r)
        self.mapping = np.roll(np.arange(self.k)[::-1], 1) # for shifting x
        self.name = name
        self.H = H # desired output size

        assert self.k % 2 == 0 # important on the shifting part below

    def forward(self, x):
        a = np.fft.irfft(np.fft.rfft(x, n=self.k) * self.r, n=self.k)[:, :self.H]
        return np.real(a)

    def backward(self, x, d_a):
        new_x = np.pad(x, [(0, 0), (0, self.k - x.shape[1])], 'constant', constant_values=0)[:, self.mapping]
        self.dr = np.sum(np.fft.rfft(new_x, n=self.k) * np.fft.rfft(d_a, n=self.k), axis=0)

        # the first element is always real number, so it doesn't hurt we take its conjugate as well
        # the last element doesn't need to have its conjugate (in the case of when k is even)
        #
        d_x = np.fft.irfft(np.fft.rfft(d_a, n=self.k) * np.append(np.conj(self.r[:self.k/2]), self.r[self.k/2]), n=self.k)[:, :x.shape[1]]

        if __debug__:
            tmpr = np.fft.irfft(self.r, n=self.k)
            assert np.allclose(np.append(np.conj(self.r[:self.k/2]), self.r[self.k/2]), np.fft.rfft(tmpr[self.mapping], n=self.k))
            d_x2 = np.fft.irfft(np.fft.rfft(d_a, n=self.k) * np.fft.rfft(tmpr[self.mapping], n=self.k), n=self.k)[:,:x.shape[1]]
            assert np.allclose(d_x2, d_x)
        return d_x

    def update(self, lr=0.01):
        self.r = self.r - lr * self.dr
        self.dr.fill(0.)



def time_test2():
    b = 32
    d = 28 * 28
    x0 = np.random.random([b, d])
    W0 = np.random.random(d)

    # http://stackoverflow.com/questions/7370801/measure-time-elapsed-in-python
    from timeit import default_timer as timer
    # from time import time as timer

    from scipy.linalg import circulant


    I = d
    H = d

    #circ = NeatCircFC(I, H, 'neatcircfc')
    circ = CircFC(I, H, 'circfc')
    circ.r = W0

    fc = FC(I, H, 'fc')
    fc.w = circulant(W0)[:H]
    fc.c[:] = 0

    n = 10
    fwd_circ_time = [0] * n
    fwd_fc_time = [0] * n
    bck_circ_time = [0] * n
    bck_fc_time = [0] * n
    for i in xrange(n):

        # circfc
        start = timer()
        y0 = circ.forward(x0)
        end = timer()
        fwd_circ_time[i] = end - start

        # ground truth
        start = timer()
        y1 = fc.forward(x0)
        end = timer()
        fwd_fc_time[i] = end - start

        assert np.allclose(y0, y1)

        d_a = np.random.random(y0.shape)

        start = timer()
        g0 = circ.backward(x0, d_a)
        end = timer()
        bck_circ_time[i] = end - start

        start = timer()
        g1 = fc.backward(x0, d_a)
        end = timer()
        bck_fc_time[i] = end - start

        assert np.allclose(g0, g1)


    print "avg(fwd_circ_time) = ", sum(fwd_circ_time) / float(n)
    print "avg(fwd_fc_time) = ", sum(fwd_fc_time) / float(n)
    print "avg(bck_circ_time) = ", sum(bck_circ_time) / float(n)
    print "avg(bck_fc_time) = ", sum(bck_fc_time) / float(n)





class NewCircFC(object):
    def __init__(self, I, H, name=None):
        # I : input size
        # H : hidden size
        self.I = I
        self.H = H
        if self.I <= self.H:
            self.k = I
            self.c = [CircFC(self.k, self.k, name + '_tmp_%d' % i) if (i + 1) * self.k <= self.H
                      else CircFC(self.k, self.H - i * self.k, name + '_tmp_%d' % i)
                      for i in xrange((self.H + self.I - 1) / self.I)]
        else:
            self.k = H
            self.c = [CircFC(self.k, self.k, name + '_tmp_%d' % i) if (i + 1) * self.k <= self.I
                      else CircFC(self.I - i * self.k, self.k, name + '_tmp_%d' % i)
                      for i in xrange((self.I + self.H - 1) / self.H)]
        self.name = name
        print "ATTENTION: You are using NewCircFC"

    def forward(self, x):
        assert self.I == x.shape[1]
        a = np.zeros((x.shape[0], self.H))
        if self.I <= self.H:
            for i in xrange((self.H + self.I - 1) / self.I): # ceil(5/3)=2, i={0,1} -- {0,3}
                end = (i + 1) * self.k
                if end > self.H:
                    end = self.H
                a[:, i*self.k:end] = self.c[i].forward(x)
        else:
            for i in xrange((self.I + self.H - 1) / self.H):
                end = (i + 1) * self.k
                if end > self.I:
                    end = self.I
                a += self.c[i].forward(x[:,i*self.k:end])
        if __debug__:
            print self.name, "forward", x.shape, "to", a.shape
        return a

    def backward(self, x, d_a):
        d_x = np.zeros(x.shape)
        if self.I <= self.H:
            for i in xrange((self.H + self.I - 1) / self.I): # ceil(5/3)=2, i={0,1} -- {0,3}
                end = (i + 1) * self.k
                if end > self.H:
                    end = self.H
                d_x += self.c[i].backward(x, d_a[:,i*self.k:end])
        else:
            for i in xrange((self.I + self.H - 1) / self.H):
                end = (i + 1) * self.k
                if end > self.I:
                    end = self.I
                d_x[:, i*self.k:end] = self.c[i].backward(x[:,i*self.k:end], d_a)
        if __debug__:
            print self.name, "backward", d_a.shape, "to", d_x.shape
        return d_x

    def update(self, lr=0.01):
        for i in xrange(len(self.c)):
            self.c[i].update(lr)

   

class NewCircFC2(object):
    def __init__(self, I, H, k, name=None):
        # I : input size
        # H : hidden size
        self.I = I
        self.H = H
        self.k = k
        self.rows = (self.H + self.k - 1) / self.k
        self.cols = (self.I + self.k - 1) / self.k
        self.c = [CircFC(self.k, self.k, name + '_tmp_%d_%d' % (i,j)) for j in xrange(self.cols) for i in xrange(self.rows)]
        self.name = name
        print "ATTENTION: You are using NewCircFC2"

    def forward(self, x):
        assert self.I == x.shape[1]
        a = np.zeros((x.shape[0], self.k*self.rows))
        new_x = np.pad(x, [(0,0), (0, self.k*self.cols-x.shape[1])], 'constant', constant_values=0)
        for i in xrange(self.rows):
            for j in xrange(self.cols):
                a[:, i*self.k:(i+1)*self.k] += self.c[i*self.cols + j].forward(new_x[:, j*self.k:(j+1)*self.k])
        if __debug__:
            print self.name, "forward", x.shape, "to", a.shape
        return a[:,:self.H]

    def backward(self, x, d_a):
        d_x = np.zeros([x.shape[0], self.k*self.cols])
        new_x = np.pad(x, [(0, 0), (0, self.k * self.cols - x.shape[1])], 'constant', constant_values=0)
        for j in xrange(self.cols):
            for i in xrange(self.rows):
                d_x[:, j*self.k:(j+1)*self.k] += self.c[i*self.cols + j].backward(new_x[:, j*self.k:(j+1)*self.k], d_a[:, i*self.k:(i+1)*self.k])
        if __debug__:
            print self.name, "backward", d_a.shape, "to", d_x.shape
        return d_x[:,:self.I]

    def update(self, lr=0.01):
        for i in xrange(self.rows):
            for j in xrange(self.cols):
                self.c[i][j].update(lr)



class NewCircFC3(object):
    def __init__(self, I, H, k, name=None):
        # I : input size
        # H : hidden size
        self.I = I
        self.H = H
        self.k = k
        self.rows = (self.H + self.k - 1) / self.k
        self.cols = (self.I + self.k - 1) / self.k
        self.w = init_w([1, self.cols, self.rows, self.k])
        self.mapping = np.roll(np.arange(self.k)[::-1], 1) # for shifting x
        self.name = name
        print "ATTENTION: You are using NewCircFC3"

    def forward(self, x):
        assert self.I == x.shape[1]
        a = np.zeros((x.shape[0], self.k*self.rows))
        new_x = np.pad(x, [(0,0), (0, self.k*self.cols-x.shape[1])], 'constant', constant_values=0)
        new_x = new_x.reshape([x.shape[0], self.cols, 1, self.k]) 
        a = np.sum(
                np.fft.irfft(np.fft.rfft(new_x, n=self.k) * np.fft.rfft(self.w, n=self.k), n=self.k),
                axis=1
            ).reshape(a.shape)
        if __debug__:
            print self.name, "forward", x.shape, "to", a.shape
        return a[:,:self.H]

    def backward(self, x, d_a):
        d_x = np.zeros([x.shape[0], self.k*self.cols])
        new_x = np.pad(x, [(0, 0), (0, self.k * self.cols - x.shape[1])], 'constant', constant_values=0)
        new_x = new_x.reshape([x.shape[0], self.cols, 1, self.k])[:, :, :, self.mapping]
        new_d_a = np.pad(d_a, [(0,0), (0, self.k * self.rows -d_a.shape[1])], 'constant', constant_values=0)
        new_d_a = new_d_a.reshape(x.shape[0], 1, self.rows, self.k)
        self.dw = np.sum(np.fft.irfft(np.fft.rfft(new_x, n=self.k) * np.fft.rfft(new_d_a, n=self.k), n=self.k), axis=0)
        d_x = np.sum(np.fft.irfft(np.fft.rfft(new_d_a, n=self.k) * np.fft.rfft(self.w[:,:,:,self.mapping], n=self.k), n=self.k), axis=2)
        d_x = d_x.reshape([x.shape[0], self.k * self.cols])
        if __debug__:
            print self.name, "backward", d_a.shape, "to", d_x.shape
        return d_x[:,:self.I]

    def update(self, lr=0.01):
        self.w = self.w - lr * self.dw
        pass









        
class CauchyFC(object):
    def __init__(self, I, H, name=None):
        # I : input size
        # H : hidden size
        # Notice:
        # since cauchy matrix is 1/(s-t), if s and t are too small, then w can be too large
        self.s = init_w(H) * H * H
        self.ds = np.zeros(self.s.shape)

        self.t = init_w(I) * I * I
        self.dt = np.zeros(self.t.shape)

        self.name = name

    def forward(self, x):
        # http://stackoverflow.com/questions/21427687/efficiently-generating-a-cauchy-matrix-from-two-numpy-arrays
        self.w = 1.0 / (self.s.reshape((-1,1)) - self.t)
        a = np.dot(x, self.w.T) # a = wx
        if __debug__:
            print self.name, "forward", x.shape, "to", a.shape
        return a

    def backward(self, x, d_a):
        self.ds = np.sum(d_a * (np.dot(x, - self.w.T * self.w.T)), axis=0)
        self.dt = np.sum(x * (np.dot(d_a, self.w * self.w)), axis=0)
        d_x = np.dot(d_a, self.w)
        if __debug__:
            print self.name, "backward", d_a.shape, "to", d_x.shape
        return d_x

    def update(self, lr=0.01):
        self.s = self.s - lr * self.ds
        self.ds.fill(0.)
        self.t = self.t - lr * self.dt
        self.dt.fill(0.)


        

class BlockCircFC(object):
    def __init__(self, I, H, name=None, partition_size=4):
        # I : input size
        # H : hidden size
        self.c = init_w([H, 1])
        self.dc = np.zeros(self.c.shape)

	def block_indx(k, rc, cc):
            rc = int((rc+k-1)/k) * k
            cc = int((cc+k-1)/k) * k
            i = np.arange(0,k,1).reshape([1,k])
            j = np.arange(0,-k,-1).reshape([k,1])
            indx = i + j
            indx = (indx + k) % k
            m = np.tile(indx, [int(rc/k), int(cc/k)])
            offset = np.arange(0,rc*cc)
            i = (offset / cc) / k
            j = (offset % cc) / k
            offset = (i * cc + j * k).reshape([rc,cc])
            return m + offset

        self.p = partition_size
        assert 0 == H % self.p 
        assert 0 == I % self.p 
        self.r = init_w([H * I / self.p])
        self.dr = np.zeros(self.r.shape)
        self.idx = block_indx(self.p, H, I)
        self.name = name


    def forward(self, x):
        self.w = self.r[self.idx]
        a = np.dot(x, self.w.T) + self.c.T # a = wx + c
        if __debug__:
            print self.name, "forward", x.shape, "to", a.shape
        return a

    def backward(self, x, d_a):
        self.dw = np.dot(d_a.T, x)
        self.dc = np.dot(d_a.T, np.ones([x.shape[0], 1]))
        d_x = np.dot(d_a, self.w) # this is for next backpropagate layer
        #https://docs.scipy.org/doc/numpy/reference/generated/numpy.bincount.html
        self.dr = np.bincount(self.idx.flatten(), weights=self.dw.flatten()) 
        if __debug__:
            print self.name, "backward", d_a.shape, "to", d_x.shape
        return d_x

    def update(self, lr=0.01):
        self.r = self.w - lr * self.dw
        self.dr.fill(0.)
        self.c = self.c - lr * self.dc
        self.dc.fill(0.)




class FC(object):
    def __init__(self, I, H, name=None):
        # I : input size
        # H : hidden size
        self.w = init_w([H, I])
        self.dw = np.zeros(self.w.shape)
        self.c = init_w([H, 1])
        self.dc = np.zeros(self.c.shape)

        self.name = name

    def forward(self, x):
        a = np.dot(x, self.w.T) + self.c.T # a = wx + c
        if __debug__:
            print self.name, "forward", x.shape, "to", a.shape
        return a

    def backward(self, x, d_a):
        self.dw = np.dot(d_a.T, x)
        self.dc = np.dot(d_a.T, np.ones([x.shape[0], 1]))
        d_x = np.dot(d_a, self.w) # this is for next backpropagate layer
        if __debug__:
            print self.name, "backward", d_a.shape, "to", d_x.shape
        return d_x

    def update(self, lr=0.01):
        self.w = self.w - lr * self.dw
        self.dw.fill(0.)
        self.c = self.c - lr * self.dc
        self.dc.fill(0.)





class BaseConv(object):
    """
    This is only for two matrix doing convolution
    """

    def __init__(self, I, name=None):
        # I : input size
        self.I = I
        self.w = init_w([self.I, self.I])
        self.dw = np.zeros(self.w.shape)

        self.name = name

    def forward(self, x):
        self.dw = 0 # this is to clear, corresponding to the accumulation in backward
        w = self.w.ravel()[::-1].reshape([self.I, self.I])
        s = [self.I + x.shape[0] - 1, self.I + x.shape[1] - 1]
        r = np.fft.irfft2(np.fft.rfft2(w, s) * np.fft.rfft2(x, s), s)[(self.I-1):(x.shape[0]), (self.I-1):(x.shape[1])]
        if __debug__:
            fr = np.zeros([x.shape[0] - self.w.shape[0] + 1, x.shape[1] - self.w.shape[1] + 1])
            for i in xrange(r.shape[0]):
                for j in xrange(r.shape[1]):
                    fr[i,j] = np.sum( self.w * x[i:i+self.w.shape[0],j:j+self.w.shape[1]] )
            assert np.allclose(fr, r)
            print self.name, "forward", x.shape, "to", r.shape
        return r

    def backward(self, x, d_a):
        da = d_a.ravel()[::-1].reshape(d_a.shape)
        s = [da.shape[0] + x.shape[0] - 1, da.shape[1] + x.shape[1] - 1]
        dw = np.fft.irfft2(np.fft.rfft2(da, s) * np.fft.rfft2(x, s), s)
        dw = dw[(d_a.shape[0]-1):(x.shape[0]), (d_a.shape[1]-1):(x.shape[1])]
        self.dw += dw # !!!!!! notice that this is for multi-channel

        s = [d_a.shape[0] + self.I - 1, d_a.shape[1] + self.I - 1]
        d_x = np.fft.irfft2(np.fft.rfft2(d_a, s) * np.fft.rfft2(self.w, s), s)

        if __debug__:
            fdw = np.zeros(self.dw.shape)
            for a in xrange(self.w.shape[0]):
                for b in xrange(self.w.shape[1]):
                    fdw[a,b] = np.sum(d_a * x[a:a+d_a.shape[0],b:b+d_a.shape[1]])
            assert np.allclose(fdw, dw)

            fdx = np.zeros(x.shape) # this is for next backpropagate layer
            assert d_a.shape[0] + self.w.shape[0] - 1 == d_x.shape[0]
            assert d_a.shape[1] + self.w.shape[1] - 1 == d_x.shape[1]
            for i in xrange(d_a.shape[0]):
                for j in xrange(d_a.shape[1]):
                    for a in xrange(self.w.shape[0]):
                        for b in xrange(self.w.shape[1]):
                            fdx[i+a,j+b] += d_a[i,j] * self.w[a, b]
            assert np.allclose(fdx, d_x)
            print self.name, "backward", d_a.shape, "to", d_x.shape
        return d_x

    def update(self, lr=0.01):
        self.w = self.w - lr * self.dw
        self.dw.fill(0.)




class Conv(object):
    def __init__(self, (iN, iC, iW, iD), (oN, oC, oW, oD), name=None):
        # (batch_size, channels, width, height)
        # assume stride is 1
        assert iN == oN
        filter_size = iW - oW + 1
        self.c = iC
        self.f = oC
        self.b = [[BaseConv(filter_size, (name + '_tmp_i%d_o%d' % (i, j))) for i in xrange(self.c)] for j in xrange(self.f)]
        self.w = oW
        self.name = name

    def forward(self, x):
        a = np.zeros([x.shape[0], self.f, self.w, self.w])
        for i in xrange(a.shape[0]):
            for f in xrange(self.f):
                for c in xrange(self.c):
                    a[i,f,:,:] += self.b[f][c].forward(x[i,c,:,:])
        if __debug__:
            print self.name, "forward", x.shape, "to", a.shape
        return a

    def backward(self, x, d_a):
        d_x = np.zeros(x.shape)
        for i in xrange(d_a.shape[0]):
            for f in xrange(self.f):
                for c in xrange(self.c):
                    d_x[i,c,:,:] += self.b[f][c].backward(x[i,c,:,:], d_a[i,f,:,:])
        if __debug__:
            print self.name, "backward", d_a.shape, "to", d_x.shape
        return d_x

    def update(self, lr=0.01):
        for c in self.c:
            c.update(lr)




class Pooling(object):
    def __init__(self, (iN, iC, iW, iH), k, name=None):
        # (batch_size, channels, width, height)
        # assume stride is 1
        # max pooling k by k
        self.k = k
        self.name = name

        self.indx = np.arange(iN * iC * iW * iH).reshape(-1, iW, iH)
        self.indx = self.indx.reshape(-1, iW/self.k, self.k, iH/self.k, self.k)
        self.indx = np.swapaxes(self.indx, 2, 3)
        self.indx = self.indx.reshape(-1, self.k * self.k)

    def forward(self, x):
        assert 4 == len(x.shape)
        new_x = x.ravel()
        self.maxindx = np.argmax(new_x[self.indx], axis=0)
        a = x[self.maxindx]
        return a

    def backward(self, x, d_a):
        d_x = np.zeros(x.shape)
        d_x[self.maxindx][:] = d_a.ravel()[:]
        return d_x

    def update(selfself, lr=0.01):
        pass








sigmoid = lambda x: 1. / (1. + np.exp(-x))


class Sigmoid(object):
    def __init__(self, name=None):
        self.name = name

    def forward(self, a):
        b = sigmoid(a)
        if __debug__:
            print self.name, "forward", a.shape, "to", b.shape
        return b

    def backward(self, a, d_b):
        d_a = d_b * sigmoid(a) * (1 - sigmoid(a)) # siga for sigmoid(a)
        if __debug__:
            print self.name, "backward", d_b.shape, "to", d_a.shape
        return d_a

    def update(self):
        pass



class Tanh(object):
    def __init__(self, name=None):
        self.name = name

    def forward(self, a):
        b = np.tanh(a)
        if __debug__:
            print self.name, "forward", a.shape, "to", b.shape
        return b

    def backward(self, a, d_b):
        d_a = d_b * (1 - np.tanh(a)**2)
        if __debug__:
            print self.name, "backward", d_b.shape, "to", d_a.shape
        return d_a

    def update(self):
        pass

    
    
# http://stackoverflow.com/questions/32546020/neural-network-backpropagation-with-relu
class ReLU(object):
    def __init__(self, name=None):
        self.name = name

    def forward(self, a):
        b = np.copy(a)
        b[b <= 0] = 0
        if __debug__:
            print self.name, "forward", a.shape, "to", b.shape
        return b

    def backward(self, a, d_b):
        d_a = np.copy(d_b)
        d_a[a <= 0] = 0
        if __debug__:
            print self.name, "backward", d_b.shape, "to", d_a.shape
        return d_a

    def update(self, lr=0.01):
        pass



# http://mochajl.readthedocs.io/en/latest/user-guide/neuron.html
class LeakyReLU(object):
    def __init__(self, name=None, r=0.01):
        self.name = name
        self.r = r

    def forward(self, a):
        b = np.copy(a)
        b[b <= 0] *= self.r
        if __debug__:
            print self.name, "forward", a.shape, "to", b.shape
        return b

    def backward(self, a, d_b):
        d_a = np.copy(d_b)
        d_a[a <= 0] *= self.r
        if __debug__:
            print self.name, "backward", d_b.shape, "to", d_a.shape
        return d_a

    def update(self, lr=0.01):
        pass



class EmbeddingLayer(object):                                                      
    def __init__(self, M, H, name=None):                                           
        self.w = init_w([M, H])                                                    
        self.dw = np.zeros(self.w.shape)                                           
        self.name = name                                                           
                                                                                   
    def forward(self, x):                                                          
        a = self.w[x]                                                              
        if __debug__:                                                              
            print self.name, "forward", x.shape, "to", a.shape                     
        return a                                                                   
                                                                                   
    def backward(self, x, d_a):                                                    
        d_a = d_a.reshape([-1, d_a.shape[-1]]) #(-1, H)                            
        for i, v in enumerate(x.ravel()):                                          
            self.dw[v] += d_a[i]                                                   
        if __debug__:                                                              
            print self.name, "backward", d_a.shape, "to None"                      
        return None                                                                
                                                                                   
    def update(self, lr=0.01):                                                     
        self.w = self.w - lr * self.dw                                             
        self.dw.fill(0.) 

    
   
	
class ReduceMeanLayer(object):                                                     
                                                                                   
    def __init__(self, axis, name=None):                                           
        self.name = name                                                           
        self.axis = axis                                                           
                                                                                   
    def forward(self, x):                                                          
        a = np.mean(x, self.axis)                                                  
        if __debug__:                                                              
            print self.name, "forward", x.shape, "to", a.shape                     
        return a                                                                
                                                                                
    def backward(self, x, d_a):                                                 
        s = list(d_a.shape)                                                     
        s.insert(self.axis, 1)                                                  
        d_a = d_a.reshape(s) / x.shape[self.axis]                               
        d_x = np.repeat(d_a, x.shape[self.axis], self.axis)                     
        if __debug__:                                                           
            print self.name, "backward", d_a.shape, "to", x.shape               
        return d_x                                                              
                                                                                
    def update(self, lr=0.01):                                                  
        pass 
	
	
    

class EuclideanLoss(object):

    def forward(self, pred, target):
        cost = 0.5 * np.sum(((pred - target)**2))
        if __debug__:
            print "euclidean loss", cost
        return cost

    def backward(self, pred, target):
        assert pred.shape == target.shape
        d_b = pred - target
        if __debug__:
            print "euclidean loss backward", d_b.shape
        return d_b



class SoftmaxCrossEntropyLoss(object):

    def __init__(self, name=None):
        self.name = name
        self.prob = None

    def forward(self, x, target): # example, x = [0.6,-0.4,0,2.1], target = 3
        e_x = np.exp(x - x.max(axis=1)[:, None])
        self.prob = e_x / e_x.sum(axis=1)[:, None]
        cost =  np.sum( - np.log(np.maximum(self.prob[np.arange(x.shape[0]), np.ravel(target)], 1e-6) ) )
        if __debug__:
            print "SoftmaxCrossEntropyLoss", cost
        return cost

    def backward(self, x, target):
        d_b = np.copy(self.prob)
        d_b[np.arange(x.shape[0]), np.ravel(target)] -= 1.
        if __debug__:
            print "SoftmaxCrossEntropyLoss backward", d_b.shape
        return d_b


class HuffmanNode(object):                                                      
    def __init__(self, left=None, right=None, idx=None):                        
        self.left = left                                                        
        self.right = right                                                      
        self.idx = idx                                                          
    def children(self):                                                         
        return((self.left, self.right))                                         
                                                                                
def create_tree(frequencies):                                                   
    p = queue.PriorityQueue()                                                   
    cnt = 0                                                                     
    for k,v in frequencies.items():# 1. Create a leaf node for each symbol      
        p.put((v,k,cnt))               #    and add it to the priority queue    
        cnt+=1                                                                  
    while p.qsize() > 1:           # 2. While there is more than one node       
        l, r = p.get(), p.get()    # 2a. remove two highest nodes               
        node = HuffmanNode(l, r, cnt)   # 2b. create internal node with children
        p.put((l[0]+r[0], node))   # 2c. add new node to queue                  
        cnt += 1                                                                
    return p.get()                 # 3. tree is complete - return root node     
                                                                                
def walk_tree(node, prefix="", code={}, prepath=[], path={}):                   
    if isinstance(node[1].left[1], HuffmanNode):                                
        walk_tree(node[1].left,prefix+"0", code, prepath+[node[1].idx])         
    else:                                                                       
        code[node[1].left[1]]=prefix+"0"                                        
        path[node[1].left[1]]=prepath+[node[1].left[2]]                         
    if isinstance(node[1].right[1],HuffmanNode):                                
        walk_tree(node[1].right,prefix+"1", code, prepath+[node[1].idx])        
    else:                                                                       
        code[node[1].right[1]]=prefix+"1"                                       
        path[node[1].right[1]]=prepath+[node[1].right[2]]                       
    return(code, path)                                                          
                                                                                
def encode(freq):                                                               
    root = create_tree(freq)                                                    
    code, path = walk_tree(root)                                                
    return [(x, code.get(x, 0), path.get(x, 0)) for x in set(code).union(path)], rootmmnnnnnnnnnnnnnmmnnnnnmmmmmmmmmmmmmmmmmmmnnnn


class HierarchicalSoftmaxLoss(object):                                             
    def __init__(self, H, O, root, path, code, name=None):                         
        self.name = name                                                           
        self.w = init_w([np.max(np.max(path))+1, H])                               
        self.dw = np.zeros(self.w.shape)                                           
        self.root = root                                                           
        self.path = path                                                           
        self.code = code                                                           
                                                                                   
    def forward(self, h, y):                                                       
        loss = 0                                                                   
        for idx, i in enumerate(y):                                                
            path = self.path[i]                                                    
            vecs = self.w[path]                                                    
            tmp  = np.dot(vecs, h[idx])                                            
            prob = sigmoid(tmp)                                                    
            code = np.array(self.code[i])                                          
            loss += np.sum(code * np.log(prob) + (1-code) * np.log(1-prob))        
        return loss                                                                
                                                                                   
    def backward(self, h, y):                                                      
        loss = 0                                                                   
        d_h = np.zeros(h.shape) # (B, H)                                           
        for idx, i in enumerate(y):                                                
            path = self.path[i]                                                    
            vecs = self.w[path] #(L, H)                                            
            tmp  = np.dot(vecs, h[idx]).reshape([-1,1]) #(L, 1)                    
            prob = sigmoid(tmp) #(L, 1)                                            
            code = np.array(self.code[i]).reshape([-1,1]) # (L, 1)                 
            self.dw[path] += (code-prob) * h[idx] #(L, H)                          
            d_h[idx] += np.sum((prob-code) * vecs, axis=0)                         
        return d_h                                                                 
                                                                                   
    def update(self, lr=0.01):                                                     
        self.w = self.w - lr * self.dw                                             
        self.dw.fill(0.) 



def GradientChecking1():
    # this is to just check network can go both forward and backward
    B = 3  # batch size
    I = 5  # input size
    H = 11 # hidden size
    O = 7   # output size

    x = init_w([B, I])
    y = np.asarray(np.sum(np.sin(x), axis=1).reshape(B, 1), np.int)

    layers = [FC(I, H, "fc1"), Sigmoid("sig1"), FC(H, O, "fc2"), Sigmoid("sig2")]
    nlayers = len(layers)

    # forward and backward

    # inputs[i] is the input for i-th layer
    # the last of inputs[i] must be the output of current network
    inputs = [x]
    for i in xrange(nlayers):
        inputs.append( layers[i].forward(inputs[-1]) ) # inputs[i] is the input for i-th layer

    cost = SoftmaxCrossEntropyLoss()
    loss = cost.forward(inputs[-1], y)

    # grads[i] is the gradients for i-th layer, but in the reverse order
    grads = [cost.backward(inputs[-1], y)]
    for i in reversed(xrange(nlayers)):
        grads.append( layers[i].backward(inputs[i], grads[-1]) ) # grads[i]

    for l in layers:
        l.update()

    print "Successfully go forward and backward through all layers"




def fwd(x, y, layers, cost):
    inputs = [x]
    nlayers = len(layers)
    for i in xrange(nlayers):
        inputs.append( layers[i].forward(inputs[-1]) ) # inputs[i] is the input for i-th layer
    loss = cost.forward(inputs[-1], y)
    return loss


def GradientChecking2():
    # this is to check fully connected layer
    B = 3  # batch size
    I = 7  # input size
    O = I   # output size

    x = init_w([B, I])
    y = np.asarray(np.sum(np.sin(x), axis=1).reshape(B, 1), np.int)
    #y = np.sum(np.sin(x), axis=1).reshape(B, O)

    layers = [FC(I, O, "fc1")]
    nlayers = len(layers)

    # forward and backward

    # inputs[i] is the input for i-th layer
    # the last of inputs[i] must be the output of current network
    inputs = [x]
    for i in xrange(nlayers):
        inputs.append( layers[i].forward(inputs[-1]) ) # inputs[i] is the input for i-th layer

    cost = SoftmaxCrossEntropyLoss()
    loss = cost.forward(inputs[-1], y)

    # grads[i] is the gradients for i-th layer, but in the reverse order
    grads = [cost.backward(inputs[-1], y)]
    for i in reversed(xrange(nlayers)):
        grads.append( layers[i].backward(inputs[i], grads[-1]) ) # grads[i]

    # following checking method is from https://gist.github.com/karpathy/587454dc0146a6ae21fc
    delta = 1e-5
    rel_error_thr_warning = 1e-2
    rel_error_thr_error = 1

    checklist = [layers[0].w, layers[0].c]
    grads_analytic = [layers[0].dw, layers[0].dc]
    names = ['w', 'c']
    for j in xrange(len(checklist)):
        mat = checklist[j]
        dmat = grads_analytic[j]
        name = names[j]
        for i in xrange(mat.size):
            old_val = mat.flat[i]

            # test f(x + delta_x)
            mat.flat[i] = old_val + delta
            loss0 = fwd(x, y, layers, cost)

            # test f(x - delta_x)
            mat.flat[i] = old_val - delta
            loss1 = fwd(x, y, layers, cost)

            mat.flat[i] = old_val # recover

            grad_analytic = dmat.flat[i]
            grad_numerical = (loss0 - loss1) / (2 * delta)

            if grad_numerical == 0 and grad_analytic == 0:
                rel_error = 0 # both are zero, OK.
                status = 'OK'
            elif abs(grad_numerical) < 1e-7 and abs(grad_analytic) < 1e-7:
                rel_error = 0 # not enough precision to check this
                status = 'VAL SMALL WARNING'
            else:
                rel_error = abs(grad_analytic - grad_numerical) / abs(grad_numerical + grad_analytic)
                status = 'OK'
                if rel_error > rel_error_thr_warning: status = 'WARNING'
                if rel_error > rel_error_thr_error: status = '!!!DANGEROUS ERROR!!!'

            print '%s checking param %s index %s (val = %+8f), analytic = %+8f, numerical = %+8f, relative error = %+8f' \
                    % (status, name, `np.unravel_index(i, mat.shape)`, old_val, grad_analytic, grad_numerical, rel_error)

    print "Finish checking fully connected"


def GradientChecking3():
    # this is to check fully connected layer
    B = 3  # batch size
    I = 7  # input size
    H = 19
    O = I   # output size

    x = init_w([B, I])
    y = np.sin(x)
    #y = np.sum(np.sin(x), axis=1).reshape(B, O)

    layers = [CircFC(I, H, "CircFc1"), CircFC(H, O, "CircFc2")]
    nlayers = len(layers)

    # forward and backward

    # inputs[i] is the input for i-th layer
    # the last of inputs[i] must be the output of current network
    inputs = [x]
    for i in xrange(nlayers):
        inputs.append( layers[i].forward(inputs[-1]) ) # inputs[i] is the input for i-th layer

    cost = EuclideanLoss()
    # loss = cost.forward(inputs[-1], y)

    # grads[i] is the gradients for i-th layer, but in the reverse order
    grads = [cost.backward(inputs[-1], y)]
    for i in reversed(xrange(nlayers)):
        grads.append( layers[i].backward(inputs[i], grads[-1]) ) # grads[i]

    # following checking method is from https://gist.github.com/karpathy/587454dc0146a6ae21fc
    delta = 1e-5
    rel_error_thr_warning = 1e-2
    rel_error_thr_error = 1

    checklist = [layers[0].r, layers[1].r]
    grads_analytic = [layers[0].dr, layers[1].dr]
    names = ['r0', 'r1']
    for j in xrange(len(checklist)):
        mat = checklist[j]
        dmat = grads_analytic[j]
        name = names[j]
        for i in xrange(mat.size):
            old_val = mat.flat[i]

            # test f(x + delta_x)
            mat.flat[i] = old_val + delta
            loss0 = fwd(x, y, layers, cost)

            # test f(x - delta_x)
            mat.flat[i] = old_val - delta
            loss1 = fwd(x, y, layers, cost)

            mat.flat[i] = old_val # recover

            grad_analytic = dmat.flat[i]
            grad_numerical = (loss0 - loss1) / (2 * delta)

            if grad_numerical == 0 and grad_analytic == 0:
                rel_error = 0 # both are zero, OK.
                status = 'OK'
            elif abs(grad_numerical) < 1e-7 and abs(grad_analytic) < 1e-7:
                rel_error = 0 # not enough precision to check this
                status = 'VAL SMALL WARNING'
            else:
                rel_error = abs(grad_analytic - grad_numerical) / abs(grad_numerical + grad_analytic)
                status = 'OK'
                if rel_error > rel_error_thr_warning: status = 'WARNING'
                if rel_error > rel_error_thr_error: status = '!!!DANGEROUS ERROR!!!'

            print '%s checking param %s index %s (val = %+8f), analytic = %+8f, numerical = %+8f, relative error = %+8f' \
                    % (status, name, `np.unravel_index(i, mat.shape)`, old_val, grad_analytic, grad_numerical, rel_error)

    print "Finish checking fully connected"



def GradientChecking4():
    # this is to check fully connected layer
    B = 3  # batch size
    I = 8  # input size
    H = 20
    O = I   # output size

    x = init_w([B, I])
    y = np.sin(x)
    #y = np.sum(np.sin(x), axis=1).reshape(B, O)

    layers = [CircFC_fft(I, H, "CircFc1"), CircFC_fft(H, O, "CircFc2")]
    nlayers = len(layers)

    # forward and backward

    # inputs[i] is the input for i-th layer
    # the last of inputs[i] must be the output of current network
    inputs = [x]
    for i in xrange(nlayers):
        inputs.append( layers[i].forward(inputs[-1]) ) # inputs[i] is the input for i-th layer

    cost = EuclideanLoss()
    # loss = cost.forward(inputs[-1], y)

    # grads[i] is the gradients for i-th layer, but in the reverse order
    grads = [cost.backward(inputs[-1], y)]
    for i in reversed(xrange(nlayers)):
        grads.append( layers[i].backward(inputs[i], grads[-1]) ) # grads[i]

    # following checking method is from https://gist.github.com/karpathy/587454dc0146a6ae21fc
    delta = 1e-5
    rel_error_thr_warning = 1e-2
    rel_error_thr_error = 1

    checklist = [layers[0].r, layers[1].r]
    grads_analytic = [np.fft.irfft(layers[0].dr, n=layers[0].k), np.fft.irfft(layers[1].dr, n=layers[1].k)]
    names = ['r0', 'r1']
    for j in xrange(len(checklist)):
        mat = np.fft.irfft(checklist[j], n=layers[j].k) # this is different from other grad tests
        dmat = grads_analytic[j]
        name = names[j]
        for i in xrange(mat.size):
            old_val = mat.flat[i]

            # test f(x + delta_x)
            mat.flat[i] = old_val + delta
            #checklist[j] = np.fft.rfft(mat)
            layers[j].r = np.fft.rfft(mat, n=layers[j].k)
            loss0 = fwd(x, y, layers, cost)

            # test f(x - delta_x)
            mat.flat[i] = old_val - delta
            #checklist[j] = np.fft.rfft(mat)
            layers[j].r = np.fft.rfft(mat, n=layers[j].k)
            loss1 = fwd(x, y, layers, cost)

            mat.flat[i] = old_val # recover

            grad_analytic = dmat.flat[i]
            grad_numerical = (loss0 - loss1) / (2 * delta)

            if grad_numerical == 0 and grad_analytic == 0:
                rel_error = 0 # both are zero, OK.
                status = 'OK'
            elif abs(grad_numerical) < 1e-7 and abs(grad_analytic) < 1e-7:
                rel_error = 0 # not enough precision to check this
                status = 'VAL SMALL WARNING'
            else:
                rel_error = abs(grad_analytic - grad_numerical) / abs(grad_numerical + grad_analytic)
                status = 'OK'
                if rel_error > rel_error_thr_warning: status = 'WARNING'
                if rel_error > rel_error_thr_error: status = '!!!DANGEROUS ERROR!!!'

            print '%s checking param %s index %s (val = %+8f), analytic = %+8f, numerical = %+8f, relative error = %+8f' \
                    % (status, name, `np.unravel_index(i, mat.shape)`, old_val, grad_analytic, grad_numerical, rel_error)

    print "Finish checking fully connected"


def GradientChecking5():
    x = np.random.random([15,15])
    y = np.random.random([11,11]) # randomly selected

    layers = [BaseConv(3, 'base0'), BaseConv(3, 'base1')]
    nlayers = len(layers)

    # forward and backward

    # inputs[i] is the input for i-th layer
    # the last of inputs[i] must be the output of current network
    inputs = [x]
    for i in xrange(nlayers):
        inputs.append( layers[i].forward(inputs[-1]) ) # inputs[i] is the input for i-th layer

    cost = EuclideanLoss()
    # loss = cost.forward(inputs[-1], y)

    # grads[i] is the gradients for i-th layer, but in the reverse order
    grads = [cost.backward(inputs[-1], y)]
    for i in reversed(xrange(nlayers)):
        grads.append( layers[i].backward(inputs[i], grads[-1]) ) # grads[i]

    delta = 1e-5
    rel_error_thr_warning = 1e-2
    rel_error_thr_error = 1

    checklist = [layers[i].w for i in xrange(nlayers)]
    grads_analytic = [layers[i].dw for i in xrange(nlayers)]
    names = [layers[i].name for i in xrange(nlayers)]
    for j in xrange(len(checklist)):
        mat = checklist[j]
        dmat = grads_analytic[j]
        name = names[j]
        for i in xrange(mat.size):
            old_val = mat.flat[i]

            # test f(x + delta_x)
            mat.flat[i] = old_val + delta
            loss0 = fwd(x, y, layers, cost)

            # test f(x - delta_x)
            mat.flat[i] = old_val - delta
            loss1 = fwd(x, y, layers, cost)

            mat.flat[i] = old_val # recover

            grad_analytic = dmat.flat[i]
            grad_numerical = (loss0 - loss1) / (2 * delta)

            if grad_numerical == 0 and grad_analytic == 0:
                rel_error = 0 # both are zero, OK.
                status = 'OK'
            elif abs(grad_numerical) < 1e-7 and abs(grad_analytic) < 1e-7:
                rel_error = 0 # not enough precision to check this
                status = 'VAL SMALL WARNING'
            else:
                rel_error = abs(grad_analytic - grad_numerical) / abs(grad_numerical + grad_analytic)
                status = 'OK'
                if rel_error > rel_error_thr_warning: status = 'WARNING'
                if rel_error > rel_error_thr_error: status = '!!!DANGEROUS ERROR!!!'

            print '%s checking param %s index %s (val = %+8f), analytic = %+8f, numerical = %+8f, relative error = %+8f' \
                    % (status, name, `np.unravel_index(i, mat.shape)`, old_val, grad_analytic, grad_numerical, rel_error)





def GradientChecking6():
    x = np.random.random([10,3,17,17])
    y = np.zeros([10,7,3,3])
    y[:,:,:,:] = np.random.random([10,7,3,3]) # randomly selected

    layers = [Conv(x.shape, (10,5,13,13), 'conv0'), Conv((10,5,13,13), y.shape, 'conv1')]
    #layers = [Conv(x.shape, y.shape, 'conv0')]
    nlayers = len(layers)

    # forward and backward

    # inputs[i] is the input for i-th layer
    # the last of inputs[i] must be the output of current network
    inputs = [x]
    for i in xrange(nlayers):
        inputs.append( layers[i].forward(inputs[-1]) ) # inputs[i] is the input for i-th layer

    cost = EuclideanLoss()
    # loss = cost.forward(inputs[-1], y)

    # grads[i] is the gradients for i-th layer, but in the reverse order
    grads = [cost.backward(inputs[-1], y)]
    for i in reversed(xrange(nlayers)):
        grads.append( layers[i].backward(inputs[i], grads[-1]) ) # grads[i]

    delta = 1e-5
    rel_error_thr_warning = 1e-2
    rel_error_thr_error = 1

    checklist = [bi.w for i in xrange(nlayers) for b in layers[i].b for bi in b]
    grads_analytic = [bi.dw for i in xrange(nlayers) for b in layers[i].b for bi in b]
    names = [bi.name for i in xrange(nlayers) for b in layers[i].b for bi in b]
    for j in xrange(len(checklist)):
        mat = checklist[j]
        dmat = grads_analytic[j]
        name = names[j]
        for i in xrange(mat.size):
            old_val = mat.flat[i]

            # test f(x + delta_x)
            mat.flat[i] = old_val + delta
            loss0 = fwd(x, y, layers, cost)

            # test f(x - delta_x)
            mat.flat[i] = old_val - delta
            loss1 = fwd(x, y, layers, cost)

            mat.flat[i] = old_val # recover

            grad_analytic = dmat.flat[i]
            grad_numerical = (loss0 - loss1) / (2 * delta)

            if grad_numerical == 0 and grad_analytic == 0:
                rel_error = 0 # both are zero, OK.
                status = 'OK'
            elif abs(grad_numerical) < 1e-7 and abs(grad_analytic) < 1e-7:
                rel_error = 0 # not enough precision to check this
                status = 'VAL SMALL WARNING'
            else:
                rel_error = abs(grad_analytic - grad_numerical) / abs(grad_numerical + grad_analytic)
                status = 'OK'
                if rel_error > rel_error_thr_warning: status = 'WARNING'
                if rel_error > rel_error_thr_error: status = '!!!DANGEROUS ERROR!!!'

            print '%s checking param %s index %s (val = %+8f), analytic = %+8f, numerical = %+8f, relative error = %+8f' \
                    % (status, name, `np.unravel_index(i, mat.shape)`, old_val, grad_analytic, grad_numerical, rel_error)



                

def GradientChecking7():
    # this is to check fully connected layer
    B = 3  # batch size
    I = 7  # input size
    H = 19
    O = I   # output size

    x = init_w([B, I])
    y = np.sin(x)
    #y = np.sum(np.sin(x), axis=1).reshape(B, O)

    layers = [CauchyFC(I, H, "Cauchy1"), CauchyFC(H, O, "Cauchy1")]
    nlayers = len(layers)

    # forward and backward

    # inputs[i] is the input for i-th layer
    # the last of inputs[i] must be the output of current network
    inputs = [x]
    for i in xrange(nlayers):
        inputs.append( layers[i].forward(inputs[-1]) ) # inputs[i] is the input for i-th layer

    cost = EuclideanLoss()
    # loss = cost.forward(inputs[-1], y)

    # grads[i] is the gradients for i-th layer, but in the reverse order
    grads = [cost.backward(inputs[-1], y)]
    for i in reversed(xrange(nlayers)):
        grads.append( layers[i].backward(inputs[i], grads[-1]) ) # grads[i]

    # following checking method is from https://gist.github.com/karpathy/587454dc0146a6ae21fc
    delta = 1e-5
    rel_error_thr_warning = 1e-2
    rel_error_thr_error = 1

    checklist = [layers[0].s, layers[0].t, layers[1].s, layers[1].t]
    grads_analytic = [layers[0].ds, layers[0].dt, layers[1].ds, layers[1].dt]
    names = ['s0', 't0', 's1', 't1']
    for j in xrange(len(checklist)):
        mat = checklist[j]
        dmat = grads_analytic[j]
        name = names[j]
        for i in xrange(mat.size):
            old_val = mat.flat[i]

            # test f(x + delta_x)
            mat.flat[i] = old_val + delta
            loss0 = fwd(x, y, layers, cost)

            # test f(x - delta_x)
            mat.flat[i] = old_val - delta
            loss1 = fwd(x, y, layers, cost)

            mat.flat[i] = old_val # recover

            grad_analytic = dmat.flat[i]
            grad_numerical = (loss0 - loss1) / (2 * delta)

            if grad_numerical == 0 and grad_analytic == 0:
                rel_error = 0 # both are zero, OK.
                status = 'OK'
            elif abs(grad_numerical) < 1e-7 and abs(grad_analytic) < 1e-7:
                rel_error = 0 # not enough precision to check this
                status = 'VAL SMALL WARNING'
            else:
                rel_error = abs(grad_analytic - grad_numerical) / abs(grad_numerical + grad_analytic)
                status = 'OK'
                if rel_error > rel_error_thr_warning: status = 'WARNING'
                if rel_error > rel_error_thr_error: status = '!!!DANGEROUS ERROR!!!'

            print '%s checking param %s index %s (val = %+8f), analytic = %+8f, numerical = %+8f, relative error = %+8f' \
                    % (status, name, `np.unravel_index(i, mat.shape)`, old_val, grad_analytic, grad_numerical, rel_error)

    print "Finish checking fully connected"

    
    

def GradientChecking8():
    # this is to check fully connected layer
    B = 3  # batch size
    I = 7  # input size
    H = 17
    O = I   # output size

    x = init_w([B, I])
    y = np.sin(x)
    #y = np.sum(np.sin(x), axis=1).reshape(B, O)

    #layers = [NewCircFC(I, H, "CircFc1"), ReLU('relu0'), NewCircFC(H, O, "CircFc2")]
    layers = [NewCircFC(I, H, "CircFc1"), LeakyReLU('leakyrelu0'), NewCircFC(H, O, "CircFc2")]
    nlayers = len(layers)

    # forward and backward

    # inputs[i] is the input for i-th layer
    # the last of inputs[i] must be the output of current network
    inputs = [x]
    for i in xrange(nlayers):
        inputs.append( layers[i].forward(inputs[-1]) ) # inputs[i] is the input for i-th layer

    cost = EuclideanLoss()
    # loss = cost.forward(inputs[-1], y)

    # grads[i] is the gradients for i-th layer, but in the reverse order
    grads = [cost.backward(inputs[-1], y)]
    for i in reversed(xrange(nlayers)):
        grads.append( layers[i].backward(inputs[i], grads[-1]) ) # grads[i]

    # following checking method is from https://gist.github.com/karpathy/587454dc0146a6ae21fc
    delta = 1e-5
    rel_error_thr_warning = 1e-2
    rel_error_thr_error = 1

    checklist = [c.r for c in layers[0].c] + [c.r for c in layers[2].c]
    grads_analytic = [c.dr for c in layers[0].c] + [c.dr for c in layers[2].c]
    names = ['r%d' % i for i in xrange(len(checklist))]
    for j in xrange(len(checklist)):
        mat = checklist[j]
        dmat = grads_analytic[j]
        name = names[j]
        for i in xrange(mat.size):
            old_val = mat.flat[i]

            # test f(x + delta_x)
            mat.flat[i] = old_val + delta
            loss0 = fwd(x, y, layers, cost)

            # test f(x - delta_x)
            mat.flat[i] = old_val - delta
            loss1 = fwd(x, y, layers, cost)

            mat.flat[i] = old_val # recover

            grad_analytic = dmat.flat[i]
            grad_numerical = (loss0 - loss1) / (2 * delta)

            if grad_numerical == 0 and grad_analytic == 0:
                rel_error = 0 # both are zero, OK.
                status = 'OK'
            elif abs(grad_numerical) < 1e-7 and abs(grad_analytic) < 1e-7:
                rel_error = 0 # not enough precision to check this
                status = 'VAL SMALL WARNING'
            else:
                rel_error = abs(grad_analytic - grad_numerical) / abs(grad_numerical + grad_analytic)
                status = 'OK'
                if rel_error > rel_error_thr_warning: status = 'WARNING'
                if rel_error > rel_error_thr_error: status = '!!!DANGEROUS ERROR!!!'

            print '%s checking param %s index %s (val = %+8f), analytic = %+8f, numerical = %+8f, relative error = %+8f' \
                    % (status, name, `np.unravel_index(i, mat.shape)`, old_val, grad_analytic, grad_numerical, rel_error)

    print "Finish checking fully connected"




def GradientChecking9():
    # this is to check fully connected layer
    B = 3  # batch size
    I = 7  # input size
    H = 17
    O = I   # output size

    x = init_w([B, I])
    y = np.sin(x)
    #y = np.sum(np.sin(x), axis=1).reshape(B, O)

    layers = [NewCircFC2(I, H, 5, "CircFc1"), Sigmoid('relu0'), NewCircFC2(H, O, 4, "CircFc2")]
    #layers = [NewCircFC(I, H, "CircFc1"), LeakyReLU('leakyrelu0'), NewCircFC(H, O, "CircFc2")]
    nlayers = len(layers)

    # forward and backward

    # inputs[i] is the input for i-th layer
    # the last of inputs[i] must be the output of current network
    inputs = [x]
    for i in xrange(nlayers):
        inputs.append( layers[i].forward(inputs[-1]) ) # inputs[i] is the input for i-th layer

    cost = EuclideanLoss()
    # loss = cost.forward(inputs[-1], y)

    # grads[i] is the gradients for i-th layer, but in the reverse order
    grads = [cost.backward(inputs[-1], y)]
    for i in reversed(xrange(nlayers)):
        grads.append( layers[i].backward(inputs[i], grads[-1]) ) # grads[i]

    # following checking method is from https://gist.github.com/karpathy/587454dc0146a6ae21fc
    delta = 1e-5
    rel_error_thr_warning = 1e-2
    rel_error_thr_error = 1

    checklist = [c.r for c in layers[0].c] + [c.r for c in layers[2].c]
    grads_analytic = [c.dr for c in layers[0].c] + [c.dr for c in layers[2].c]
    names = ['r%d' % i for i in xrange(len(checklist))]
    for j in xrange(len(checklist)):
        mat = checklist[j]
        dmat = grads_analytic[j]
        name = names[j]
        for i in xrange(mat.size):
            old_val = mat.flat[i]

            # test f(x + delta_x)
            mat.flat[i] = old_val + delta
            loss0 = fwd(x, y, layers, cost)

            # test f(x - delta_x)
            mat.flat[i] = old_val - delta
            loss1 = fwd(x, y, layers, cost)

            mat.flat[i] = old_val # recover

            grad_analytic = dmat.flat[i]
            grad_numerical = (loss0 - loss1) / (2 * delta)

            if grad_numerical == 0 and grad_analytic == 0:
                rel_error = 0 # both are zero, OK.
                status = 'OK'
            elif abs(grad_numerical) < 1e-7 and abs(grad_analytic) < 1e-7:
                rel_error = 0 # not enough precision to check this
                status = 'VAL SMALL WARNING'
            else:
                rel_error = abs(grad_analytic - grad_numerical) / abs(grad_numerical + grad_analytic)
                status = 'OK'
                if rel_error > rel_error_thr_warning: status = 'WARNING'
                if rel_error > rel_error_thr_error: status = '!!!DANGEROUS ERROR!!!'

            print '%s checking param %s index %s (val = %+8f), analytic = %+8f, numerical = %+8f, relative error = %+8f' \
                    % (status, name, `np.unravel_index(i, mat.shape)`, old_val, grad_analytic, grad_numerical, rel_error)

    print "Finish checking fully connected"




def GradientChecking10():
    # this is to check fully connected layer
    B = 3  # batch size
    I = 7  # input size
    H = 17
    O = I   # output size

    x = init_w([B, I])
    y = np.sin(x)
    #y = np.sum(np.sin(x), axis=1).reshape(B, O)

    layers = [NewCircFC2(I, H, 5, "CircFc1"), Tanh('tanh0'), NewCircFC2(H, O, 4, "CircFc2")]
    #layers = [NewCircFC(I, H, "CircFc1"), LeakyReLU('leakyrelu0'), NewCircFC(H, O, "CircFc2")]
    nlayers = len(layers)

    # forward and backward

    # inputs[i] is the input for i-th layer
    # the last of inputs[i] must be the output of current network
    inputs = [x]
    for i in xrange(nlayers):
        inputs.append( layers[i].forward(inputs[-1]) ) # inputs[i] is the input for i-th layer

    cost = EuclideanLoss()
    # loss = cost.forward(inputs[-1], y)

    # grads[i] is the gradients for i-th layer, but in the reverse order
    grads = [cost.backward(inputs[-1], y)]
    for i in reversed(xrange(nlayers)):
        grads.append( layers[i].backward(inputs[i], grads[-1]) ) # grads[i]

    # following checking method is from https://gist.github.com/karpathy/587454dc0146a6ae21fc
    delta = 1e-5
    rel_error_thr_warning = 1e-2
    rel_error_thr_error = 1

    checklist = [c.r for c in layers[0].c] + [c.r for c in layers[2].c]
    grads_analytic = [c.dr for c in layers[0].c] + [c.dr for c in layers[2].c]
    names = ['r%d' % i for i in xrange(len(checklist))]
    for j in xrange(len(checklist)):
        mat = checklist[j]
        dmat = grads_analytic[j]
        name = names[j]
        for i in xrange(mat.size):
            old_val = mat.flat[i]

            # test f(x + delta_x)
            mat.flat[i] = old_val + delta
            loss0 = fwd(x, y, layers, cost)

            # test f(x - delta_x)
            mat.flat[i] = old_val - delta
            loss1 = fwd(x, y, layers, cost)

            mat.flat[i] = old_val # recover

            grad_analytic = dmat.flat[i]
            grad_numerical = (loss0 - loss1) / (2 * delta)

            if grad_numerical == 0 and grad_analytic == 0:
                rel_error = 0 # both are zero, OK.
                status = 'OK'
            elif abs(grad_numerical) < 1e-7 and abs(grad_analytic) < 1e-7:
                rel_error = 0 # not enough precision to check this
                status = 'VAL SMALL WARNING'
            else:
                rel_error = abs(grad_analytic - grad_numerical) / abs(grad_numerical + grad_analytic)
                status = 'OK'
                if rel_error > rel_error_thr_warning: status = 'WARNING'
                if rel_error > rel_error_thr_error: status = '!!!DANGEROUS ERROR!!!'

            print '%s checking param %s index %s (val = %+8f), analytic = %+8f, numerical = %+8f, relative error = %+8f' \
                    % (status, name, `np.unravel_index(i, mat.shape)`, old_val, grad_analytic, grad_numerical, rel_error)

    print "Finish checking fully connected"




def GradientChecking11():
    # this is to check fully connected layer
    B = 8  # batch size
    I = 16  # input size
    H = 32
    O = I   # output size

    x = init_w([B, I])
    y = np.sin(x)

    layers = [BlockCircFC(I, H, "BlockCircFc1"), LeakyReLU('leakyrelu0'), BlockCircFC(H, O, "BlockCircFc2")]
    nlayers = len(layers)

    # forward and backward

    # inputs[i] is the input for i-th layer
    # the last of inputs[i] must be the output of current network
    inputs = [x]
    for i in xrange(nlayers):
        inputs.append( layers[i].forward(inputs[-1]) ) # inputs[i] is the input for i-th layer

    cost = EuclideanLoss()
    # loss = cost.forward(inputs[-1], y)

    # grads[i] is the gradients for i-th layer, but in the reverse order
    grads = [cost.backward(inputs[-1], y)]
    for i in reversed(xrange(nlayers)):
        grads.append( layers[i].backward(inputs[i], grads[-1]) ) # grads[i]

    # following checking method is from https://gist.github.com/karpathy/587454dc0146a6ae21fc
    delta = 1e-5
    rel_error_thr_warning = 1e-2
    rel_error_thr_error = 1

    checklist = [layers[0].r, layers[0].c, layers[2].r, layers[2].c]
    grads_analytic = [layers[0].dr, layers[0].dc, layers[2].dr, layers[2].dc]
    names = ['r%d' % i for i in xrange(len(checklist))]
    for j in xrange(len(checklist)):
        mat = checklist[j]
        dmat = grads_analytic[j]
        name = names[j]
        for i in xrange(mat.size):
            old_val = mat.flat[i]

            # test f(x + delta_x)
            mat.flat[i] = old_val + delta
            loss0 = fwd(x, y, layers, cost)

            # test f(x - delta_x)
            mat.flat[i] = old_val - delta
            loss1 = fwd(x, y, layers, cost)

            mat.flat[i] = old_val # recover

            grad_analytic = dmat.flat[i]
            grad_numerical = (loss0 - loss1) / (2 * delta)

            if grad_numerical == 0 and grad_analytic == 0:
                rel_error = 0 # both are zero, OK.
                status = 'OK'
            elif abs(grad_numerical) < 1e-7 and abs(grad_analytic) < 1e-7:
                rel_error = 0 # not enough precision to check this
                status = 'VAL SMALL WARNING'
            else:
                rel_error = abs(grad_analytic - grad_numerical) / abs(grad_numerical + grad_analytic)
                status = 'OK'
                if rel_error > rel_error_thr_warning: status = 'WARNING'
                if rel_error > rel_error_thr_error: status = '!!!DANGEROUS ERROR!!!'

            print '%s checking param %s index %s (val = %+8f), analytic = %+8f, numerical = %+8f, relative error = %+8f' \
                    % (status, name, `np.unravel_index(i, mat.shape)`, old_val, grad_analytic, grad_numerical, rel_error)

    print "Finish checking fully connected"






def GradientChecking12():
    # this is to check fully connected layer
    B = 8  # batch size
    I = 8  # input size
    H = 8
    O = I   # output size

    x = init_w([B, I])
    y = np.sin(x)

    layers = [DisplaceFC(I, H, "DisplaceFC1"), LeakyReLU('leakyrelu0'), DisplaceFC(H, O, "DisplaceFC2")]
    nlayers = len(layers)

    # forward and backward

    # inputs[i] is the input for i-th layer
    # the last of inputs[i] must be the output of current network
    inputs = [x]
    for i in xrange(nlayers):
        inputs.append( layers[i].forward(inputs[-1]) ) # inputs[i] is the input for i-th layer

    cost = EuclideanLoss()
    # loss = cost.forward(inputs[-1], y)

    # grads[i] is the gradients for i-th layer, but in the reverse order
    grads = [cost.backward(inputs[-1], y)]
    for i in reversed(xrange(nlayers)):
        grads.append( layers[i].backward(inputs[i], grads[-1]) ) # grads[i]

    # following checking method is from https://gist.github.com/karpathy/587454dc0146a6ae21fc
    delta = 1e-5
    rel_error_thr_warning = 1e-2
    rel_error_thr_error = 1

    checklist = [layers[0].g, layers[0].h, layers[0].c, layers[2].g, layers[2].h, layers[2].c]
    grads_analytic = [layers[0].dg, layers[0].dh, layers[0].dc, layers[2].dg, layers[2].dh, layers[2].dc]
    names = ['0g', '0h', '0c', '2g', '2h', '2c' ]
    for j in xrange(len(checklist)):
        mat = checklist[j]
        dmat = grads_analytic[j]
        name = names[j]
        for i in xrange(mat.size):
            old_val = mat.flat[i]

            # test f(x + delta_x)
            mat.flat[i] = old_val + delta
            loss0 = fwd(x, y, layers, cost)

            # test f(x - delta_x)
            mat.flat[i] = old_val - delta
            loss1 = fwd(x, y, layers, cost)

            mat.flat[i] = old_val # recover

            grad_analytic = dmat.flat[i]
            grad_numerical = (loss0 - loss1) / (2 * delta)

            if grad_numerical == 0 and grad_analytic == 0:
                rel_error = 0 # both are zero, OK.
                status = 'OK'
            elif abs(grad_numerical) < 1e-7 and abs(grad_analytic) < 1e-7:
                rel_error = 0 # not enough precision to check this
                status = 'VAL SMALL WARNING'
            else:
                rel_error = abs(grad_analytic - grad_numerical) / abs(grad_numerical + grad_analytic)
                status = 'OK'
                if rel_error > rel_error_thr_warning: status = 'WARNING'
                if rel_error > rel_error_thr_error: status = '!!!DANGEROUS ERROR!!!'

            print '%s checking param %s index %s (val = %+8f), analytic = %+8f, numerical = %+8f, relative error = %+8f' \
                    % (status, name, `np.unravel_index(i, mat.shape)`, old_val, grad_analytic, grad_numerical, rel_error)

    print "Finish checking fully connected"



def GradientChecking13():
    # this is to check fully connected layer
    B = 8  # batch size
    I = 4  # input size
    H = 16
    O = I   # output size

    x = init_w([B, I])
    y = np.sin(x)

    layers = [BlockDisplaceFC(I, H, 3, "BlockDisplaceFC1"), LeakyReLU('leakyrelu0'), BlockDisplaceFC(H, O, 3, "BlockDisplaceFC2")]
    nlayers = len(layers)

    # forward and backward

    # inputs[i] is the input for i-th layer
    # the last of inputs[i] must be the output of current network
    inputs = [x]
    for i in xrange(nlayers):
        inputs.append( layers[i].forward(inputs[-1]) ) # inputs[i] is the input for i-th layer

    cost = EuclideanLoss()
    # loss = cost.forward(inputs[-1], y)

    # grads[i] is the gradients for i-th layer, but in the reverse order
    grads = [cost.backward(inputs[-1], y)]
    for i in reversed(xrange(nlayers)):
        grads.append( layers[i].backward(inputs[i], grads[-1]) ) # grads[i]

    # following checking method is from https://gist.github.com/karpathy/587454dc0146a6ae21fc
    delta = 1e-5
    rel_error_thr_warning = 1e-2
    rel_error_thr_error = 1

    cl = [bij for bi in layers[0].B for bij in bi] + [bij for bi in layers[2].B for bij in bi]
    checklist = [bij.g for bij in cl] + [bij.h for bij in cl] + [bij.c for bij in cl]
    grads_analytic = [bij.dg for bij in cl] + [bij.dh for bij in cl] + [bij.dc for bij in cl]
    names = ['%s_dg' % bij.name for bij in cl] + ['%s_dh' % bij.name for bij in cl] + ['%s_dc' % bij.name for bij in cl]
    for j in xrange(len(checklist)):
        mat = checklist[j]
        dmat = grads_analytic[j]
        name = names[j]
        for i in xrange(mat.size):
            old_val = mat.flat[i]

            # test f(x + delta_x)
            mat.flat[i] = old_val + delta
            loss0 = fwd(x, y, layers, cost)

            # test f(x - delta_x)
            mat.flat[i] = old_val - delta
            loss1 = fwd(x, y, layers, cost)

            mat.flat[i] = old_val # recover

            grad_analytic = dmat.flat[i]
            grad_numerical = (loss0 - loss1) / (2 * delta)

            if grad_numerical == 0 and grad_analytic == 0:
                rel_error = 0 # both are zero, OK.
                status = 'OK'
            elif abs(grad_numerical) < 1e-7 and abs(grad_analytic) < 1e-7:
                rel_error = 0 # not enough precision to check this
                status = 'VAL SMALL WARNING'
            else:
                rel_error = abs(grad_analytic - grad_numerical) / abs(grad_numerical + grad_analytic)
                status = 'OK'
                if rel_error > rel_error_thr_warning: status = 'WARNING'
                if rel_error > rel_error_thr_error: status = '!!!DANGEROUS ERROR!!!'

            print '%s checking param %s index %s (val = %+8f), analytic = %+8f, numerical = %+8f, relative error = %+8f' \
                    % (status, name, `np.unravel_index(i, mat.shape)`, old_val, grad_analytic, grad_numerical, rel_error)

    print "Finish checking fully connected"




def GradientChecking14():
    # this is to check fully connected layer
    B = 8  # batch size
    I = 8  # input size
    H = 17
    O = I   # output size

    x = init_w([B, I])
    y = np.sin(x)

    layers = [DisplaceFC2(I, H, "DisplaceFC1"), LeakyReLU('leakyrelu0'), DisplaceFC2(H, O, "DisplaceFC2")]
    nlayers = len(layers)

    # forward and backward

    # inputs[i] is the input for i-th layer
    # the last of inputs[i] must be the output of current network
    inputs = [x]
    for i in xrange(nlayers):
        inputs.append( layers[i].forward(inputs[-1]) ) # inputs[i] is the input for i-th layer

    cost = EuclideanLoss()
    # loss = cost.forward(inputs[-1], y)

    # grads[i] is the gradients for i-th layer, but in the reverse order
    grads = [cost.backward(inputs[-1], y)]
    for i in reversed(xrange(nlayers)):
        grads.append( layers[i].backward(inputs[i], grads[-1]) ) # grads[i]

    # following checking method is from https://gist.github.com/karpathy/587454dc0146a6ae21fc
    delta = 1e-5
    rel_error_thr_warning = 1e-2
    rel_error_thr_error = 1

    checklist = [layers[0].g, layers[0].h, layers[0].c, layers[2].g, layers[2].h, layers[2].c]
    grads_analytic = [layers[0].dg, layers[0].dh, layers[0].dc, layers[2].dg, layers[2].dh, layers[2].dc]
    names = ['0g', '0h', '0c', '2g', '2h', '2c' ]
    for j in xrange(len(checklist)):
        mat = checklist[j]
        dmat = grads_analytic[j]
        name = names[j]
        for i in xrange(mat.size):
            old_val = mat.flat[i]

            # test f(x + delta_x)
            mat.flat[i] = old_val + delta
            loss0 = fwd(x, y, layers, cost)

            # test f(x - delta_x)
            mat.flat[i] = old_val - delta
            loss1 = fwd(x, y, layers, cost)

            mat.flat[i] = old_val # recover

            grad_analytic = dmat.flat[i]
            grad_numerical = (loss0 - loss1) / (2 * delta)

            if grad_numerical == 0 and grad_analytic == 0:
                rel_error = 0 # both are zero, OK.
                status = 'OK'
            elif abs(grad_numerical) < 1e-7 and abs(grad_analytic) < 1e-7:
                rel_error = 0 # not enough precision to check this
                status = 'VAL SMALL WARNING'
            else:
                rel_error = abs(grad_analytic - grad_numerical) / abs(grad_numerical + grad_analytic)
                status = 'OK'
                if rel_error > rel_error_thr_warning: status = 'WARNING'
                if rel_error > rel_error_thr_error: status = '!!!DANGEROUS ERROR!!!'

            print '%s checking param %s index %s (val = %+8f), analytic = %+8f, numerical = %+8f, relative error = %+8f' \
                    % (status, name, `np.unravel_index(i, mat.shape)`, old_val, grad_analytic, grad_numerical, rel_error)

    print "Finish checking fully connected"



def GradientChecking15():
    # this is to check fully connected layer
    B = 3  # batch size
    I = 7  # input size
    H = 17
    O = I   # output size

    x = init_w([B, I])
    y = np.sin(x)
    #y = np.sum(np.sin(x), axis=1).reshape(B, O)

    layers = [NewCircFC3(I, H, 5, "CircFc1"), Tanh('tanh0'), NewCircFC3(H, O, 4, "CircFc2")]
    nlayers = len(layers)

    # forward and backward

    # inputs[i] is the input for i-th layer
    # the last of inputs[i] must be the output of current network
    inputs = [x]
    for i in xrange(nlayers):
        inputs.append( layers[i].forward(inputs[-1]) ) # inputs[i] is the input for i-th layer

    cost = EuclideanLoss()
    # loss = cost.forward(inputs[-1], y)

    # grads[i] is the gradients for i-th layer, but in the reverse order
    grads = [cost.backward(inputs[-1], y)]
    for i in reversed(xrange(nlayers)):
        grads.append( layers[i].backward(inputs[i], grads[-1]) ) # grads[i]

    # following checking method is from https://gist.github.com/karpathy/587454dc0146a6ae21fc
    delta = 1e-5
    rel_error_thr_warning = 1e-2
    rel_error_thr_error = 1

    checklist = [layers[0].w, layers[2].w]
    grads_analytic = [layers[0].dw, layers[2].dw]
    names = ['w%d' % i for i in xrange(len(checklist))]
    for j in xrange(len(checklist)):
        mat = checklist[j]
        dmat = grads_analytic[j]
        name = names[j]
        for i in xrange(mat.size):
            old_val = mat.flat[i]

            # test f(x + delta_x)
            mat.flat[i] = old_val + delta
            loss0 = fwd(x, y, layers, cost)

            # test f(x - delta_x)
            mat.flat[i] = old_val - delta
            loss1 = fwd(x, y, layers, cost)

            mat.flat[i] = old_val # recover

            grad_analytic = dmat.flat[i]
            grad_numerical = (loss0 - loss1) / (2 * delta)

            if grad_numerical == 0 and grad_analytic == 0:
                rel_error = 0 # both are zero, OK.
                status = 'OK'
            elif abs(grad_numerical) < 1e-7 and abs(grad_analytic) < 1e-7:
                rel_error = 0 # not enough precision to check this
                status = 'VAL SMALL WARNING'
            else:
                rel_error = abs(grad_analytic - grad_numerical) / abs(grad_numerical + grad_analytic)
                status = 'OK'
                if rel_error > rel_error_thr_warning: status = 'WARNING'
                if rel_error > rel_error_thr_error: status = '!!!DANGEROUS ERROR!!!'

            print '%s checking param %s index %s (val = %+8f), analytic = %+8f, numerical = %+8f, relative error = %+8f' \
                    % (status, name, `np.unravel_index(i, mat.shape)`, old_val, grad_analytic, grad_numerical, rel_error)

    print "Finish checking fully connected"





def GradientChecking16():                                                       
                                                                                
    txt = "this is an example for huffman encoding"                             
    symb2freq = defaultdict(int)                                                
    for ch in txt:                                                              
        symb2freq[ch] += 1                                                      
    tree, root = encode(symb2freq)                                              
    labels = np.unique(list(txt))                                               
    print "labels", len(labels)                                                 
    tree_idx = {}                                                               
    for i,xs in enumerate(tree):                                                
        tree_idx[xs[0]] = i                                                     
                                                                                
    path = []                                                                   
    for label in labels:                                                        
        path.append(tree[tree_idx[label]][2])                                   
                                                                                
    code = []                                                                   
    for label in labels:                                                        
        code.append(map(int, list(tree[tree_idx[label]][1])))                   
                                                                                
    # this is to just check network can go both forward and backward            
    B = 3  # batch size                                                         
    I = 5  # input size                                                         
    H = 11 # hidden size                                                        
    O = len(labels)  # output size                                              
                                                                                
    x = np.random.randint(0, I, size=(B,I))                                     
    y = np.random.randint(0, O, size=[B])                                       
                                                                                
    layers = [EmbeddingLayer(I,H), ReduceMeanLayer(1, "reduce") ]               
    nlayers = len(layers)                                                       
                                                                                
    # forward and backward                                                      
                                                                                
    # inputs[i] is the input for i-th layer                                     
    # the last of inputs[i] must be the output of current network               
    inputs = [x]                                                                
    for i in xrange(nlayers):                                                   
        inputs.append( layers[i].forward(inputs[-1]) ) # inputs[i] is the input for i-th layer
                                                                                
    cost = HierarchicalSoftmaxLoss(H, O, root, path, code)                      
    loss = cost.forward(inputs[-1], y)                                          
                                                                                
    # grads[i] is the gradients for i-th layer, but in the reverse order        
    grads = [cost.backward(inputs[-1], y)]                                      
    for i in reversed(xrange(nlayers)):                                         
        grads.append( layers[i].backward(inputs[i], grads[-1]) ) # grads[i] 

    # following checking method is from https://gist.github.com/karpathy/587454dc0146a6ae21fc
    delta = 1e-5                                                                
    rel_error_thr_warning = 1e-2                                                
    rel_error_thr_error = 1                                                     
                                                                                
    checklist = [layers[0].w, cost.w]                                           
    grads_analytic = [layers[0].dw, cost.dw]                                    
    names = ['w', 'cost_w']                                                     
    for j in xrange(len(checklist)):                                            
        mat = checklist[j]                                                      
        dmat = grads_analytic[j]                                                
        name = names[j]                                                         
        for i in xrange(mat.size):                                              
            old_val = mat.flat[i]                                               
                                                                                
            # test f(x + delta_x)                                               
            mat.flat[i] = old_val + delta                                       
            loss0 = fwd(x, y, layers, cost)                                     
                                                                                
            # test f(x - delta_x)                                               
            mat.flat[i] = old_val - delta                                       
            loss1 = fwd(x, y, layers, cost)                                     
                                                                                
            mat.flat[i] = old_val # recover                                     
                                                                                
            grad_analytic = dmat.flat[i]                                        
            grad_numerical = (loss0 - loss1) / (2 * delta)                      
                                                                                
            if grad_numerical == 0 and grad_analytic == 0:                      
                rel_error = 0 # both are zero, OK.                              
                status = 'OK'                                                   
            elif abs(grad_numerical) < 1e-7 and abs(grad_analytic) < 1e-7:      
                rel_error = 0 # not enough precision to check this              
                status = 'VAL SMALL WARNING'                                    
            else:                                                               
                rel_error = abs(grad_analytic - grad_numerical) / abs(grad_numerical + grad_analytic)
                status = 'OK'                                                   
                if rel_error > rel_error_thr_warning: status = 'WARNING'        
                if rel_error > rel_error_thr_error: status = '!!!DANGEROUS ERROR!!!'
                                                                                
            print '%s checking param %s index %s (val = %+8f), analytic = %+8f, numerical = %+8f, relative error = %+8f' \
                    % (status, name, `np.unravel_index(i, mat.shape)`, old_val, grad_analytic, grad_numerical, rel_error)




if __name__ == "__main__":
    #GradientChecking1()
    #GradientChecking2()
    #circulant_check()
    #GradientChecking3()
    #GradientChecking4()
    #GradientChecking5()
    #GradientChecking6()
    #GradientChecking7()
    #GradientChecking8()
    #GradientChecking9()
    #GradientChecking10()
    #GradientChecking11()
    #GradientChecking12()
    #GradientChecking13()
    #GradientChecking14()
    #GradientChecking15()
    GradientChecking16()
    #time_test2()
    pass
