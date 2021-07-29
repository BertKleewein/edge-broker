## Make sure you have python 3.6+ installed

Make sure you have python 3.6, 3.7, 3.8, or 3.9 installed.   Run `python --version` to verify:
```
(Python-3.6.10) bertk@bertk-hp:~/temp/broker$ python --version
Python 3.6.10
```

If have python 2.7, you may be able to install python 3 using `sudo apt install python3 python3-pip`

If you have python 2 and python 3 both installed, you may just need to use the `python3` command until we're done setting up the virtual environment.

The instuctions will use `python3`.  This should work even if you don't have python 2 installed.  If this doesn't work, just replace `python3` with `python` in the following instructions.

## Set up your virtual environment

Next, we set up a virtual environment.  This gives us a safe space to install Python libraries without changing your "global" python configuration.

First, install the `virtualenv` library
```
python3 -m pip install virtualenv
```

Then, create your virtual environment in some directory.  This can go anywhere.  The last directory segment defines the name of the environment.  Let's use `~/env/iothub-broker`:

```
python3 -m venv ~/env/iothub-broker
```

Then, activate your virtual environment.  You need to do this any time you wnat to work with this code.
```
source ~/env/iothub-broker/bin/activate
```

On Windows, there will be an `activate.cmd` in the `iothub-broker/bin` directory that does the same thing.

After you do this, your prompt will change to include the `iothub-broker` name.

```
bertk@bertk-hp:~$ source ~/env/iothub-broker/bin/activate
(iothub-broker) bertk@bertk-hp:~$
```

At this point, you are using the python and pip executables from inside the `~/env/iothub-broker` directory, and all libraries that you install will also be stored in this directory.

## Install dependent libraries
Now that we're in the virtual environment, you can use `python3` or `python` commands since they both point to the same thing.

To install the dependent libraries, run pip in this directory:
```
pip install -r requirements.txt
```

This should install Paho as well as a few other libraries that we need.  You can verify this with `pip list`:
```
(iothub-broker) bertk@bertk-hp:~/temp/broker$ pip list
Package           Version
----------------- --------
paho-mqtt         1.5.1
pip               18.1
setuptools        40.6.2
six               1.16.0
typing-extensions 3.10.0.0
```

(If it gives you a warning about upgrading `pip`, feel free to do so.  It's not required, but it doesn't hurt either.)  

## Set your connection string
The sample apps look for the connection string in the environment variable `IOTHUB_CONNECTION_STRING`.  Set this variable:
```
export IOTHUB_CONNECTION_STRING="HostName=FOO;DeviceId=BAR;SharedAccessKey=BAZINGA="
```
