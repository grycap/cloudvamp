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

import time
import subprocess
from multiprocessing.pool import ThreadPool
import cPickle as pickle
import os
from cvem.config import Config, logger
from cpyutils.runcommand import runcommand

from connectors.one.OpenNebula import OpenNebula as CMP

class Monitor:
	"""
	Base class to monitors
	"""
	
	def __init__(self):
		self.last_set_mem = {}
		""" Dict to store the timestamp of the last modification of the memory for each VM """
		self.original_mem = {}
		""" Dict to store the initial memory assigned to each VM """
		self.mem_diff = {}
		""" Dict to store the difference between the initial memory 
		assigned to each VM and the memory provided by the VM monitor """
		self.last_migration = {}
		""" Dict to store the timestamp of the last migration operation made in each host """
		
		self.load_data()
	
	def load_data(self):
		"""
		Load the monitor data from file
		"""
		if os.path.isfile(Config.DATA_FILE):
			try:
				data_file = open(Config.DATA_FILE, 'r')
				self.last_set_mem = pickle.load(data_file)
				self.original_mem = pickle.load(data_file)
				self.mem_diff = pickle.load(data_file)
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
			pickle.dump(self.last_set_mem, data_file)
			pickle.dump(self.original_mem, data_file)
			pickle.dump(self.mem_diff, data_file)
			pickle.dump(self.last_migration, data_file)
			data_file.close()
		except Exception:
			logger.exception("ERROR saving data to the file: " + Config.DATA_FILE + ". Changes not stored!!")

	@staticmethod
	def get_host_info(host_id):
		if host_id:
			return CMP.get_host_info(host_id)
		else:
			logger.error("Trying to get host info from a VM without host.id") 

	def migrate_vm(self, vm_id, host_info, all_vms):
		"""
		Migrate one of the VMs of the host to free memory
		"""
		logger.debug("Migrating.")
		
		vm_id_to_migrate, vm_mem = self.select_vm_to_migrate(vm_id, host_info, all_vms)
		logger.debug("Migramos la VM %d al host %d" % (vm_id, host_info.id))
		host_id_to_migrate = self.select_host_to_migrate(vm_mem)
		if not host_id_to_migrate:
			logger.warn("There are no host with enough free memory to host the VM " + str(vm_id_to_migrate))
			return False
	
		if not Config.ONLY_TEST:
			return CMP.migrate(vm_id_to_migrate, host_id_to_migrate)
		else:
			logger.debug("No migrate. This is just a test.")
			return False
	
	def monitor_vm(self, vm, all_vms):
		"""
		Main function of the monitor
		"""
		vm_pct_free_memory = float(vm.free_memory)/float(vm.total_memory) * 100.0
		if vm.id not in self.mem_diff:
			self.mem_diff[vm.id] = vm.real_memory - vm.total_memory
		
		vm.total_memory += self.mem_diff[vm.id]
		
		vmid_msg = "VMID " + str(vm.id) + ": "
		vm.host = Monitor.get_host_info(vm.host.id)
		#logger.debug(vmid_msg + "VM is in Host: " + vm.host.name + ". PACKEDMEMORY = " + str(vm.host.raw.TEMPLATE.PACKEDMEMORY))
		
		logger.info(vmid_msg + "Total Memory: " + str(vm.total_memory))
		logger.info(vmid_msg + "Free Memory: %d" % vm.free_memory)
		if vm_pct_free_memory < (Config.MEM_OVER - Config.MEM_MARGIN) or vm_pct_free_memory > (Config.MEM_OVER + Config.MEM_MARGIN):
			now = time.time()
	
			logger.debug(vmid_msg + "VM %s has %.2f of free memory, change the memory size" % (vm.id, vm_pct_free_memory))
			if vm.id in self.last_set_mem:
				logger.debug(vmid_msg + "Last memory change was %s secs ago." % (now - self.last_set_mem[vm.id]))
			else:
				self.original_mem[vm.id] = vm.total_memory
				logger.debug(vmid_msg + "The memory of this VM has been never modified. Store the initial memory  : " + str(self.original_mem[vm.id]))
				self.last_set_mem[vm.id] = now
	
			if (now - self.last_set_mem[vm.id]) < Config.COOLDOWN:
				logger.debug(vmid_msg + "It is in cooldown period. No changing the memory.")
			else:
				multiplier = 1.0 + (Config.MEM_OVER/100.0)
				mem_usada = vm.total_memory - vm.free_memory
				logger.debug(vmid_msg + "The used memory %d is multiplied by %.2f" % (int(mem_usada), multiplier))
				new_mem =  int(mem_usada * multiplier)
				# We never set more memory that the initial amount
				if new_mem > self.original_mem[vm.id]:
					new_mem = self.original_mem[vm.id]
				elif new_mem < Config.MEM_MIN:
					new_mem = Config.MEM_MIN
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
							self.last_set_mem[vm.id] = now
					else:
						self.change_memory(vm.id, vm.host, new_mem)
						self.last_set_mem[vm.id] = now

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
			all_vms = CMP.get_vm_list()
			monitored_vms = self.get_monitored_vms(all_vms, Config.USER_FILTER)
			
			for vm in monitored_vms:
				self.monitor_vm(vm, all_vms)
			
			if monitored_vms:
				pool.map(lambda vm: self.monitor_vm(vm, all_vms), monitored_vms)
			else:
				logger.debug("There is no VM with monitoring information.")
	
			logger.debug("-----------------------------------")
			self.save_data()
			time.sleep(Config.DELAY)

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

		Return: ID of the VM to migrate 
		"""
		raise Exception("Not implemented")
	
	@staticmethod
	def select_host_to_migrate(free_memory):
		"""
		Get the ID of the HOST to migrate.
		
		Args:
		- free_memory: amount of memory needed in the destination host of the VM to migrate.

		Return: ID of the Host to migrate 
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
		raise Exception("Not implemented")

class MonitorONE(Monitor):
	"""
	Monitor for OpenNebula
	"""
	@staticmethod
	def change_memory(vm_id, vm_host, new_mem):
		"""
		Function to change the memory of the VM using the virsh command
		"""
		vm_name = "one-" + str(vm_id)
		# This command require the cvemd daemon to be executed with the oneadmin user and have configured the ssh access without password 
		virsh_cmd = "virsh -c 'qemu+ssh://oneadmin@" + vm_host.name + "/system' setmem " + vm_name + " " + str(new_mem)
	
		logger.debug("Change the memory from " + str(vm_id) + " to " + str(new_mem))
		logger.debug("Executing: " + virsh_cmd)
		if not Config.ONLY_TEST:
			success, out = runcommand(virsh_cmd, shell=True)

			if success:
				logger.debug("virsh output: " + out)
			else:
				logger.error("Error changing memory: " + out)
		else:
			out = "Not executed. This is just a test."

	@staticmethod
	def host_has_memory_free(host_info,free_memory):
		"""
		Check if a node has enough free memory available
		"""
		if host_info:
			host_free_memory = host_info.raw.HOST_SHARE.MAX_MEM - host_info.raw.HOST_SHARE.MEM_USAGE
			logger.debug("The host %s has %d KB of free memory." % (host_info.name, host_free_memory))
			if host_free_memory - free_memory > Config.HOST_MEM_MARGIN:
				return True
			else:
				return False
		else:
			return False

	@staticmethod
	def select_host_to_migrate(free_memory):
		"""
		Get the ID of the HOST to migrate. It selects the HOST with more free memory.
		If no node has enough memory to host the VM to migrate, return None.
		"""
		host_list = CMP.get_host_list()
		
		hosts_mem = {} 
		# Select the node with more memory free
		for host in host_list:
			hosts_mem[host.id] = host.raw.HOST_SHARE.MAX_MEM - host.raw.HOST_SHARE.MEM_USAGE
		
		hosts_mem = sorted(hosts_mem.items(), key=lambda x: x[1], reverse = True)
		
		if hosts_mem[0][1] > free_memory:
			return hosts_mem[0][0]
		else:
			return None

	@staticmethod
	def select_vm_to_migrate(req_vm_id, host_info, all_vms):
		"""
		Get the ID of the VM to migrate. It selects the VM with less memory avoiding to migrate VM with ID "req_vm_id"
		"""
		vms_mem = {} 
		for vm_id in host_info.raw.VMS.ID:
			for vm in all_vms:
				if int(vm_id) == vm.id and req_vm_id != vm.id:
					vms_mem[vm.id] = vm.total_memory
					if not vms_mem[vm.id]:
						# If the monitored total memory is not available use the CMP original allocated one 
						vms_mem[vm.id] = vm.allocated_memory
		
		# if we want to get the biggest one set reverse=True
		vms_mem = sorted(vms_mem.items(), key=lambda x: x[1])
		
		return vms_mem[0]

if __name__ == "__main__":

	monitor = MonitorONE()
	monitor.start()