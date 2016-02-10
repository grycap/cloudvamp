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

import os
import logging.config
import logging
import ConfigParser

def parse_options(config, section_name, config_class):
	options = config.options(section_name)
	for option in options:
		option = option.upper()
		if option in config_class.__dict__ and not option.startswith("__"):
			if isinstance(config_class.__dict__[option], bool):
				config_class.__dict__[option] = config.getboolean(section_name, option)
			elif isinstance(config_class.__dict__[option], float):
				config_class.__dict__[option] = config.getfloat(section_name, option)
			elif isinstance(config_class.__dict__[option], int):
				config_class.__dict__[option] = config.getint(section_name, option)
			else:
				config_class.__dict__[option] = config.get(section_name, option)
		else:
			logger = logging.getLogger('InfrastructureManager')
			logger.warn("Unknown option in the IM config file. Ignoring it: " + option)

class Config:
	CVEM_PATH = os.path.dirname(os.path.realpath(__file__ + "/.."))
	DATA_FILE = CVEM_PATH + "/cvem.dat"
	# Amount of free Memory reserved by the SO (aprox.) 
	SYS_MEM_OFFSET = 80000
	# Minimum amount of memory to assign to a VM.
	MEM_MIN = 262144
	# Difference between the amount of the current memory of the VM and the new one to be set to perform the operation (in KB)     
	MEM_DIFF_TO_CHANGE = 1024
	# The Memory Overprovisioning Percentage
	MEM_OVER = 30.0
	# The Memory Overprovisioning Percentage margin
	MEM_MARGIN = 5
	# Cooldown Time (in secs)
	COOLDOWN = 10.0
	# Sleep time between each monitor loop (in secs)
	DELAY = 5
	# Cooldown migration time (in secs)
	MIGRATION_COOLDOWN = 45
	# Host memory margin (in KB) to migrate VM to another host
	HOST_MEM_MARGIN = 102400
	# Maximum number of threads to launch in the monitor
	MAX_THREADS = 1
	# To filter the VMs by user
	USER_FILTER = None
	# Flag to make just a test without modify any VM
	ONLY_TEST = True
	# Minimum amount of free memory to activate the exponential backoff.
	MIN_FREE_MEMORY = 20000
	# Command to change the memory of a VM, parameters:
	#  {hostname}: hostname where the VM is allocated
	#  {vmid}: ID of the VM
	#  {newmemory}: Amount of memory to assign to the VM
	CHANGE_MEMORY_CMD = "virsh -c 'qemu+ssh://{hostname}/system' setmem one-{vmid} {newmemory}"
	# Class child of cvem Monitor to be executed
	MONITOR_CLASS = 'connectors.one.OpenNebula.MonitorONE'

try:
	# First try locally
	logging.config.fileConfig(Config.CVEM_PATH + '/logging.conf')
except:
	# then try in the /etc/cvem directory
	logging.config.fileConfig('/etc/cvem/logging.conf')

logger = logging.getLogger('monitor')

config = ConfigParser.ConfigParser()
config.read([Config.CVEM_PATH + '/cvem.cfg', Config.CVEM_PATH + '/etc/cvem.cfg', '/etc/cvem/cvem.cfg'])

section_name = "cvem"
if config.has_section(section_name):
	parse_options(config, section_name, Config)