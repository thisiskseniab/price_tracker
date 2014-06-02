Price Tracker
=========================

Overview
=========================

Price Tracker is a very simple tracker of Amazon product prices.

In a config (see request.example) add your AWS credentials, Amazon product ids that you want to track and your Gmail credentials.

This might eventually turn into a useful webapp or something. Knowing me, probably not. So use command line.

Sending g-emails with smtplib.

What you'll need
==========================

* Python 2.7+
* [Redis server](http://redis.io/topics/quickstart)
* [redis-py](https://pypi.python.org/pypi/redis/)
* [gdata python library](https://developers.google.com/gdata/articles/python_client_lib)
* [AWS account](https://aws.amazon.com/) - access and secret key pair
* [Amazon Associates Account](https://affiliate-program.amazon.com/gp/associates/network/main.html) - Amazon associates tag
* [Amazon Simple Product API](https://github.com/yoavaviram/python-amazon-simple-product-api)
* Gmail account and password or [application-specific password](https://support.google.com/accounts/answer/185833?hl=en) if you are using 2 factor authentication (and you should)
* An empty spreadsheet in Google Drive titled "Amazon Price Tracker"

Installation
=========================

* Clone this project
* Install all the prerequisites
* Rename request.example file to 'request'
* Edit request file with your list of Amazon products and product IDs, your AWS credentials, Amazon associates tag, and Gmail address and password
* Run price_tracker.py occasionally or set up a cron job to run it automatically for you
* If using crobjob:
```
$ crontab -e
# This example will run the price tracker every hour
0 */1 * * * /absolute/path/to/price_tracker.py --file "/absolute/path/to/request"
```

TODO:
============================
Not in any particular order
* accept args from the command line for the following options:
  * ~~path to request file~~
  * ~~clean up redis data~~
  * first run
  * no spreadsheets
  * email only when price decreased
  * clear all data from redis and/or gdrive
* improvements to spreadsheet editing:
  * instead of clearing out spreadsheet every time append date/price columns to the existing spreadsheet - gdata api limitation
  * create spreadsheet instead relying on the user to do it - gdata api limitation
* provide Vagrantfile/manifest for users who would prefer to run price_tracker from a VM
