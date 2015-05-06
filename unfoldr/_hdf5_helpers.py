# -*- coding: utf-8 -*-

import numpy as np

def _convert_to_dtype(arr, dt):    
  arr2 = np.empty(len(arr), dtype=dt)
  converter={'S':str,
             'f':float,
             'i':int}
  kinds=[dt[i].kind for i in range(len(dt))]
  for i, (kind, name) in enumerate(zip(kinds, dt.names)):
    arr2[name] = map(converter[kind],
                     arr[:,i])
  return arr2
