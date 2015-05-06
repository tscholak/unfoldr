# -*- coding: utf-8 -*-

def _pickle_method(method):
  """
  Pickle methods properly, including class methods.
  """
  func_name = method.im_func.__name__
  obj = method.im_self
  cls = method.im_class
  if func_name.startswith('__') and not func_name.endswith('__'):
    cls_name = cls.__name__.lstrip('_')
    func_name = '_' + cls_name + func_name
  return _unpickle_method, (func_name, obj, cls)

def _unpickle_method(func_name, obj, cls):
  """
  Unpickle methods properly, including class methods.
  """
  try:
    for cls in cls.mro():
      try:
        func = cls.__dict__[func_name]
      except KeyError:
        pass
      else:
        break
  except AttributeError:
    func = cls.__dict__[func_name]
  return func.__get__(obj, cls)
