#!/usr/bin/env python
from amazon.api import AmazonAPI
from ConfigParser import SafeConfigParser
from os import getcwd
import redis
import smtplib

import gdata.spreadsheet.service
import time


def connect_to_amazon(file):
    config = SafeConfigParser()
    config.read(file)
    access_key = config.get('credentials', 'AMAZON_ACCESS_KEY')
    secret_key = config.get('credentials', 'AMAZON_SECRET_KEY')
    assoc_tag = config.get('credentials', 'AMAZON_ASSOC_TAG')
    connection = AmazonAPI(access_key, secret_key, assoc_tag)
    return connection

def get_guser_gpwd(file):
    config = SafeConfigParser()
    config.read(file)
    gmail_user = config.get('gmail', 'address')
    gmail_pwd = config.get('gmail', 'pwd')
    return gmail_user, gmail_pwd

def get_products(file):
    config = SafeConfigParser()
    config.read(file)
    products =  dict(config.items('products'))
    return products

# Only send email to yourself, no spamming here
def send_email(file, text):
    gmail_user, gmail_pwd = get_guser_gpwd(file)
    FROM = gmail_user
    TO = [gmail_user]
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
        print "Successfully sent the mail"
    except Exception as e:
        print "Failed to send mail"
        print e

def get_spreadsheet_info(file):
    gmail_user, gmail_pwd = get_guser_gpwd(file)

    client = gdata.spreadsheet.service.SpreadsheetsService() 
    client.debug = False
    client.email = gmail_user
    client.password = gmail_pwd
    client.source = 'Adding Amazon Price Tracker data' 
    client.ProgrammaticLogin()

    query = gdata.spreadsheet.service.DocumentQuery()
    query['title'] = 'Amazon Price Tracker'
    query['title-exact'] = 'true'
    feed = client.GetSpreadsheetsFeed(query=query)
    spreadsheet_id = feed.entry[0].id.text.rsplit('/',1)[1]
    worksheet_id = 'od6'

    return client, spreadsheet_id, worksheet_id

def spreadsheet_setup(file):
    client, spreadsheet_id, worksheet_id = get_spreadsheet_info(file)

    # Set up a query with empty cells
    query = gdata.spreadsheet.service.CellQuery()
    query.return_empty = 'true'
    query.min_row = '1'
    query.max_row = '50'
    query.min_col = '1'
    query.max_col = '4'
    cells = client.GetCellsFeed(spreadsheet_id, wksht_id=worksheet_id, query=query)

    batch_request = gdata.spreadsheet.SpreadsheetsCellsFeed()

    # Add headers
    cells.entry[0].cell.inputValue = 'product'
    batch_request.AddUpdate(cells.entry[0])
    cells.entry[1].cell.inputValue = 'date'
    batch_request.AddUpdate(cells.entry[1])
    cells.entry[2].cell.inputValue = 'lowestprice'
    batch_request.AddUpdate(cells.entry[2])
    cells.entry[3].cell.inputValue = 'currentprice'
    batch_request.AddUpdate(cells.entry[3])

    try:
        client.ExecuteBatch(batch_request, cells.GetBatchLink().href)
    except Exception as e:
        print e

def clear_spreadsheet(file):
    client, spreadsheet_id, worksheet_id = get_spreadsheet_info(file)

    # Set up a query that starts at row 2
    query = gdata.spreadsheet.service.CellQuery()
    query.min_row = '2'

    # Pull just those cells
    cells_no_headers = client.GetCellsFeed(spreadsheet_id, wksht_id=worksheet_id, query=query)
    batch_request = gdata.spreadsheet.SpreadsheetsCellsFeed()

    # Iterate through every cell in the CellsFeed, replacing each one with ''
    for i, entry in enumerate(cells_no_headers.entry):
        entry.cell.inputValue = ''
        batch_request.AddUpdate(cells_no_headers.entry[i])

    try:
        client.ExecuteBatch(batch_request, cells_no_headers.GetBatchLink().href)
    except Exception as e:
        print e

def write_spreadsheet(file, title, prices):
    client, spreadsheet_id, worksheet_id = get_spreadsheet_info(file)

    price_old, price_new = prices.split(':')

    row = {'product': title , 'date': time.strftime("%d/%m/%Y %H:%M:%S"), \
                                'lowestprice': price_old , 'currentprice': price_new }
    try:
        client.InsertRow(row, spreadsheet_id, worksheet_id)
    except Exception as e:
        print e


# entry in redis will look like
# title: "price_lowest:price_new"
def track_prices(redis_server, amazon, products, file):
    try:
        # Before we add any new data, clear the spreadsheet
        clear_spreadsheet(file)
    except Exception as e:
        print "Something went wrong while accessing 'Amazon Price Tracker' spreadsheet"
        print "Does it exist?"
        print "Real error:"
        print e
        return
    for product_id in products.itervalues():
        product = amazon.lookup(ItemId=product_id)
        title = product.title
        price_now, currency = product.price_and_currency
        price = redis_server.get(title)
        if price:
            price_older, price_old = price.split(':')
            # Keep around only the lowest price ever at all times
            if price_older < price_old:
                key = str(price_older) + ":" + str(price_now)
                difference = float(price_now) - float(price_older)
            else:
                key = str(price_old) + ":" + str(price_now)
                difference = float(price_now) - float(price_old)
            # Add data to redis
            redis_server.set(title, key)
            # Write data to gdrive spreadsheet
            write_spreadsheet(file, title, key)
            # Compute the difference between prices and send an email with appropriate message
            if difference != 0.0:
                if difference < 0.0:
                    message = "Hey, looks like price for " + title + " have decreased by " + str(difference) + " lowest price : new price is " + key
                    send_email(file, message)
                else:
                    message = "Hey, looks like price for " + title + " have increased by " + str(difference) + " lowest price : new price is " + key
                    send_email(file, message)
            else:
                message = "Hey, no difference here for "+ title + " lowest price : new price is " + key
        else:
            print "This is a first run of the program, adding initial data for " + title
            key = str(price_now) + ":" + str(price_now)
            redis_server.set(title, key)
            # Setup spreadsheet
            spreadsheet_setup(file)
            # Add first data to it
            write_spreadsheet(file, title, key)

def main():
    cwd = getcwd()
    request_file = cwd+'/request'
    # If using a cronjob to run price tracker
    # uncomment next line and provide absolute path to the request file
    # request_file = '/absolute/path/to/request'
    redis_server = redis.StrictRedis(host='localhost', port=6379, db=0)
    amazon = connect_to_amazon(request_file)
    products = get_products(request_file)
    track_prices(redis_server, amazon, products, request_file)

if __name__ == "__main__":
    main()