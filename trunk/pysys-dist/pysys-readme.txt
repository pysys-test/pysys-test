PySys 0.3.1 Readme
==================

Dependencies
------------


Installation
------------
Installation on windows is performed by downloading the PySys-X.Y.Z.win32.exe 
installer executable and running. To install on unix systems you should download
the source tar.gz archive and perform the following

 $ tar zxvpf PySys-X.Y.Z.tar.gz
 $ cd PySys-X.Y.Z
 $ python setup.py build
 $ python setup.py install
 
To install you may need to have root privileges on the machine. Installation on 
both windows and unix will install the PySys modules into the site-packages area
of the default python. 


Running the Samples
-------------------
PySys has a set of basic examples to demonstrate it's use for running automated 
and manual testcases. The samples are distributed in a unix line ending friendly 
tar.gz archive, and a windows line ending friendly zip file. To unpack the tests 
on unix systems use

 $ tar zxvpf PySys-examples.X.Y.Z.tar.gz
 $ cd pysys-examples/fibonacci/testcases

To run or print information on the testcases, use the pysys.py script installed in
to the scripts directory of the python install. For more information on the usage
of the script use "pysys.py -h", or "pysys.py run -h" | "pysys.py print -h".
