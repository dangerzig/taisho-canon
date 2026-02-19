"""Fast implementations of performance-critical functions.

Tries to import Cython-compiled versions; falls back to pure Python.
Build Cython with: python3 setup.py build_ext --inplace

Set DIGEST_NO_CYTHON=1 to force pure-Python fallback (useful for debugging
and profiling without Cython overhead).
"""

import logging
import os

logger = logging.getLogger(__name__)

if os.environ.get("DIGEST_NO_CYTHON"):
    from ._fast_fallback import (  # noqa: F401
        fast_ngram_hashes,
        fast_find_seeds,
        fast_fuzzy_extend,
    )
    logger.debug("Using pure-Python fallback (DIGEST_NO_CYTHON set)")
else:
    try:
        from ._fast import (  # noqa: F401  # type: ignore[import-not-found]
            fast_ngram_hashes,
            fast_find_seeds,
            fast_fuzzy_extend,
        )
        logger.debug("Using Cython implementation")
    except ImportError:
        from ._fast_fallback import (  # noqa: F401
            fast_ngram_hashes,
            fast_find_seeds,
            fast_fuzzy_extend,
        )
        logger.debug("Cython not available, using pure-Python fallback")
