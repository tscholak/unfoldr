#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs
import os
import re
import sys
import platform

from setuptools import setup, Extension

try:
  from Cython.Build import cythonize
except:
  print ('This package requires Cython.')
  raise

import numpy as np

try:
  numpy_include = np.get_include()
except AttributeError:
  numpy_include = np.get_numpy_include()

here = os.path.abspath(os.path.dirname(__file__))

def read(*parts):
  return codecs.open(os.path.join(here, *parts), 'r').read()

from unfoldr import __version__

requirements = ['numpy', 'h5py', 'cython']

if 'darwin' in platform.platform().lower():
  os.environ["CC"] = "gcc-mp-4.9"
  os.environ["CXX"] = "g++-mp-4.9"

extensions = [Extension("unfoldr._core",
                        ["unfoldr/_core.pyx"],
                        extra_link_args=["-fopenmp"],
                        extra_compile_args=['-fopenmp'])]

if __name__ == '__main__':
  setup(name='unfoldr',
        version=__version__,
        description='A tool to unfold spectra of random matrices and Hamiltonians '
                    'and to calculate the nearest-neighbor level spacings.',
        long_description=read('README.rst'),
        classifiers=['Programming Language :: Python',
                     'Development Status :: 3 - Alpha',
                     'Natural Language :: English',
                     'Environment :: Console',
                     'Intended Audience :: Science/Research',
                     'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
                     'Operating System :: OS Independent',
                     'Programming Language :: Python :: 2.7',
                     'Topic :: Scientific/Engineering :: Physics',
                     'Topic :: Scientific/Engineering :: Mathematics',
                     'Topic :: Utilities',],
        keywords='unfolding physics research science',
        license='GPLv3',
        url='https://github.com/tscholak/unfoldr',
        author='Torsten Scholak',
        author_email='torsten.scholak@googlemail.com',
        packages=['unfoldr'],
        platforms=['Any'],
        entry_points={'console_scripts': ["unfoldr=unfoldr.unfoldr:main",]},
        install_requires=requirements,
        ext_modules=cythonize(extensions),
        include_dirs = [numpy_include,],
        test_suite='tests',)
