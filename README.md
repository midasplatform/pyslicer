pyslicer
========

midas viewable python console to interact with slicer


To install and run the twisted based python server that will accept http requests from Midas and
create Slicer jobs in response, first you will need to install a python2.6.




Download and extract a Slicer nightly binary, the directory where this is extracted to is `SLICER_DIR` (where the Slicer exe should be contained in).

Also, in the `library/twserver.cfg` file, set the path to your slicer exe like so:

```
slicer_path=SLICER_DIR/Slicer
```

Now change directories into your SLICER_DIR.

```
cd SLICER_DIR
```

As of Slicer Nightly Build 10-16-2012, you will no longer need to manually create the include path or copy over pyconfig.h

We will need a pyconfig.h header for python26 in order to install pip.  You can get this from an ubuntu python system install of 2.6 at 
`/usr/include/python2.6`



Since we will also be compiling twisted, we will need all headers here, so go ahead and copy them over.

```bash
mkdir lib/Python/include
mkdir lib/Python/include/python2.6
cp /usr/include/python2.6/*.h lib/Python/include/python2.6/
```




Download and install distribute and pip, you will have to replace the path to the python exe with
the path to your installed python 2.6 interpreter exe.

```bash
curl http://python-distribute.org/distribute_setup.py > distribute_setup.py
./Slicer --launch /usr/bin/python distribute_setup.py 
curl https://raw.github.com/pypa/pip/master/contrib/get-pip.py > get_pip.py
./Slicer --launch /usr/bin/python get_pip.py 
```

Now that pip is installed in your Slicer Python, you can run pip to install pydas and the pydas depedencies.

```bash
./Slicer --launch SLICER_DIR/lib/Python/bin/pip install pydas
```

You will need to install twisted, but I had trouble with this step:

```bash
./Slicer --launch SLICER_DIR/lib/Python/bin/pip install twisted
```

An alternate approach is to download the source of twisted, extract it yourself to `TWISTED_DIR`, then run this command there:

```bash
SLICER_DIR/Slicer --no-main-window --python-script setup.py install
```



Now you could run your `twserver.py` using your Slicer Python like this :

```bash
SLICER_DIR/Slicer --no-main-window --python-script twserver.py
```

