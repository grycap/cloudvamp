#!/usr/bin/python
# -------------------------------------------------------------------------- #
# Copyright 2015, Universitat Politecnica de Valencia                        #
#                                                                            #
# Licensed under the Apache License, Version 2.0 (the "License"); you may    #
# not use this file except in compliance with the License. You may obtain    #
# a copy of the License at                                                   #
#                                                                            #
# http://www.apache.org/licenses/LICENSE-2.0                                 #
#                                                                            #
# Unless required by applicable law or agreed to in writing, software        #
# distributed under the License is distributed on an "AS IS" BASIS,          #
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.   #
# See the License for the specific language governing permissions and        #
# limitations under the License.                                             #
#--------------------------------------------------------------------------- #

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
import os

# Add special files
datafiles = []
datafiles.append(('/etc/init.d', ['scripts/cvem']))
datafiles.append(('/etc/cvem', ['etc/cvem.cfg']))
datafiles.append(('/etc/cvem', ['etc/one.cfg']))
datafiles.append(('/etc/cvem', ['logging.conf']))

setup(name="CVEM", version="0.2.1",
	author='GRyCAP - Universitat Politecnica de Valencia',
	author_email='micafer1@upv.es',
	url='https://github.com/grycap/cloudvamp',
	packages=['cvem', 'connectors', 'connectors.one'],
	scripts=["cvemd.py"],
	data_files=datafiles,
	license="Apache License, Version 2.0, https://www.apache.org/licenses/LICENSE-2.0",
	long_description="",
	description="CVEM - Cloud Virtual Elasticity Manager",
	platforms=["any"],
	install_requires=[]
)
