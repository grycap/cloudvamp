#!/usr/bin/env ruby

# -------------------------------------------------------------------------- #
#                                                                            #
# This is a modified version of the kvm.rb file from OpenNebula KVM IM,      #
# version 4.8. This file include modifications to adapt it to CloudVAMP.     #
# Modifications are concentrated in the first part of the code, although     #
# other parts may also have been modified.                                   #
#                                                                            #
# -------------------------------------------------------------------------- #

# -------------------------------------------------------------------------- #
# Original file                                                              #
# Copyright 2002-2014, OpenNebula Project (OpenNebula.org), C12G Labs        #
#                                                                            #
# CloudVAMP modifications                                                    #
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

def print_info(name, value)
    value = "0" if value.nil? or value.to_s.strip.empty?
    puts "#{name}=#{value}"
end

vmsinfo_text = `../../vmm/cloudvamp/poll --kvm -t`
exit(-1) if $?.exitstatus != 0

# Set the percentage of packed memory dedicated for overcommiting
$O = 1.0

original_vmsinfo_text = vmsinfo_text
$virtual_mem = 0
vmsinfo_text.split(/\n/).each{|line|
	pcontent=line.match('^\s+POLL="(.*)".*$')
	if pcontent
		maxmemory = 0
		usedmemory = 0
		pollres=pcontent.captures[0]
		pollres.split(" ").each{|varval|
			var, val = varval.split("=")
			if var == 'MAXMEMORY' 
				maxmemory = val.to_f
			elsif var == 'USEDMEMORY'
				usedmemory = val.to_f
			end	
		}
		if maxmemory == 0
			maxmemory = usedmemory
		end
		$virtual_mem = $virtual_mem + maxmemory - usedmemory
	end
}

######
#  First, get all the posible info out of virsh
#  TODO : use virsh freecell when available
######

nodeinfo_text = `virsh -c qemu:///system nodeinfo`
exit(-1) if $?.exitstatus != 0

nodeinfo_text.split(/\n/).each{|line|
    if     line.match('^CPU\(s\)')
        $total_cpu   = line.split(":")[1].strip.to_i * 100
    elsif  line.match('^CPU frequency')
        $cpu_speed   = line.split(":")[1].strip.split(" ")[0]
    elsif  line.match('^Memory size')
        $total_memory = line.split(":")[1].strip.split(" ")[0]
    end
}

######
#   for everything else, top & proc
#####

NETINTERFACE = "eth|bond|em|p[0-9]+p[0-9]+"

top_text=`top -bin2`
exit(-1) if $?.exitstatus != 0

top_text.gsub!(/^top.*^top.*?$/m, "") # Strip first top output

top_text.split(/\n/).each{|line|
    if line.match('^%?Cpu')
        line[7..-1].split(",").each{|elemento|
            temp = elemento.strip.split(/[% ]/)
            if temp[1]=="id"
            idle = temp[0]
            $free_cpu = idle.to_f * $total_cpu.to_f / 100
            $used_cpu = $total_cpu.to_f - $free_cpu
                break
            end

        }
    end
}

$total_memory = `free -k|grep "Mem:" | awk '{print $2}'`
tmp=`free -k|grep "buffers\/cache"|awk '{print $3 " " $4}'`.split

$used_memory=tmp[0]
$free_memory=tmp[1]

net_text=`cat /proc/net/dev`
exit(-1) if $?.exitstatus != 0

$netrx = 0
$nettx = 0

net_text.split(/\n/).each{|line|
    if line.match("^ *#{NETINTERFACE}")
        arr   = line.split(":")[1].split(" ")
        $netrx += arr[0].to_i
        $nettx += arr[8].to_i
    end
}

print_info("HYPERVISOR","kvm")
print_info("TOTALCPU",$total_cpu)
print_info("CPUSPEED",$cpu_speed)
print_info("TOTALMEMORY",$total_memory.to_f + ($O * $virtual_mem.to_f))
print_info("PACKEDMEMORY",$virtual_mem)
print_info("USEDMEMORY",$used_memory)
print_info("FREEMEMORY",$free_memory)
print_info("FREECPU",$free_cpu)
print_info("USEDCPU",$used_cpu)
print_info("NETRX",$netrx)
print_info("NETTX",$nettx)

# Remove or coment the following line if you are setting permission for execution for poll.sh
puts original_vmsinfo_text