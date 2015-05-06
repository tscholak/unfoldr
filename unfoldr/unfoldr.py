# -*- coding: utf-8 -*-

'''
# unfoldr - a tool to unfold spectra of random matrices and Hamiltonians
# and to calculate the nearest-neighbor level spacings.
#
# Copyright (C) 2015 Torsten Scholak <torsten.scholak@googlemail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import ctypes
import os
import sys
import re
import tempfile

import argparse
import logging

import multiprocessing as mp
import copy_reg
import types
from contextlib import closing

import collections as cs
import numpy as np
import h5py

from . import __version__
from ._pickle_helpers import _pickle_method, _unpickle_method
from ._hdf5_helpers import _convert_to_dtype
from ._core import _process_sorted_eigval

logging.basicConfig()
logger = logging.getLogger(__name__)

copy_reg.pickle(types.MethodType, _pickle_method, _unpickle_method)

spacing_dt = np.dtype([('spacing', np.float64),])

class ArgumentParserError(Exception):
  pass

class ThrowingArgumentParser(argparse.ArgumentParser):
  def error(self, message):
    raise ArgumentParserError(message)

RawData = cs.namedtuple('RawData', ['id',
                                    'eigval',
                                    'filename',
                                    'size'])
ProcessedData = cs.namedtuple('ProcessedData', ['slice',
                                                'spacings'])

class Task():
  def __init__(self, eigval_id):
    self.eigval_id = eigval_id
  def __str__(self):
    return str(self.eigval_id)

class Result():
  def __init__(self, processed_data):
    self.processed_data = processed_data
  def __str__(self):
    return str(self.processed_data)

class Unfoldr(object):
  def __init__(self):
    self.raw_data = []
    self.tasks = []
    self.results = []

  def __del__(self):
    pass

  def _parse_limits(self, string):
    '''
    Parse the limits.
    '''
    scinot = '-?(?:0|[1-9]\d*)(?:\.\d*)?(?:[eE][+\-]?\d+)?'
    result = re.match(r'('+scinot+')?,('+scinot+')?$', string)
    if not result:
      raise argparse.ArgumentTypeError("'" + string + "' is not a valid range of numbers. "
                                       "Expected are forms like '0,1', '0,', or ',1'. "
                                       "Numbers have to be expressed in the scientific notation.")
    start = float(result.group(1) or -sys.float_info.max)
    end = float(result.group(2) or sys.float_info.max)
    if start > end:
      start, end = end, start
    return [start, end]

  def _build_parser(self):
    '''
    Set the command line arguments.
    '''
    parser = ThrowingArgumentParser(prog='unfoldr',
                                    description="""unfold spectra of random matrices and Hamiltonians
                                                and calculate the nearest-neighbor level spacings.""",
                                    epilog="""Report bugs to: torsten.scholak+unfoldr@googlemail.com
                                           unfoldr home page: <https://github.com/tscholak/unfoldr>""",
                                    add_help=False,
                                    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    
    required = parser.add_argument_group('mandatory arguments')
    other = parser.add_argument_group('other arguments')

    other.add_argument('-h', '--help',
                       action='help',
                       help='show this help message and exit')
    other.add_argument('-V', '--version', 
                       action='version',              
                       version='%(prog)s ' + __version__)
    other.add_argument('-q', '--quiet', dest='quiet',
                       action='store_true', default=False,
                       help='quiet output')
    other.add_argument('-v', '--verbose', dest='verbose',
                       action='store_true', default=False,
                       help='verbose output')
    other.add_argument('-D', '--debug', dest='debug',
                       action='store_true', default=False,
                       help='debug output')

    required.add_argument('-d', '--dataset', dest='dataset', metavar='<dsname>',
                          type=str, required=True,
                          help='input data set')
    required.add_argument('-m', '--member', dest='member', metavar='<mname>',
                          type=str, required=True,
                          help='input data set member')
    parser.add_argument('-b', '--binning', dest='binning', metavar='<size>',
                        type=float, default=float("inf"),
                        help='binning')
    limits_arg = parser.add_argument('-l', '--limits', dest='limits', metavar='<range>',
                                     type=self._parse_limits, default=[-sys.float_info.max,sys.float_info.max],
                                     help='limits')
    parser.add_argument('-L', '--l10', dest='log_bin',
                        action='store_true', default=False,
                        help='logarithmic binning')

    parser.add_argument('-p', '--poolsize', dest='size_pool', metavar='<size>',
                        type=float, default=2,
                        help='relative size of the unfolding pool')

    parser.add_argument('-i', '--inmemory', dest='in_memory',
                        action='store_true', default=False,
                        help='keep all data in memory')
    
    required.add_argument('-o', '--output', dest='out_file', metavar='<outfile>',
                          required=True,
                          help='name of output file')
    parser.add_argument(dest='in_file', metavar='<infile>',
                        nargs='+',
                        help='name(s) of input file(s)')

    return limits_arg, parser

  def _configure_logging(self):
    '''
    Set up logging.
    '''
    if self.options.debug:
      logger.setLevel(logging.DEBUG)
    elif self.options.verbose:
      logger.setLevel(logging.INFO)
    elif self.options.quiet:
      logger.setLevel(logging.CRITICAL)
    else:
      logger.setLevel(logging.WARNING)

  def _check_options(self, limits_arg):
    '''
    Further checks of the arguments.
    '''
    if self.options.log_bin:
      if np.sign(self.options.limits[0]) == 0 or np.sign(self.options.limits[1]) == 0:
        raise argparse.ArgumentError(limits_arg,
                                     'For logarithmic binning, the limits must not be zero.')
      if np.sign(self.options.limits[0]) != np.sign(self.options.limits[1]):
        raise argparse.ArgumentError(limits_arg,
                                     "For logarithmic binning, the limits have to be "
                                     "either both positive or both negative.")

  def _read_files(self):
    '''
    Reading data from files.
    '''
    raw_data = []
    
    for in_file in self.options.in_file:
      try:
        in_f = h5py.File(in_file, 'r')
        ds = in_f[self.options.dataset]
        ev = ds[self.options.member]
        in_f.close()
      except IOError:
        print "Warning: could not open file '{0}'. Skipping.".format(in_file)
        logger.warning('IOError')
        continue
      except:
        print "Warning: could not read file '{0}'. Skipping.".format(in_file)
        logger.warning('UnknownError')
        continue

      for eigval in ev:
        if self.options.log_bin:
          eigval = eigval[np.sign(self.options.limits[0]) * eigval > 0]
          eigval_id = np.log10(eigval)
        else:
          eigval_id = eigval
        eigval_id = np.int64(np.floor(eigval_id / self.options.binning))

        if not self.options.in_memory:
          tmp_dir = tempfile.mkdtemp()

        for cur_id in range(self.min_id, self.max_id + 1, 1):
          sel = eigval_id == cur_id
          size_sel = np.sum(sel)

          if size_sel == 0:
            continue

          if self.options.in_memory:
            eigval_sel = mp.Array(ctypes.c_double, size_sel)
            np.frombuffer(eigval_sel.get_obj())[:] = eigval[sel]
            raw_data.append(RawData._make([cur_id,
                                           eigval_sel,
                                           '',
                                           size_sel]))
          else:
            eigval_sel_fp = np.memmap(os.path.join(tmp_dir, str(cur_id)),
                                      dtype=np.float64,
                                      mode='w+',
                                      shape=size_sel)
            eigval_sel_fp[:] = eigval[sel]
            raw_data.append(RawData._make([cur_id,
                                           '',
                                           eigval_sel_fp.filename,
                                           size_sel]))
            del eigval_sel_fp

    return raw_data

  def _pool_init(self, raw_data_):
    global raw_data
    raw_data = raw_data_

  def _unfold(self, raw_data):
    '''
    Creation and processing of the unfolding tasks.
    '''
    for cur_id in range(self.min_id, self.max_id + 1, 1):
      self.tasks.append(Task(cur_id))

    with closing(mp.Pool(initializer=self._pool_init,
                         initargs=(raw_data,))) as p:
      p.map_async(self._process,
                  self.tasks,
                  callback=self.results.extend)
    p.join()

  def _process(self, task):
    '''
    Process a task.
    '''
    task_id = task.eigval_id
    
    slice = self.options.binning * (np.float64(task_id) + 0.5)
    if self.options.log_bin:
      slice = 10 ** slice

    task_data = [(raw_datum.eigval,
                  raw_datum.filename,
                  raw_datum.size) for raw_datum in raw_data if raw_datum.id == task_id]

    unfolding_pool_count = np.int64(np.floor(np.float64(self.options.size_pool) * 
                                             np.float64(len(task_data)) / 
                                             (1 + np.float64(self.options.size_pool))))

    spacings = np.empty(0, dtype=np.float64)
    
    if unfolding_pool_count > 1:
      unfolding_pool = np.empty(0, dtype=np.float64)

      for (eigval, filename, size) in task_data[:unfolding_pool_count]:
        if self.options.in_memory:
          eigval = np.frombuffer(eigval.get_obj())
        else:
          eigval = np.memmap(filename, dtype=np.float64, mode='r', shape=size)

        unfolding_pool.resize(len(unfolding_pool) + len(eigval))
        unfolding_pool[-len(eigval):] = eigval[0:]

        if not self.options.in_memory:
          del eigval

      unfolding_pool = np.sort(unfolding_pool)

      if len(unfolding_pool) > 2:
        for (eigval, filename, size) in task_data[unfolding_pool_count:]:
          if self.options.in_memory:
            eigval = np.frombuffer(eigval.get_obj())
          else:
            eigval = np.memmap(filename,
                               dtype=np.float64,
                               mode='r',
                               shape=size)

          if len(eigval) <= 2:
            if not self.options.in_memory:
              del eigval
            continue

          try:
            cur_spacings = _process_sorted_eigval(eigval,
                                                  unfolding_pool,
                                                  unfolding_pool_count)
          except:
            cur_spacings = np.empty(0, dtype=np.float64)

          if not self.options.in_memory:
            del eigval

          spacings.resize (len(spacings) + len(cur_spacings))
          spacings[-len(cur_spacings):] = cur_spacings[0:]

    return Result(ProcessedData._make([slice, spacings]))

  def _save(self):
    try:
      out_f = h5py.File(self.options.out_file, 'w')
      for result in self.results:
        out_f.create_dataset(str(result.processed_data.slice),
                             data=_convert_to_dtype(np.array([result.processed_data.spacings],
                                                             dtype=object).transpose(),
                                                    spacing_dt))
      out_f.close()
    except IOError:
      raise IOError("could not open file '{0}'.".format(self.options.out_file))
    except:
      raise IOError("could not write file '{0}'.".format(self.options.out_file))

  def _clean_up(self):
    if not self.options.in_memory:
      files = [raw_datum.filename for raw_datum in self.raw_data]
      for filename in files:
        try:
          os.remove(filename)
        except OSError:
          logger.debug("could not delete file '{0}'.".format(filename))

  def main(self, argv):
    '''
    Main routine of the Unfoldr class.
    '''
    limits_arg, parser = self._build_parser()
    self.options = parser.parse_args(argv)
    self._configure_logging()
    self._check_options(limits_arg)
    logger.debug(self.options)

    if self.options.log_bin:
      self.min_id = np.log10(self.options.limits[0])
      self.max_id = np.log10(self.options.limits[1])
    else:
      self.min_id = self.options.limits[0]
      self.max_id = self.options.limits[1]
    self.min_id = np.int64(np.floor(self.min_id / self.options.binning))
    self.max_id = np.int64(np.floor(self.max_id / self.options.binning))

    raw_data = self._read_files()
    logger.info('files read.')

    self._unfold(raw_data)
    logger.info('data unfolded.')

    self._clean_up()
    logger.info('temporary files deleted.')

    self._save()
    logger.info('file saved.')

def main():
  '''
  Main routine of the program. Mostly exception handling.
  '''
  try:
    Unfoldr().main(sys.argv[1:])
  except KeyboardInterrupt:
    print "\nInterrupted by user."
    return_code = 1
  except ArgumentParserError as e:
    print 'Error: {0}'.format(e)
    logger.debug('ArgumentParserError')
    return_code = 2
  except argparse.ArgumentError as e:
    print 'Error: {0}'.format(e)
    logger.debug('ArgumentError')
    return_code = 2
  except argparse.ArgumentTypeError as e:
    print 'Error: {0}'.format(e)
    logger.debug('ArgumentTypeError')
    return_code = 2
  except Exception as e:
    print 'Error: {0}'.format(e)
    logger.debug(e, exc_info=False)
    return_code = 1
  else:  
    logger.info('program finished without error.')
    return_code = 0

  return return_code

if __name__ == "__main__":
  mp.freeze_support()
  main()
