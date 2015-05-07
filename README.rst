unfoldr
=======

unfolding and nearest-neighbor level spacings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Given the eigenvalues of an ensemble of random matrices, unfoldr
calculates the nearest-neighbor level spacings of the unfolded spectrum,
either as a whole or for *slices* of it. You can specify how you want to
cut the spectrum into slices — linearly, logarithmically —, and unfoldr
will calculate the level spacings for each slice individually. With this
you can study how the level spacing statistics change with energy and
whether or not there is a phase transition in the spectrum.

Check out `this blog
post <http://tscholak.github.io/code/physics/2015/05/05/unfoldr.html>`__
for more details.

Current status
--------------

The current branch continuous integration status: |Build Status|

Installation
------------

unfoldr has been tested with Python 2.7 on 64-bit Linux and Mac OS X. It
requires the following packages:

-  `NumPy <http://www.numpy.org>`__
-  `h5py <http://www.h5py.org>`__
-  `Cython <http://cython.org>`__

Obtaining the source code
~~~~~~~~~~~~~~~~~~~~~~~~~

::

    $ git clone git@github.com:tscholak/unfoldr.git

Setting up unfoldr
~~~~~~~~~~~~~~~~~~

unfoldr uses the
`setuptools <https://pypi.python.org/pypi/setuptools>`__. From within
the source code directory, run:

::

    python setup.py install

Make sure your Python's ``bin`` directory is in your ``$PATH``. On Mac
OS X, if you use Macports and haven't done so already, add

::

    export PATH=/opt/local/Library/Frameworks/Python.framework/Versions/2.7/bin:$PATH

to your ``~/.bash_login`` or ``~/.bash_profile`` file.

Usage
-----

unfoldr reads input files one-by-one and processes them in parallel. The
output file is written to once at the end of the program. The data in
the output file can be analyzed statistically with
`histogramr <https://github.com/tscholak/histogramr>`__.

Command line arguments
~~~~~~~~~~~~~~~~~~~~~~

::

    usage: unfoldr [-h] [-V] [-q] [-v] [-D] -d <dsname> -m <mname> [-b <size>]
                   [-l <range>] [-L] [-p <size>] [-i] -o <outfile>
                   <infile> [<infile> ...]

    unfold spectra of random matrices and Hamiltonians and calculate the nearest-
    neighbor level spacings.

    positional arguments:
      <infile>              name(s) of input file(s)

    optional arguments:
      -b <size>, --binning <size>
                            binning (default: inf)
      -l <range>, --limits <range>
                            limits (default: [-1.7976931348623157e+308,
                            1.7976931348623157e+308])
      -L, --l10             logarithmic binning (default: False)
      -p <size>, --poolsize <size>
                            relative size of the unfolding pool (default: 2)
      -i, --inmemory        keep all data in memory (default: False)

    mandatory arguments:
      -d <dsname>, --dataset <dsname>
                            input data set (default: None)
      -m <mname>, --member <mname>
                            input data set member (default: None)
      -o <outfile>, --output <outfile>
                            name of output file (default: None)

    other arguments:
      -h, --help            show this help message and exit
      -V, --version         show program's version number and exit
      -q, --quiet           quiet output (default: False)
      -v, --verbose         verbose output (default: False)
      -D, --debug           debug output (default: False)

    Report bugs to: torsten.scholak+unfoldr@googlemail.com unfoldr home page:
    <https://github.com/tscholak/unfoldr>

Impact
------

So far, unfoldr has unfolded spectra for the following publication(s):
\* Torsten Scholak, Thomas Wellens, Andreas Buchleitner, "Spectral
Backbone of Excitation Transport in Ultra-Cold Rydberg Gases", Phys.
Rev. A 90, 063415 (2014)

.. |Build Status| image:: https://travis-ci.org/tscholak/unfoldr.png
   :target: https://travis-ci.org/tscholak/unfoldr
