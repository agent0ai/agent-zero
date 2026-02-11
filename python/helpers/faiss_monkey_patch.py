# import sys
# from types import ModuleType, SimpleNamespace

# import numpy  # real numpy

# # for python 3.12 on arm, faiss needs a fake cpuinfo module


# """ This disgusting hack was brought to you by:
# https://github.com/facebookresearch/faiss/issues/3936
# """

# faiss_monkey_patch.py  – import this before faiss -----------------
import sys
import types
from types import SimpleNamespace

import numpy as np

# fake numpy.distutils and numpy.distutils.cpuinfo packages
dist = types.ModuleType("numpy.distutils")
cpuinfo = types.ModuleType("numpy.distutils.cpuinfo")

# cpu attribute that looks like the real one
cpuinfo.cpu = SimpleNamespace(  # type: ignore
    # FAISS only does   .info[0].get('Features', '')
    info=[{}]
)

# register in sys.modules
dist.cpuinfo = cpuinfo  # type: ignore
sys.modules["numpy.distutils"] = dist
sys.modules["numpy.distutils.cpuinfo"] = cpuinfo

# crucial: expose it as an *attribute* of the already-imported numpy package
np.distutils = dist  # type: ignore
# -------------------------------------------------------------------

import warnings  # noqa: E402 — must follow monkey-patch setup above

with warnings.catch_warnings():
    warnings.simplefilter("ignore", DeprecationWarning)
    import faiss  # noqa: F401 — side-effect import: loads faiss C extension
