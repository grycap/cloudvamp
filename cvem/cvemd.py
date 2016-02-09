#! /usr/bin/env python
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

import sys
import importlib
from cvem.config import Config, logger

if __name__ == "__main__":

	monitor = None
	try:
		module_name, class_name = Config.MONITOR_CLASS.rsplit(".", 1)
		MonitorClass = getattr(importlib.import_module(module_name), class_name)
		monitor = MonitorClass()
	except Exception, ex:
		logger.exception("Error loading Monitor class")
		print "Error loading Monitor class: ", ex
		print "Check if the class name '%s' is correct." % Config.MONITOR_CLASS
		sys.exit(-1)

	monitor.start()