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

import ConfigParser
from cvem.config import Config, parse_options

class ConfigONE:
	# Data to connect to the XML-RCP API of OpenNebula
	ONE_SERVER = None
	ONE_PORT = 2633
	ONE_ID = None

config = ConfigParser.ConfigParser()
config.read([Config.CVEM_PATH + '/one.cfg', Config.CVEM_PATH + '/etc/one.cfg', '/etc/cvem/one.cfg'])

section_name = "one"
if config.has_section(section_name):
	parse_options(config, section_name, ConfigONE)