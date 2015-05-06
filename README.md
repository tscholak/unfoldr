# unfoldr
### unfolding and nearest-neighbor level spacings
Check out [this blog post](http://tscholak.github.io/code/physics/2015/05/06/unfoldr.html) for more details.

## Current status
The current branch continuous integration status:
[![Build Status](https://travis-ci.org/tscholak/unfoldr.png)](https://travis-ci.org/tscholak/unfoldr)

## Installation
unfoldr has been tested with Python 2.7 on 64-bit Linux and Mac OS X. It requires the following packages:
* [NumPy](http://www.numpy.org)
* [h5py](http://www.h5py.org)
* [Cython](http://cython.org)

### Obtaining the source code
```
$ git clone git@github.com:tscholak/unfoldr.git
```

### Setting up histogramr
unfoldr uses the setuptools. From within the source code directory, run:
```
python setup.py install
```

## Usage
unfoldr reads input files one-by-one and processes them in parallel. The output file is written to once at the end of the program. The data in the output file can be analyzed statistically with [histogramr](https://github.com/tscholak/histogramr).

### Command line arguments
```
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
```

## Impact
So far, unfoldr has unfolded spectra for the following publication(s):
* Torsten Scholak, Thomas Wellens, Andreas Buchleitner, "Spectral Backbone of Excitation Transport in Ultra-Cold Rydberg Gases", Phys. Rev. A 90, 063415 (2014)

