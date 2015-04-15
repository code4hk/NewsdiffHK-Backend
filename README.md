NewsdiffHK
==========

This is the backend of Newsdiff HK.  The frontend lives [here](https://github.com/code4hk/Newsdiff-Frontend).

Inspired by and modified from similar projects in [Taiwan](https://github.com/ronnywang/newsdiff) and [US](https://github.com/ecprice/newsdiffs).

Dev Environment Setup
---------------------

Install mongodb and start it up:

    $mongod --dbpath <path to ur dev db>

To create a virtual environment and install the dependencies:

    $ virtualenv -p python3 newsdiff
    $ source newsdiff/bin/activate
    $ pip3 install -r requirements.txt

To run the scraper:
	
	$ python3 main.py &

To track the log:

	$ tail news_diff.log -f

To deactivate the virtual environment after use:

    $ deactivate
   
