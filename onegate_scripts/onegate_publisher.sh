#!/bin/bash
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
 
ONEGATE_URL=$1
ONEGATE_TOKEN=$2
VMID=$3
DELAY=$4

TMP_DIR=`mktemp -d`
 
while true
do
	echo "" > $TMP_DIR/metrics
	
	MEM_TOTAL_4k=`grep DirectMap4k: /proc/meminfo | awk '{print $2}'`
	MEM_TOTAL_2M=`grep DirectMap2M: /proc/meminfo | awk '{print $2}'`
	MEM_TOTAL_REAL=$((MEM_TOTAL_4k+MEM_TOTAL_2M))
	
	MEM_FREE=`grep MemFree: /proc/meminfo | awk '{print $2}'`
	MEM_BUFFERED=`grep Buffers: /proc/meminfo | awk '{print $2}'`
	MEM_CACHED=`grep Cached: /proc/meminfo | grep -v Swap | awk '{print $2}'`
	
	# Add the cache and buffers to free memory
	MEM_FREE=`expr $MEM_FREE + $MEM_BUFFERED + $MEM_CACHED`
	
	MEM_TOTAL=`grep MemTotal: /proc/meminfo | awk '{print $2}'`
	 
	echo "MEM_TOTAL = $MEM_TOTAL" >> $TMP_DIR/metrics
	echo "MEM_TOTAL_REAL = $MEM_TOTAL_REAL" >> $TMP_DIR/metrics
	echo "MEM_FREE = $MEM_FREE" >> $TMP_DIR/metrics
	
	# TODO: do no send the information if the values are the same (or similar) to the last values
	curl -X "PUT" --header "X-ONEGATE-TOKEN: $ONEGATE_TOKEN" --header "X-ONEGATE-VMID: $VMID" $ONEGATE_URL --data-binary @$TMP_DIR/metrics
	sleep $DELAY
done
