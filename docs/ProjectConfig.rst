Project Configuration
=====================

Each PySys project has a configuration file called ``pysysproject.xml`` at the top level. This file contains 
``property`` elements for any user-defined properties that will be used by your tests such as credentials, server 
names. It also contains allows customization of how PySys executes tests and reports on the results. 

Here is a comprehensive project file with examples of most of the available elements to show what is possible:

.. literalinclude:: ../pysys-examples/pysysproject.xml
  :language: xml
