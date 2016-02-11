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

import time
from multiprocessing.pool import ThreadPool
import cPickle as pickle
import os
from config import Config, logger
from cpyutils.runcommand import runcommand

class VMMonitorData:
	"""
	Class to store monitoring information for each VM 
	"""

	def __init__(self, vm_id):
		self.id = vm_id
		self.last_set_mem = None
		""" The timestamp of the last modification of the memory for each VM """
		self.original_mem = None
		""" The initial memory assigned to each VM """
		self.mem_diff = None
		""" The difference between the initial memory 
		assigned to each VM and the memory provided by the VM monitor """
		self.no_free_memory_count = 0
		""" The number of consecutive occurrences of not having free memory in each VM """

class Monitor:
	"""
	Base class to monitors
	"""
	
	def __init__(self, cmpo = None):
		self.cmp = cmpo
		""" Object child of CMPInfo to connect with the underlying CMP """
		self.last_migration = {}
		""" Dict to store the timestamp of the last migration operation made in each host """
		self.vm_data = {}
		""" Dict to store the monitoring information for each VM """
		
		self.load_data()

	def clean_old_data(self, current_vms):
		"""
		Clean old data from the Monitor
		Delete the values of VMs that do not appear in the
		monitoring system.
		To avoid an uncontrolled increase of memory usage.
		"""
		current_vmids = [vm.id for vm in current_vms]

		try:
			for vmid in self.vm_data.keys():
				if vmid not in current_vmids:
					logger.debug("Removing data for old VM ID: %s" % str(vmid))
					del self.vm_data[vmid]
		except:
			logger.exception("ERROR cleaning old data.")
	
	def load_data(self):
		"""
		Load the monitor data from file
		"""
		if os.path.isfile(Config.DATA_FILE):
			try:
				data_file = open(Config.DATA_FILE, 'r')
				self.vm_data = pickle.load(data_file)
				self.last_migration = pickle.load(data_file)
				data_file.close()
			except Exception:
				logger.exception("ERROR loading data file: " + Config.DATA_FILE + ". Data not loaded.")
		else:
			logger.debug("No data file: " + Config.DATA_FILE)
		
	def save_data(self):
		"""
		Save the monitor data to file
		"""
		try:
			data_file = open(Config.DATA_FILE, 'wb')
			pickle.dump(self.vm_data, data_file)
			pickle.dump(self.last_migration, data_file)
			data_file.close()
		except Exception:
			logger.exception("ERROR saving data to the file: " + Config.DATA_FILE + ". Changes not stored!!")

	def get_host_info(self, host_id):
		if host_id is not None:
			return self.cmp.get_host_info(host_id)
		else:
			logger.error("Trying to get host info from a VM without host.id") 

	def migrate_vm(self, vm_id, host_info, all_vms):
		"""
		Migrate one of the VMs of the host to free memory
		"""
		logger.debug("Migrating.")
		
		vm_to_migrate = self.select_vm_to_migrate(vm_id, host_info, all_vms)
		host_to_migrate = self.select_host_to_migrate(vm_to_migrate)
		if not host_to_migrate:
			logger.warn("There are no host with enough resources to host the VM " + str(vm_to_migrate.id))
			return False
	
		if not Config.ONLY_TEST:
			logger.debug("Migrate the VM %d to host %d" % (vm_to_migrate.id, host_to_migrate.id))
			return self.cmp.migrate(vm_to_migrate.id, host_to_migrate.id)
		else:
			logger.debug("No migrate. This is just a test.")
			return False
	
	def monitor_vm(self, vm, all_vms):
		"""
		Main function of the monitor
		""" 
		vm_pct_free_memory = float(vm.free_memory)/float(vm.total_memory) * 100.0
		
		if vm.id not in self.vm_data:
			self.vm_data[vm.id] = VMMonitorData(vm.id)
		
		if self.vm_data[vm.id].mem_diff is None:
			self.vm_data[vm.id].mem_diff = vm.real_memory - vm.total_memory
		
		vmid_msg = "VMID " + str(vm.id) + ": "
		vm.host = self.get_host_info(vm.host.id)
		
		logger.info(vmid_msg + "Real Memory: " + str(vm.real_memory))
		logger.info(vmid_msg + "Total Memory: " + str(vm.total_memory))
		logger.info(vmid_msg + "Free Memory: %d (%.2f%%)" % (vm.free_memory, vm_pct_free_memory))
		
		mem_over_ratio = Config.MEM_OVER
		if vm.mem_over_ratio:
			mem_over_ratio = vm.mem_over_ratio

		if vm_pct_free_memory < (mem_over_ratio - Config.MEM_MARGIN) or vm_pct_free_memory > (mem_over_ratio + Config.MEM_MARGIN):
			now = time.time()
	
			logger.debug(vmid_msg + "VM %s has %.2f%% of free memory, change the memory size" % (vm.id, vm_pct_free_memory))
			if self.vm_data[vm.id].last_set_mem is not None:
				logger.debug(vmid_msg + "Last memory change was %s secs ago." % (now - self.vm_data[vm.id].last_set_mem))
			else:
				self.vm_data[vm.id].original_mem = vm.allocated_memory
				logger.debug(vmid_msg + "The memory of this VM has been never modified. Store the initial memory  : " + str(self.vm_data[vm.id].original_mem))
				self.vm_data[vm.id].last_set_mem = now
	
			if (now - self.vm_data[vm.id].last_set_mem) < Config.COOLDOWN:
				logger.debug(vmid_msg + "It is in cooldown period. No changing the memory.")
			else:
				used_mem = vm.total_memory - vm.free_memory
				min_free_memory = Config.MIN_FREE_MEMORY
				# check if the VM has defined a specific MIN_FREE_MEMORY value
				if vm.min_free_mem:
					min_free_memory = vm.min_free_mem
				# it not free memory use exponential backoff idea
				if vm.free_memory <= min_free_memory:
					logger.debug(vmid_msg + "No free memory in the VM!")
					if self.vm_data[vm.id].no_free_memory_count > 1:
						# if this is the third time with no free memory use the original size
						logger.debug(vmid_msg + "Increase the mem to the original size.")
						new_mem =  self.vm_data[vm.id].original_mem
						self.vm_data[vm.id].no_free_memory_count = 0
					else:
						logger.debug(vmid_msg + "Increase the mem with 50% of the original.")
						new_mem =  int(used_mem + (self.vm_data[vm.id].original_mem - used_mem) * 0.5)
						self.vm_data[vm.id].no_free_memory_count += 1
				else:
					divider = 1.0 - (mem_over_ratio/100.0)
					logger.debug(vmid_msg + "The used memory %d is divided by %.2f" % (int(used_mem), divider))
					new_mem =  int(used_mem / divider)
				
				# Check for minimum memory
				if new_mem < Config.MEM_MIN:
					new_mem = Config.MEM_MIN
					
				# add diff to new_mem value and to total_memory to make it real_memory (vm.real_memory has delays between updates)
				new_mem += self.vm_data[vm.id].mem_diff
				vm.total_memory += self.vm_data[vm.id].mem_diff
				
				# We never set more memory that the initial amount
				if new_mem > self.vm_data[vm.id].original_mem:
					new_mem = self.vm_data[vm.id].original_mem

				if abs(int(vm.total_memory)-new_mem) < Config.MEM_DIFF_TO_CHANGE:
					logger.debug(vmid_msg + "Not changing the memory. Too small difference.")
				else:
					logger.debug(vmid_msg + "Changing the memory from %d to %d" % (vm.total_memory, new_mem))
					if new_mem > vm.total_memory:
						# If we increase the memory we must check if the host has enough free space to avoid overcommitting 
						if not self.host_has_memory_free(vm.host,new_mem-vm.total_memory):
							# The host has not enough free memory. Let's try to migrate a VM.
							logger.debug(vmid_msg + "The host " + vm.host.name + " has not enough free memory!. Let's try to migrate a VM.")
							if vm.host.id in self.last_migration and (now - self.last_migration[vm.host.id]) < Config.MIGRATION_COOLDOWN:
								logger.debug("The host %s is in migration cooldown period, let's wait.." % vm.host.name)
							else: 
								if self.migrate_vm(vm.id, vm.host, all_vms):
									logger.debug("A VM has been migrated from host %d. Store the timestamp." % vm.host.id)
									self.last_migration[vm.host.id] = now
						else:
							logger.debug(vmid_msg + "The host " + vm.host.name + " has enough free memory.")
							self.change_memory(vm.id, vm.host, new_mem)
							self.vm_data[vm.id].last_set_mem = now
					else:
						self.change_memory(vm.id, vm.host, new_mem)
						self.vm_data[vm.id].last_set_mem = now

	@staticmethod
	def get_monitored_vms(vm_list, user = None):
		"""
		Get the list of VMs that has the monitored metrics available and filtered by user
		"""
		res = []
		for vm in vm_list:
			if vm.free_memory:
				# Check the user filter
				if not user or vm.user_id == user:  
					res.append(vm)
	
		return res

	def start(self):
		"""
		Launch the monitor loop
		"""
		pool = ThreadPool(processes=Config.MAX_THREADS)
	
		while True:
			all_vms = self.cmp.get_vm_list()
			monitored_vms = self.get_monitored_vms(all_vms, Config.USER_FILTER)
			
			if monitored_vms:
				pool.map(lambda vm: self.monitor_vm(vm, all_vms), monitored_vms)
			else:
				logger.debug("There is no VM with monitoring information.")
	
			logger.debug("-----------------------------------")

			self.clean_old_data(monitored_vms)
			self.save_data()
			time.sleep(Config.DELAY)

	@staticmethod
	def power_on_host(free_memory, cpus, delay = 5, timeout = None):
		"""
		Try to power on a node connecting with CLUES
		
		Args:
		- free_memory: amount of memory needed in the host.
		- cpus: number of cpus needed in the host.
		- delay: number of seconds to sleep when waiting the request to be served (default 5).
		- timeout: timeout (in secs) to wait the request to be served (default configcli.config_client.CLUES_REQUEST_WAIT_TIMEOUT).

		Return: True if a host has been powered on or False otherwise. 
		"""
		try:
			import configcli
			if not timeout:
				timeout = configcli.config_client.CLUES_REQUEST_WAIT_TIMEOUT
			clues_server = configcli.get_clues_proxy_from_config()
			success, r_id = clues_server.request_create(configcli.config_client.CLUES_SECRET_TOKEN, cpus, free_memory, 1, "")
			
			if not success:
				logger.error("Error creating a CLUES request: %s" % r_id)
				return False
			
			now = time.time()
			
			served = False
			while not served:
				success, served = clues_server.request_wait(configcli.config_client.CLUES_SECRET_TOKEN, r_id, 1)
				
				if success and served:
					return True
				elif ((time.time() - now) > timeout):
					return False
				else:
					time.sleep(delay)
			
			return served
		except ImportError:
			logger.warn("Error trying to import configcli. It seems that CLUES client library is not installed.")
			return False
		except Exception, ex:
			logger.warn("Error trying to power on a node with CLUES: %s" + str(ex))
			return False

	# Specific CMP subclasses must implement these methods 

	@staticmethod
	def host_has_memory_free(host_info,free_memory):
		"""
		Check if a node has enough free memory available
		
		Args:
		- host_info: HostInfo object of the host to check.
		- free_memory: amount of memory needed in the host.

		Return: True if the host has enough free memory or False otherwise. 
		"""
		raise Exception("Not implemented")
		
	@staticmethod
	def select_vm_to_migrate(req_vm_id, host_info, all_vms):
		"""
		Get the ID of the VM to migrate. 
		
		Args:
		- req_vm_id: ID of the growing memory VM that causes the migration.
		- host_info: HostInfo object of the host where the VM has to go out.
		- all_vms: List of VirtualMachineInfo objects with all the VMs of the CMP.

		Return: VirtualMachineInfo object with the VM to migrate 
		"""
		raise Exception("Not implemented")
	
	@staticmethod
	def select_host_to_migrate(vm_info):
		"""
		Get the ID of the HOST to migrate.
		
		Args:
		- vm_info: VirtualMachineInfo object with the VM to migrate

		Return: HostInfo of the Host to migrate 
		"""
		raise Exception("Not implemented")
	
	@staticmethod
	def change_memory(vm_id, vm_host, new_mem):
		"""
		Function to change the memory of the VM
		
		Args:
		- vm_id: ID of the VM to change the memory.
		- vm_host: Host where the VM is allocated.
		- new_mem: Amount of memory to set to the VM.

		Return: ID of the Host to migrate 
		"""
		chmem_cmd = Config.CHANGE_MEMORY_CMD.format(hostname = vm_host.name, vmid = str(vm_id), newmemory = str(new_mem))
	
		logger.debug("Change the memory of VM: " + str(vm_id) + " to " + str(new_mem))
		logger.debug("Executing: " + chmem_cmd)
		if not Config.ONLY_TEST:
			success, out = runcommand(chmem_cmd, shell=True)

			if success:
				logger.debug("chmem command output: " + out)
			else:
				logger.error("Error changing memory: " + out)
		else:
			logger.debug("Not executed. This is just a test.")
