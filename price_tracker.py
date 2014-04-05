#!/usr/bin/env python
from amazon.api import AmazonAPI
from ConfigParser import SafeConfigParser
import redis
import smtplib

def connect_to_amazon(file):
    config = SafeConfigParser()
    config.read(file)
    access_key = config.get('credentials', 'AMAZON_ACCESS_KEY')
    secret_key = config.get('credentials', 'AMAZON_SECRET_KEY')
    assoc_tag = config.get('credentials', 'AMAZON_ASSOC_TAG')
    connection = AmazonAPI(access_key, secret_key, assoc_tag)
    return connection

def get_products(file):
    config = SafeConfigParser()
    config.read(file)
    products =  dict(config.items('products'))
    return products

# Only send email to yourself, no spamming here
def send_email(file, text):
    config = SafeConfigParser()
    config.read(file)
    gmail_user = config.get("gmail", "address")
    gmail_pwd = config.get("gmail", "pwd")
    FROM = config.get("gmail", "address")
    TO = [config.get("gmail", "address")]
    SUBJECT = "Alert from Amazon Price tracker"
    # Prepare actual message
    message = """\From: %s\nTo: %s\nSubject: %s\n\n%s
    """ % (FROM, ", ".join(TO), SUBJECT, text)
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.login(gmail_user, gmail_pwd)
        server.sendmail(FROM, TO, message)
        server.close()
        print 'successfully sent the mail'
    except:
        print "failed to send mail"

# entry in redis will look like
# title: "price_old:price_new"
def do_things_with_redis(redis_server, amazon, products):
    for product_id in products.itervalues():
        product = amazon.lookup(ItemId=product_id)
        title = product.title
        price_now, currency = product.price_and_currency
        price = redis_server.get(title)
        if price:
            price_older, price_old = price.split(':')
            key = str(price_old) + ":" + str(price_now)
            redis_server.set(title, key)
            difference = float(price_now) - float(price_old)
            if difference != 0.0:
                if difference < 0.0:
                    message = "Hey, looks like price for " + title + " have decreased by " + str(difference) + " from " + str(float(price_old)) +  " to " + str(float(price_now))
                    send_email('request', message)
                else:
                    message = "Hey, looks like price for " + title + " have increased by " + str(difference) + " from " + str(float(price_old)) +  " to " + str(float(price_now))
                    send_email('request', message)
        else:
            print "This is a first run of the program, adding initial data..."
            key = str(price_now) + ":" + str(price_now)
            redis_server.set(title, key)

def main():
    redis_server = redis.StrictRedis(host='localhost', port=6379, db=0)
    amazon = connect_to_amazon('request')
    products = get_products('request')
    do_things_with_redis(redis_server, amazon, products)

if __name__ == "__main__":
    main()