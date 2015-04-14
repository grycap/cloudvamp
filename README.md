# CloudVAMP - Cloud Virtual Machine Automatic Memory Packing
(c) 2015 - Universitat Politecnica de Valencia - GRyCAP

## 1. ABOUT

### 1.1 What is CloudVAMP?

CloudVAMP stands for "Cloud Virtual Machine Automatic Memory Packing" and it is an automatic system that enables and manages memory overcommiting in a Cloud on-premises platform based in OpenNebula.

### 1.2 Why CloudVAMP?

Users usually have Virtual Machines (VM) with more resources than needed wether they are able to request a free amount of resources and they do not know what are the actual requirements for the application that they are inteded to run, or there are fixed templates for the  VM and they exceed the requirements of the applications.
  
### 1.3 How does CloudVAMP work?
  
CloudVAMP "borrows" the memory that is not used in the running VM, and makes it available for other VMs. If the memory is later needed by the original VM, it is returned to it.
  
### 1.4 What are the technical details?

If a VM is not using part of the memory, CloudVAMP varies the amount of memory allocated by the hypervisor to the VM to fit (with a margin) the running applications. The host that is hosting the VM will then have an extra amount of "packed memory" that can be assigned to other VMs.

That is why memory overcommiting may happen, as the sum of memory requested by the VMs hosted in the host is greater than the physical amount of memory. If memory is later needed and the host is memory-overcommited, CloudVAMP will use live-migration of VMs to make rooom for the VMs.

## 2. Installing

The current version of CloudVAMP is available for OpenNebula. It has been tested in version 4.8 but it is likely to work with version 4.0 and upper of OpenNebula. The installation consists of three steps:

1. CloudVAMP agent
2. CloudVAMP memory reporter
3. CloudVAMP overcommitment granter

###2.1 Getting CloudVAMP from git

#### Download CloudVAMP from git:
  ```
    $ cd /tmp
    $ git clone https://github.com/grycap/cloudvamp
  ```
or
  ```
    $ cd /tmp 
    $ wget https://github.com/grycap/cloudvamp/archive/master.zip
    $ unzip cloudvamp-master.zip
    $ mv cloudvamp-master cloudvamp
  ```
  
###2.2 Installing CloudVAMP agent (aka CVEM)

####2.2.1 Requirements
  
CVEM uses the library cpyutils. Follow the instructions from `https://github.com/grycap/cpyutils` to install it.

####2.2.2 Install in the system path

Enter the CVEM directory in the downloaded files and perform the setup installation.
  ```
    $ cd /tmp/cloudvamp/cvem
    $ python setup install
  ```

####2.2.3 Install in a specific path

Select a proper path where to install the CVEM service (i.e. `/usr/local/cvem`, `/opt/cvem` or other). This path will be called `CVEM_PATH`.
  ```
    $ cp -r cd /tmp/cloudvamp/cvem /usr/local
  ```

Finally you must copy (or link) `$CVEM_PATH/scripts/cvem` file to `/etc/init.d` directory.
  ```
    $ ln -s /usr/local/cvem/scripts/cvem /etc/init.d
  ```

####2.2.4 Configuration

In case that you want the CVEM service to be started at boot time, you must execute the next set of commands:

On Debian Systems:
  ```
    $ chkconfig cvem on
  ```
On RedHat Systems:
  ```
    $ update-rc.d cvem start 99 2 3 4 5 . stop 05 0 1 6 .
  ```
Or you can do it manually:
  ```
    $ ln -s /etc/init.d/cvem /etc/rc2.d/S99cvem
    $ ln -s /etc/init.d/cvem /etc/rc3.d/S99cvem
    $ ln -s /etc/init.d/cvem /etc/rc5.d/S99cvem
    $ ln -s /etc/init.d/cvem /etc/rc1.d/K05cvem
    $ ln -s /etc/init.d/cvem /etc/rc6.d/K05cvem
  ```
Adjust the installation path by setting the DAEMON variable at `/etc/init.d/cvem` to the path where the CVEM `cvemd.py` file is installed (e.g. `/usr/local/cvem/cvemd.py`), or set the name of the script file (`cvemd.py`) if the file is in the `PATH`.
  
Finally edit the configurations files *.cfg located in the etc/ directory where the CVEM is installed (e.g `/opt/cvem/etc`) or in the `/etc/cvem` directory:

* `cvem.cfg`: CVEM configuration file.
* `one.cfg`: OpenNebula specific configuration file.

###2.3 Installing CloudVAMP memory reporter

The memory reporter relies on the OpenNebula contextualization scripts. So it must be installed on the Virtual Machine images used in the platform. See more information in `http://docs.opennebula.org/4.12/user/virtual_machine_setup/bcont.html`
  
It uses the OneGate system to publish and get the so OneGate must be installed and configured: `http://archives.opennebula.org/documentation:rel4.4:onegate_usage`
  
The first step is to upload the contextualization scripts located in `/tmp/cloudvamp/onegate_scripts/` (`onegate_init.sh`, `onegate_publisher.sh`) to the OpenNebula "Files & Kernels" section.
  
Then all the templates of the VMs must be configured to activate the OpenNebula contextualization Token, include both files, and set `onegate_init.sh` as an init script:
  
  ```
    CONTEXT = [
        FILES_DS = "$FILE[IMAGE_ID=<init_file_id>] $FILE[IMAGE_ID=<publisher_file_id>]",
        INIT_SCRIPTS = "onegate_init.sh",
        TOKEN = "YES" ]
  ```

###2.4 Installing CloudVAMP overcommitment granter

####2.4.1 Getting the IM and the VMM

The CloudVAMP overcommitment granter consists of 2 parts: a Infrastructure Manager (IM) and a Virtual Machine Manager (VMM).
  
Use at your risk (it has been tested in Ubuntu, with a ONE 4.8 installation from the official opennebula repositories).
  
Create a folder for cloudvamp vmm at ONE's vmm folder (usually `/var/lib/one/remotes/vmm`) and create links to the files in kvm folder:
  
  ```
    $ mkdir /var/lib/one/remotes/vmm/cloudvamp
    $ cd /var/lib/one/remotes/vmm/cloudvamp
    $ ln -s ../kvm/* .
  ```
  
Now copy the new files in the folder
  
  ```
    $ cp /tmp/cloudvamp/opennebula/vmm/cloudvamp/* /var/lib/one/remotes/vmm/cloudvamp/
  ```

Create a folder for cloudvamp im probes files at ONE's im folder (usually `/var/lib/one/remotes/im`) and create links to the files in kvm folder:
  
  ```
    $ mkdir /var/lib/one/remotes/im/cloudvamp-probes.d
    $ cd /var/lib/one/remotes/im/cloudvamp-probes.d
    $ ln -s ../kvm-probes.d/* .
    $ rm kvm.rb
    $ chmod 644 poll.sh
  ```
  
* NOTE: take into account that file "poll.sh" must not have permission for execution (i.e. its permission mask is 0644). The file is left for completion purposes, but it is not used to avoid an unnecesary delay as its results are included in file cloudvamp.rb
  
Now copy the new files in the folder
  
  ```
    $ cp /tmp/cloudvamp/opennebula/im/cloudvamp-probes.d/* /var/lib/one/remotes/im/cloudvamp-probes.d/
  ```
  
And create a folder for the cloudvamp im as a link to the kvm one:
  
  ```
    $ ln -s /var/lib/one/remotes/im/kvm.d /var/lib/one/remotes/im/cloudvamp.d
  ```
    
####2.4.2 Activating CloudVAMP in ONE
  
Edit the one configuration file (i.e. `/etc/one/oned.conf`) and add the following lines
  
  ```
    IM_MAD = [
        name       = "cloudvamp",
        executable = "one_im_ssh",
        arguments  = "-r 3 -t 15 cloudvamp" ]
  
    VM_MAD = [
      name       = "cloudvamp",
      executable = "one_vmm_exec",
      arguments  = "-t 15 -r 0 cloudvamp",
      default    = "vmm_exec/vmm_exec_kvm.conf",
      type       = "kvm" ]
  ```

And restart ONE
  ```
  $ su - oneadmin
  $ one restart
  ```
  
####2.4.3 Activating CloudVAMP for the nodes
  
Now you should delete (or deactivate) the nodes under the control of ONE and create them again using the cloudvamp im and vmm. This will only apply to these VMs that are running the KVM hypervisor
  
> E.g. (in this case we are using dummy network)
  
  ```
  $ onehost disable myhost01
  $ onehost create myhost01 -i cloudvamp -v cloudvamp -n dummy
  ```
  
####2.4.4 Tunning CloudVAMP memory
  
In case that you do not want that all the memory borrowed from the running vms is dedicated to other VMs, you can tune the $O value from file `/var/lib/one/remotes/im/cloudvamp-probes.d/cloudvamp.rb`.
  
> E.g. If you want that only the 80% of borrowed memory is dedicated for possible autocomission, please search for the line $O = 1.0 and set it to $O = 0.8 (take into account that it is a floating point number, in case that you get back to 100%)
