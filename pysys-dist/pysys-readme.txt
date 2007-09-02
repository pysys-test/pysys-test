PySys 0.3.2 Readme
==================

Dependencies
------------
Running on windows requires installation of the pywin32 extensions written by 
Mark Hammond (http://sourceforge.net/projects/pywin32). Running the manual 
tester on unix systems requires the tcl/tk libraries to be installed on the 
host machine and the Python version to be compiled with tcl/tk support.


Installation
------------
Installation on windows is performed by downloading the PySys-X.Y.Z.win32.exe 
installer executable and running. To install on unix systems you should download
the source tar.gz archive and perform the following

 $ tar zxvpf PySys-X.Y.Z.tar.gz
 $ cd PySys-X.Y.Z
 $ python setup.py build
 $ python setup.py install
 
To install on both windows and unix systems you may need to have root privileges 
on the machine. Installation will install the PySys modules into the site-packages 
area of the default Python. 


Using the "pysys.py" launcher
-----------------------------
PySys installs a launcher script 'pysys.py' as part of the installation process 
to facilitate the management and execution of testcases. On unix systems the script 
is installed into the Python binary directory, e.g. /usr/local/bin, and is hence 
on the default user's path. On windows systems the script is installed into the 
Scripts directory of the Python installation, e.g. c:\Python24\Scripts\pysys.py, 
which is not by default on the user's path. To run on windows systems the Scripts 
directory of the Python installation should be added to the user's path, and all 
.py files associated with the Python binary to allow direct execution of the 
script. 

After installation, to see the available options to the pysys.py script use 

  $ pysys.py --help
  
The script takes three main top level command line options to it, namely 'run', 
'print' and 'make', which are used to run a set of testcases, print the meta data
for a set of testcases, or to make a new testcase directory structure respectively.
For more information on the further options available to each add --help after the 
top level option, e.g. for more information on running a set of testcases use

  $ pysys.py run --help


Running the Samples
-------------------
PySys has a set of basic examples to demonstrate it's use for running automated 
and manual testcases. The samples are distributed in a unix line ending friendly 
tar.gz archive, and a windows line ending friendly zip file. To unpack the tests 
on unix systems use

 $ tar zxvpf PySys-examples.X.Y.Z.tar.gz
 $ cd pysys-examples/fibonacci/testcases

To run the testcases in the fibonacci area, after changing directory to the 
testcases location, perform 
 
 $ pysys.py run
 
 
 

