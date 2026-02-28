"""Build script for Cython extensions.

Usage:
    python3 setup.py build_ext --inplace
"""

from setuptools import setup, Extension

try:
    from Cython.Build import cythonize
    extensions = cythonize(
        [Extension("digest_detector._fast", ["digest_detector/_fast.pyx"])],
        compiler_directives={
            "language_level": "3",
            "boundscheck": False,
            "wraparound": False,
        },
    )
except ImportError:
    # Cython not installed — skip compilation
    extensions = []

setup(
    name="digest_detector",
    python_requires=">=3.10",
    ext_modules=extensions,
)
