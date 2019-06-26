#!/usr/bin/env python
# -*- coding: utf-8 -*-#

# MIT License
#
# Copyright (c) 2019 Pim Witlox
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

import os
import sys

from setuptools import setup

version = "0.1.1"

requirements = ['click', 'click-log', 'requests', 'python-dateutil']

test_requirements = ['pytest', 'tox']

if sys.argv[-1] == "tag":
    os.system("git tag -a {0} -m 'version {1}'".format(version, version))
    os.system("git push origin master --tags")
    sys.exit()

if sys.argv[-1] == "publish":
    os.system("python setup.py sdist upload")
    os.system("python setup.py bdist_wheel upload")
    sys.exit()

if sys.argv[-1] == "test":
    try:
        modules = map(__import__, test_requirements)
    except ImportError as e:
        raise ImportError("{0} is not installed. Install your test requirements.".format(
            str(e).replace("No module named ", ""))
        )
    os.system('py.test')
    sys.exit()

setup(name="dcron-cli",
      version=version,
      description="Distributed Cronlike Scheduler - Command Line Interface",
      long_description=open("README.md").read(),
      author="Pim Witlox",
      author_email="pim@witlox.io",
      url="https://github.com/witlox/dcron-cli",
      license="MIT",
      entry_points={
          "console_scripts": [
              "dcron-cli = cli.application:main",
          ]
      },
      packages=[
          "cli"
      ],
      include_package_data=True,
      install_requires=requirements,
      python_requires=">=3.4",
      keywords="Python, Python3",
      project_urls={
          "Documentation": "https://dcron-cli.readthedocs.io/en/latest/",
          "Source": "https://github.com/witlox/dcron-cli",
          "Tracker": "https://github.com/witlox/dcron-cli/issues",
      },
      test_suite="tests",
      tests_require=test_requirements,
      classifiers=["Development Status :: 4 - Beta",
                   "Intended Audience :: System Administrators",
                   "Natural Language :: English",
                   "Environment :: Console",
                   "License :: OSI Approved :: MIT License",
                   "Programming Language :: Python",
                   "Programming Language :: Python :: 3",
                   "Programming Language :: Python :: 3.7",
                   "Topic :: Software Development :: Libraries",
                   "Topic :: Utilities"],
      )
