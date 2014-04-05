Price Tracker
=========================

Overview
=========================

Price Tracker is a very simple tracker of Amazon product prices.

In a config (see request.example) add your AWS credentials, Amazon product ids that you want to track and your Gmail credentials. 

This might eventually turn into a useful webapp or something. Knowning me, probably not. So use command line. 

Sending g-emails with smtplib.

What you'll need
==========================

* Python 2.7+ or Python 3.2+
* Redis server - (http://redis.io/topics/quickstart)
* redis-py - (https://pypi.python.org/pypi/redis/)
* AWS account - access and secret key pair (https://aws.amazon.com/)
* Amazon Associates Account - Amazon associates tag (https://affiliate-program.amazon.com/gp/associates/network/main.html)
* Amazon Simple Product API - (https://github.com/yoavaviram/python-amazon-simple-product-api)
* Gmail account and password or application-specific password if you are using 2 factor authentication (and you should) - (https://support.google.com/accounts/answer/185833?hl=en)