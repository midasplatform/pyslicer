pyslicer
========

midas viewable python console to interact with slicer


To install and run the twisted based python server that will accept http requests from Midas and
create Slicer jobs in response, first you will need to install a python2.6.




Download and extract a Slicer nightly binary, the directory where this is extracted to is SLICER_DIR (where the Slicer exe should be contained in).

Also, in the library/twserver.cfg file, set the path to your slicer exe like so:

slicer_path=SLICER_DIR/Slicer

Now change directories into your SLICER_DIR.


cd SLICER_DIR

# install distribute

wget http://python-distribute.org/distribute_setup.py
./Slicer distribute_setup.py 

# install pip

wget --no-check-certificate https://raw.github.com/pypa/pip/master/contrib/get-pip.py
./Slicer get-pip.py 

# install requests

#download the source to SLICER_DIR/requests
#in SLICER_DIR/requests
../Slicer setup.py install

# install pydas

#define a file install_distributions.py:

def install_distributions(distributions):
  """
  Copied from http://threebean.org/blog/2011/06/06/installing-from-pip-inside-python-or-a-simple-pip-api/
  """
  import pip.commands.install
  command = pip.commands.install.InstallCommand()
  opts, args = command.parser.parse_args()
  # TBD, why do we have to run the next part here twice before actual install
  requirement_set = command.run(opts, distributions)
  requirement_set = command.run(opts, distributions)
  requirement_set.install(opts)

install_distributions(['pydas'])

# then call
./Slicer install_distributions.py

# test your installs

./Slicer --no-main-window --disable-cli-modules --disable-loadable-modules --disable-scripted-loadable-modules --show-python-interactor

# in the python shell, test that these work without error
import pydas
import requests


# install twisted


#Since we will also be compiling twisted, we will need all headers here, so go ahead and copy them over.

cp /usr/include/python2.6/*.h lib/Python/include/python2.6/

# download and extract the source of twisted to the SLICER_DIR, then in the Twisted source dir:

../Slicer  --no-main-window --python-script setup.py install

# you may have to kill slicer at the end of the successful install

# test these imports in the slicer python console


import twisted.internet
import twisted.web.server













Now you could run your twserver.py using your Slicer Python like this :

SLICER_DIR/Slicer --no-main-window --disable-loadable-modules --disable-scripted-loadable-modules --python-script twserver.py
