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

from cpyutils.xmlobject import XMLObject
from cpyutils.timeoutxmlrpccli import ServerProxy
from cvem.config import logger, Config
from cvem.CMPInfo import VirtualMachineInfo, HostInfo, CMPInfo
from cvem.Monitor import Monitor
from config_one import ConfigONE

# classes to parse the results of the ONE API using xmlobject
class NIC(XMLObject):
		values = ['BRIDGE', 'IP', 'MAC', 'NETWORK', 'VNID']

class OS(XMLObject):
		values = ['BOOT', 'ROOT']

class GRAPHICS(XMLObject):
		values = ['LISTEN', 'TYPE']

class DISK(XMLObject):
		values = ['CLONE','READONLY','SAVE','SOURCE','TARGET' ]

class TEMPLATE(XMLObject):
		# In ONE versions <= 4.12 PACKEDMEMORY, MAXMEMORY and REALMEMORY are located here
		values = [ 'CPU', 'MEMORY', 'NAME', 'RANK', 'REQUIREMENTS', 'VMID', 'VCPU', 'PACKEDMEMORY', 'MAXMEMORY', 'REALMEMORY' ]
		tuples = { 'GRAPHICS': GRAPHICS, 'OS': OS }
		tuples_lists = { 'DISK': DISK, 'NIC': NIC }
		numeric = [ 'CPU', 'MEMORY', 'VCPU' ]
		noneval = 0

class HISTORY(XMLObject):
		values = ['SEQ', 'HOSTNAME', 'HID', 'STIME', 'ETIME', 'PSTIME', 'PETIME', 'RSTIME', 'RETIME' ,'ESTIME', 'EETIME', 'REASON' ]

class HISTORY_RECORDS(XMLObject):
	tuples_lists = { 'HISTORY': HISTORY }

class USER_TEMPLATE(XMLObject):
		values = [ 'MEM_FREE', 'MEM_TOTAL', 'MEM_TOTAL_REAL', 'MIN_FREE_MEM', 'MEM_OVER']
		numeric = [ 'MEM_FREE', 'MEM_TOTAL', 'MEM_TOTAL_REAL', 'MIN_FREE_MEM', 'MEM_OVER']

class VM(XMLObject):
		STATE_INIT=0
		STATE_PENDING=1
		STATE_HOLD=2
		STATE_ACTIVE=3
		STATE_STOPPED=4
		STATE_SUSPENDED=5
		STATE_DONE=6
		STATE_FAILED=7
		STATE_STR = {'0': 'init', '1': 'pending', '2': 'hold', '3': 'active', '4': 'stopped', '5': 'suspended', '6': 'done', '7': 'failed' }
		LCM_STATE_STR={'0':'init','1':'prologing','2':'booting','3':'running','4':'migrating','5':'saving (stop)','6':'saving (suspend)','7':'saving (migrate)', '8':'prologing (migration)', '9':'prologing (resume)', '10': 'epilog (stop)','11':'epilog', '12':'cancel','13':'failure','14':'delete','15':'unknown'}
		# In ONE versions >= 4.14 PACKEDMEMORY, MAXMEMORY and REALMEMORY are located here
		values = [ 'ID','UID','NAME','LAST_POLL','STATE','LCM_STATE','DEPLOY_ID','MEMORY','CPU','NET_TX','NET_RX', 'STIME','ETIME', 'PACKEDMEMORY', 'MAXMEMORY', 'REALMEMORY' ]
		tuples = { 'TEMPLATE': TEMPLATE, 'HISTORY_RECORDS': HISTORY_RECORDS, 'USER_TEMPLATE': USER_TEMPLATE }
		numeric = [ 'ID', 'UID', 'STATE', 'LCM_STATE', 'STIME','ETIME' ]

class VM_POOL(XMLObject):
	tuples_lists = { 'VM': VM }

class LEASE(XMLObject):
	values = [ 'IP', 'MAC', 'USED' ]

class TEMPLATE_VNET(XMLObject):
	values = [ 'BRIDGE', 'NAME', 'TYPE', 'NETWORK_ADDRESS' ]
	tuples_lists = { 'LEASES': LEASE }

class LEASES(XMLObject):
	tuples_lists = { 'LEASE': LEASE }
	
class RANGE(XMLObject):
	values = [ 'IP_START', 'IP_END' ]
	
class AR(XMLObject):
	values = [ 'IP', 'MAC', 'TYPE', 'ALLOCATED', 'GLOBAL_PREFIX', 'AR_ID' ]
	
class AR_POOL(XMLObject):
	tuples_lists = { 'AR': AR }

class VNET(XMLObject):
	values = [ 'ID', 'UID', 'GID', 'UNAME', 'GNAME', 'NAME', 'TYPE', 'BRIDGE', 'PUBLIC' ]
	tuples = { 'TEMPLATE': TEMPLATE_VNET, 'LEASES': LEASES, 'RANGE': RANGE, 'AR_POOL':AR_POOL }
	
class VNET_POOL(XMLObject):
	tuples_lists = { 'VNET': VNET }

class HOST_SHARE(XMLObject):
	values = [ 'MEM_USAGE', 'MAX_MEM', 'FREE_MEM', 'FREE_CPU', 'MAX_CPU' ]
	numeric = [ 'MEM_USAGE', 'MAX_MEM', 'FREE_MEM', 'FREE_CPU', 'MAX_CPU' ]

class TEMPLATE_HOST(XMLObject):
	values = [ 'PACKEDMEMORY' ]
	numeric = [ 'PACKEDMEMORY' ]

class VMS(XMLObject):
	values_lists = { 'ID' }

class HOST(XMLObject):
	STATE_INIT=0
	STATE_MONITORING_MONITORED=1
	STATE_MONITORED=2
	STATE_ERROR=3
	STATE_DISABLED=4
	STATE_MONITORING_ERROR=5
	STATE_MONITORING_INIT=6
	STATE_MONITORING_DISABLED=7
	INVALID_STATES = [STATE_ERROR, STATE_DISABLED, STATE_MONITORING_ERROR, STATE_MONITORING_DISABLED]
	values = [ 'ID', 'LAST_MON_TIME', 'NAME', 'STATE' ]
	numeric = [ 'ID', 'STATE' ]
	tuples = { 'HOST_SHARE': HOST_SHARE, 'TEMPLATE': TEMPLATE_HOST, 'VMS': VMS}
	
class HOST_POOL(XMLObject):
	tuples_lists = { 'HOST': HOST }
	
	
class OpenNebula(CMPInfo):
	"""
	OpenNebula CMPInfo subclass
	"""

	@staticmethod
	def get_vm_list():
		server_url = "http://%s:%d/RPC2" % (ConfigONE.ONE_SERVER, ConfigONE.ONE_PORT)
		try:
			server = ServerProxy(server_url,allow_none=True,timeout=10)
			# To get only ONE_ID user's resources
			#vm_filter = -3
			# To get all
			vm_filter = -2
			(success, res_info, _) = server.one.vmpool.info(ConfigONE.ONE_ID, vm_filter, -1, -1, 3)
		except:
			logger.exception("Error getting the VM list")
			return []

		if success:
			res_vm = VM_POOL(res_info)
			res = []
			for vm in res_vm.VM:
				host = HostInfo(int(vm.HISTORY_RECORDS.HISTORY[0].HID), vm.HISTORY_RECORDS.HISTORY[0].HOSTNAME)
				new_vm = VirtualMachineInfo(int(vm.ID), host, int(vm.TEMPLATE.MEMORY) * 1024, vm)
				new_vm.user_id = vm.UID
				if vm.USER_TEMPLATE.MEM_TOTAL:
					# to make it work on all ONE versions
					real_memory = vm.TEMPLATE.REALMEMORY
					if not real_memory:
						real_memory = vm.REALMEMORY
					new_vm.set_memory_values(int(real_memory),
										int(vm.USER_TEMPLATE.MEM_TOTAL),
										int(vm.USER_TEMPLATE.MEM_FREE))
					if vm.USER_TEMPLATE.MIN_FREE_MEM:
						new_vm.min_free_mem = vm.USER_TEMPLATE.MIN_FREE_MEM
					if vm.USER_TEMPLATE.MEM_OVER:
						new_vm.mem_over_ratio = vm.USER_TEMPLATE.MEM_OVER
				
					# publish MEM properties to the VM user template to show the values to the user 
					OpenNebula._publish_mem_info(new_vm)

				res.append(new_vm)
				
			return res
		else:
			logger.error("Error getting the VM list: " + res_info)
			return []

	@staticmethod
	def _publish_mem_info(vm):
		"""
		Publish MIN_FREE_MEM and MEM_OVER properties to the VM user template to show the values to the user
		
		Args:
		- vm: VirtualMachineInfo with the VM info.

		Return: True if the information is published successfully or False otherwise 
		"""
		template = ""
		if not vm.min_free_mem:
			template += "MIN_FREE_MEM = %d\n" % Config.MIN_FREE_MEMORY
		if not vm.mem_over_ratio:
			template += "MEM_OVER = %.2f\n" % Config.MEM_OVER
		
		# if there is nothing to update return True
		if not template:
			return True 
		
		server_url = "http://%s:%d/RPC2" % (ConfigONE.ONE_SERVER, ConfigONE.ONE_PORT)
		try:
			server = ServerProxy(server_url,allow_none=True,timeout=10)
			(success, res_info, _) = server.one.vm.update(ConfigONE.ONE_ID, vm.id, template, 1)
			if not success:
				logger.error("Error updating the template to show the mem info to the VM ID: %s. %s." % (vm.id, res_info))
			return success
		except:
			logger.exception("Error updating the template to show the mem info to the VM ID: %s." % vm.id)
			return False
		
		return True
	
	@staticmethod
	def get_host_info(host_id):
		server_url = "http://%s:%d/RPC2" % (ConfigONE.ONE_SERVER, ConfigONE.ONE_PORT)
		try:
			server = ServerProxy(server_url,allow_none=True,timeout=10)
			(success, res_info, _) = server.one.host.info(ConfigONE.ONE_ID, host_id)
		except:
			logger.exception("Error getting the host info: " + host_id)
			return None
		
		if success:
			host_info = HOST(res_info)
			res_host = HostInfo(int(host_info.ID), host_info.NAME, host_info.STATE not in HOST.INVALID_STATES, host_info) 
			return res_host
		else:
			logger.error("Error getting the host info: " + res_info)
			return None
	
	@staticmethod
	def get_host_list():
		server_url = "http://%s:%d/RPC2" % (ConfigONE.ONE_SERVER, ConfigONE.ONE_PORT)
		try:
			server = ServerProxy(server_url,allow_none=True,timeout=10)
			(success, res_info, _) = server.one.hostpool.info(ConfigONE.ONE_ID)
		except:
			logger.exception("Error getting the host list")
			return None
		
		if success:
			res = []
			for host in HOST_POOL(res_info).HOST:
				new_host = HostInfo(host.ID, host.NAME, host.STATE not in HOST.INVALID_STATES, host)
				res.append(new_host)
			return res
		else:
			logger.error("Error getting the host list: " + res_info)
			return None
	
	@staticmethod
	def migrate(vm_id, host_id):
		server_url = "http://%s:%d/RPC2" % (ConfigONE.ONE_SERVER, ConfigONE.ONE_PORT)
		try:
			server = ServerProxy(server_url,allow_none=True,timeout=10)
			(success, res_info, _) = server.one.vm.migrate(ConfigONE.ONE_ID, vm_id, host_id, True, True)
		except:
			logger.exception("Error migrating the VM %d to the host %d" % (vm_id, host_id))
			return False
		
		if success:
			return True
		else:
			logger.error("Error migrating the VM %d to the host %d: %s" % (vm_id, host_id, res_info))
			return False

class MonitorONE(Monitor):
	"""
	Monitor for OpenNebula
	"""
	
	def __init__(self, cmpo = None):
		Monitor.__init__(self, OpenNebula())
	
	@staticmethod
	def host_has_memory_free(host_info,free_memory):
		"""
		Check if a node has enough free memory available
		"""
		if host_info:
			host_free_memory = host_info.raw.HOST_SHARE.FREE_MEM
			logger.debug("The host %s has %d KB of free memory." % (host_info.name, host_free_memory))
			if host_free_memory - free_memory > Config.HOST_MEM_MARGIN:
				return True
			else:
				return False
		else:
			return False

	def select_host_to_migrate(self, vm_info):
		"""
		Get the ID of the HOST to migrate. It selects the HOST with more free memory.
		If no node has enough memory or cpus to host the VM to migrate, return None.
		"""
		host_list = self.cmp.get_host_list()
		
		hosts_mem = {} 
		# Select the node with more memory free
		for host in host_list:
			hosts_mem[host] = host.raw.HOST_SHARE.FREE_MEM
		
		hosts_mem = sorted(hosts_mem.items(), key=lambda x: x[1], reverse = True)
		
		cpus = vm_info.raw.TEMPLATE.CPU
		if vm_info.total_memory:
			free_memory = vm_info.total_memory
		else:
			# If the monitored total memory is not available use the CMP original allocated one 
			free_memory = vm_info.allocated_memory

		powered = None
		while powered != False:
			for host, host_mem in hosts_mem:
				# ONE FREE_CPU is a Percentage
				host_free_cpus = host.raw.HOST_SHARE.FREE_CPU/100
				if host.active and host_mem > free_memory and host_free_cpus > cpus:
					return host
			
			# only try to poweron a host once
			if powered is None:
				# Let's try to power on a host
				powered = Monitor.power_on_host(free_memory, cpus)
			else:
				# otherwise continue
				powered = False
		
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
					if vm.total_memory:
						vms_mem[vm] = vm.total_memory
					else:
						# If the monitored total memory is not available use the CMP original allocated one 
						vms_mem[vm] = vm.allocated_memory
		
		# if we want to get the biggest one set reverse=True
		vms_mem = sorted(vms_mem.items(), key=lambda x: x[1])
		
		return vms_mem[0][0]