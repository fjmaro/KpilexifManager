"""
------------------------------------------------------------------------------
KpilexifManager <https://github.com/fjmaro/KpilexifManager>
Copyright 2022 Francisco José Mata Aroco

This file is part of KpilexifManager (hereinafter called "Library").

This "Library" is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the licence, or
(at your option) any later version.

This "Library" is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

See LICENSE.md for more details.
------------------------------------------------------------------------------
"""

# pylint: disable=line-too-long
from distutils.core import setup
import kpilexifmanager

with open("README.md", "r", encoding='utf-8') as fhd:
    long_description = fhd.read()

setup(name="KpilexifManager",
      version=kpilexifmanager.__version__,
      license="GPLv3+",
      author=kpilexifmanager.__author__,
      url="https://github.com/fjmaro/KpilexifManager",
      description="Python tool for images exif and metadata treatment with Pillow and Piexif libraries",
      long_description=long_description,
      classifiers=[
          "Development Status :: 3 - Alpha",
          "Intended Audience :: Developers",
          "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
          "Programming Language :: Python :: 3",
          "Topic :: Multimedia"],
      python_requires='>=3.9',
      packages=["kpilexifmanager"],
      install_requires=['piexif==1.1.3', 'pillow==8.4.0',
                        'kmarotools @ git+https://github.com/fjmaro/KmaroTools@main'])
