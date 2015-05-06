# -*- coding: utf-8 -*-

import cython
import numpy as np
cimport numpy as np

np.import_array()

@cython.boundscheck(False)
@cython.wraparound(False)
@cython.nonecheck(False)
@cython.cdivision(True) 
@cython.profile(False)
cpdef np.ndarray[np.float64_t] _process_sorted_eigval(np.ndarray[np.float64_t] eigval,
                                                      np.ndarray[np.float64_t]  unfolding_pool,
                                                      int unfolding_pool_count):
  cdef int i, j
  cdef np.ndarray[np.float64_t] spacings = np.zeros(len(eigval)-1,
                                                    dtype=np.float64)
  cdef int l_eigval = len(eigval)
  cdef int l_unfolding_pool = len(unfolding_pool)

  i = 0
  for j in range(l_eigval):
    while unfolding_pool[i] <= eigval[j]:
      i += 1
      if i >= l_unfolding_pool:
        break
    if j + 1 < l_eigval:
      spacings[j] -= np.float64(i) / np.float64(unfolding_pool_count)
    if j > 0:
      spacings[j-1] += np.float64(i) / np.float64(unfolding_pool_count)
  return spacings
