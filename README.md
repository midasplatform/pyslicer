pyslicer
========

midas viewable python console to interact with slicer


1) To install and run the twisted based python server that will accept http requests from Midas and
create Slicer jobs in response, first you will need to install python (2.6+).

2) Download and extract a Slicer nightly binary, the directory where this is extracted to is SLICER_DIR (where the Slicer exe should be contained in).

3) Update the library/twserver.cfg file:  
3a) Set the path to your slicer exe like so:

slicer_path=SLICER_DIR/Slicer

3b) Set the Slicer proxy server URL like so:

proxy_url=YOUR_PROXY_URL

4) Install pydas and twisted  
4a) Download and install pip

curl http://python-distribute.org/distribute_setup.py > distribute_setup.py  
[sudo] python distribute_setup.py  
curl https://raw.github.com/pypa/pip/master/contrib/get-pip.py > get_pip.py  
[sudo] python get_pip.py 

4b) Run pip to install pydas and the pydas dependencies.

pip install pydas

4c) Run pip to install twisted:

pip install twisted

5) Now you could start twisted server like this :

python library/twserver.py

