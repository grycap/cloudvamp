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
from cvem.config import logger
from cvem.CMPInfo import VirtualMachineInfo, HostInfo, CMPInfo
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
		values = [ 'CPU', 'MEMORY', 'NAME', 'RANK', 'REQUIREMENTS', 'VMID', 'VCPU', 'PACKEDMEMORY', 'MAXMEMORY' ]
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
		values = [ 'ID','UID','NAME','LAST_POLL','STATE','LCM_STATE','DEPLOY_ID','MEMORY','CPU','NET_TX','NET_RX', 'STIME','ETIME' ]
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
			vm_filter = -3
			# To get all
			#vm_filter = -2
			(success, res_info, _) = server.one.vmpool.info(ConfigONE.ONE_ID, vm_filter, -1, -1, 3)
		except:
			logger.exception("Error getting the VM list")
			return []
	
		if success:
			res_vm = VM_POOL(res_info)
			res = []
			for vm in res_vm.VM:
				host = HostInfo(int(vm.HISTORY_RECORDS.HISTORY[0].HID), vm.HISTORY_RECORDS.HISTORY[0].HOSTNAME)
				new_vm = VirtualMachineInfo(int(vm.ID), host, vm.TEMPLATE.MEMORY * 1024, vm)
				new_vm.user_id = vm.UID
				if vm.USER_TEMPLATE.MEM_TOTAL:
					new_vm.set_memory_values(int(vm.USER_TEMPLATE.MEM_TOTAL_REAL),
										int(vm.USER_TEMPLATE.MEM_TOTAL),
										int(vm.USER_TEMPLATE.MEM_FREE))
				if vm.USER_TEMPLATE.MIN_FREE_MEM:
					new_vm.min_free_mem = vm.USER_TEMPLATE.MIN_FREE_MEM
				if vm.USER_TEMPLATE.MEM_OVER:
					new_vm.mem_over_ratio = vm.USER_TEMPLATE.MEM_OVER

				res.append(new_vm)
				
			return res
		else:
			logger.error("Error getting the VM list: " + res_info)
			return []
	
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