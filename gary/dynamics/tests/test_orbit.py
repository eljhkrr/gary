# coding: utf-8

""" Test core dynamics.  """

from __future__ import division, print_function

__author__ = "adrn <adrn@astro.columbia.edu>"

# Standard library
import os
import logging

# Third-party
import matplotlib.pyplot as plt
import numpy as np
from astropy import log as logger
import astropy.coordinates as coord
import astropy.units as u

# Project
from ...units import galactic
from ..orbit import Orbit

logger.setLevel(logging.DEBUG)

def test_api():
    t = np.arange(0,100,0.1)*u.Myr
    x = np.zeros((3,len(t)))*u.kpc
    x[0] = 2.*u.kpc * np.cos(0.1*u.rad*u.Hz*t)
    x[1] = 2.*u.kpc * np.sin(0.1*u.rad*u.Hz*t)

    v = np.zeros((3,len(t)))*u.km/u.s
    v[0] = -160.*u.km/u.s * np.sin(0.1*u.rad*u.Hz*t)
    v[1] = 160.*u.km/u.s * np.cos(0.1*u.rad*u.Hz*t)

    orbit = Orbit(pos=x, vel=v, t=t, unitsys=galactic)
    for nm in 'xyz':
        assert hasattr(orbit, nm)
        assert hasattr(orbit, 'v'+nm)

    new_orbit = orbit.represent_as(coord.PhysicsSphericalRepresentation)
    for nm in ['r','phi','theta']:
        assert hasattr(new_orbit, nm)
        assert hasattr(new_orbit, 'v'+nm)
