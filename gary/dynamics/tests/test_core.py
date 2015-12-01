# coding: utf-8

""" Test core dynamics.  """

from __future__ import division, print_function

__author__ = "adrn <adrn@astro.columbia.edu>"

# Standard library
import os

# Third-party
import astropy.units as u
import matplotlib.pyplot as pl
import numpy as np
from astropy import log as logger

# Project
from ..core import *
from ...potential import LogarithmicPotential
from ...units import galactic
from ...util import assert_quantities_allclose

# ----------------------------------------------------------------------------

def test_angular_momentum():

    w = CartesianPhaseSpacePosition([1.,0.,0.], [0.,0.,1.])
    assert np.allclose(np.squeeze(w.angular_momentum()), [0., -1, 0])

    w = CartesianPhaseSpacePosition([1.,0.,0.], [0.,1.,0.])
    assert np.allclose(np.squeeze(w.angular_momentum()), [0., 0, 1])

    w = CartesianPhaseSpacePosition([0.,1.,0.],[0.,0.,1.])
    assert np.allclose(np.squeeze(w.angular_momentum()), [1., 0, 0])

    w = CartesianPhaseSpacePosition([1.,0,0]*u.kpc, [0.,200.,0]*u.pc/u.Myr)
    assert_quantities_allclose(np.squeeze(w.angular_momentum()), [0,0,0.2]*u.kpc**2/u.Myr)

    # multiple - known
    q = np.array([[1.,0.,0.],[1.,0.,0.],[0,1.,0.]]).T
    p = np.array([[0,0,1.],[0,1.,0.],[0,0,1]]).T
    L = CartesianPhaseSpacePosition(q, p).angular_momentum()
    true_L = np.array([[0., -1, 0],[0., 0, 1],[1., 0, 0]]).T
    assert L.shape == (3,3)
    assert np.allclose(L, true_L)

    # multiple - random
    q = np.random.uniform(size=(3,128))
    p = np.random.uniform(size=(3,128))
    L = CartesianPhaseSpacePosition(q, p).angular_momentum()
    assert L.shape == (3,128)

# ----------------------------------------------------------------------------

def make_known_orbit(tmpdir, x, vx, potential, name):
    # See Binney & Tremaine (2008) Figure 3.8 and 3.9
    E = -0.337
    y = 0.
    vy = np.sqrt(2*(E - potential.value([x,y,0.])))[0]

    w = [x,y,0.,vx,vy,0.]
    t,ws = potential.integrate_orbit(w, dt=0.05, nsteps=10000)

    fig,ax = pl.subplots(1,1)
    ax.plot(ws[0], ws[1])
    # fig = plot_orbits(ws, linestyle='none', alpha=0.1)
    fig.savefig(os.path.join(str(tmpdir), "{}.png".format(name)))
    logger.debug(os.path.join(str(tmpdir), "{}.png".format(name)))

    return ws

def test_classify_orbit(tmpdir):

    potential = LogarithmicPotential(v_c=1., r_h=0.14, q1=1., q2=0.9, q3=1.,
                                     units=galactic)

    # individual
    w1 = make_known_orbit(tmpdir, 0.5, 0., potential, "loop")
    circ = classify_orbit(w1)
    assert circ.shape == (3,)
    assert circ.sum() == 1

    w2 = make_known_orbit(tmpdir, 0., 1.5, potential, "box")
    circ = classify_orbit(w2)
    assert circ.shape == (3,)
    assert circ.sum() == 0

    # try also for both, together
    w3 = np.stack((w1,w2),-1)
    circ = classify_orbit(w3)
    assert circ.shape == (3,2)
    assert np.allclose(circ.sum(axis=0), [1,0])

# ----------------------------------------------------------------------------

def test_align_circulation_single():

    potential = LogarithmicPotential(v_c=1., r_h=0.14, q1=1., q2=0.9, q3=1.,
                                     units=galactic)
    w0 = np.array([[0.,1.,0.,0.,0.,0.5],  # loop around x axis
                   [1.,0.,0.,0.,0.,0.5],  # loop around y axis
                   [1.,0.,0.,0.,0.5,0.],  # loop around z axis
                   [0.8,0.4,0.,0.,0.1,0.]]).T  # box

    t,w = potential.integrate_orbit(w0, dt=0.05, nsteps=10000)

    for i in range(w.shape[2]):
        circ = classify_orbit(w[...,i])
        new_w = align_circulation_with_z(w[...,i], circ)
        new_circ = classify_orbit(new_w)

        if i == 3:
            assert np.sum(new_circ) == 0
        else:
            assert new_circ[2] == 1.

def test_align_circulation_many(tmpdir):

    potential = LogarithmicPotential(v_c=1., r_h=0.14, q1=1., q2=0.9, q3=1.,
                                     units=galactic)
    w0 = np.array([[0.,1.,0.,0.,0.,0.5],  # loop around x axis
                   [1.,0.,0.,0.,0.,0.5],  # loop around y axis
                   [1.,0.,0.,0.,0.5,0.],  # loop around z axis
                   [0.8,0.4,0.,0.,0.1,0.]]).T  # box
    names = ['xloop', 'yloop', 'zloop', 'box']

    t,w = potential.integrate_orbit(w0, dt=0.05, nsteps=10000)
    # fig = plot_orbits(w, linestyle='none', alpha=0.1)
    # fig.savefig(os.path.join(str(tmpdir), "align_circulation_orbits_init.png"))

    circ = classify_orbit(w)
    assert circ.shape == (3,4)

    new_w = align_circulation_with_z(w, circ)
    # fig = plot_orbits(new_w, linestyle='none', alpha=0.1)
    # fig.savefig(os.path.join(str(tmpdir), "align_circulation_orbits_post.png"))

    new_circ = classify_orbit(new_w)
    assert np.all(new_circ[2,:3] == 1.)

def test_peak_to_peak_period():
    ntimes = 16384

    # trivial test
    for true_T in [1., 2., 4.123]:
        t = np.linspace(0,10.,ntimes)
        f = np.sin(2*np.pi/true_T * t)
        T = peak_to_peak_period(t, f)
        assert np.allclose(T, true_T, atol=1E-3)

    # modulated trivial test
    true_T = 2.
    t = np.linspace(0,10.,ntimes)
    f = np.sin(2*np.pi/true_T * t) + 0.1*np.cos(2*np.pi/(10*true_T) * t)
    T = peak_to_peak_period(t, f)
    assert np.allclose(T, true_T, atol=1E-3)
