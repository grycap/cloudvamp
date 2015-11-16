About CloudVAMP
==================

What is CloudVAMP?
---------------------------

CloudVAMP stands for "Cloud Virtual Machine Automatic Memory Procurement" and it is an automatic system that enables and manages memory oversubscription in a Cloud on-premises platform based in OpenNebula.

Why CloudVAMP?
-----------------------

Users typically deploy Virtual Machines (VMs) with more resources allocated (e.g. memory) than actually needed by the applications running in the VMs. This might happen for different reasons: i) Users are unaware of the actual requirements of applications due to a lack of profiling; ii) The applications might show dynamic memory consumption during their execution; iii) The Cloud Management Framework (e.g. OpenNebula, OpenStack) determines the amount of memory allocated for the VM out of a set of predefined templates.

How does CloudVAMP work?
-------------------------------------

CloudVAMP steals the memory that is not used in the running VMs on an OpenNebula Cloud, and makes it available for other VMs. If the memory is later needed by the original VM, it is returned to it.

What are the technical details?
--------------------------------------

If an excess of free memory for a VM is detected, CloudVAMP changes the amount of memory allocated to the VM via the underlying hypervisor (i.e. KVM) so that it fits the used memory (plus an additional margin of memory), thus considering the running applications. The host that is hosting the VM will then have an extra amount of "stolen memory" that can be used for the deployment of additional VMs on that host. Therefore, CloudVAMP introduces the ability of oversubscription for an on-premises Cloud.

CloudVAMP also prevents overloading, i.e. when the sum of memory allocated to the VMs within a host is greater than the physical amount of memory available for the host. For this, if additional memory is reclaimed by a VM, CloudVAMP uses live migration of VMs across hosts in order to safely prevent overloading without VM downtime.
