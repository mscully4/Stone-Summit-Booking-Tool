import json
import os
from selenium import webdriver
import urllib
from time import sleep
import datetime as dt
import requests
import configparser
from dateutil.relativedelta import relativedelta
from twilio.rest import Client

config = configparser.ConfigParser()
config.read('config.ini')

#Env Info
CHROMIUM_LOCATION = '/opt/bin/headless-chromium'
CHROMEDRIVER_LOCATION = '/opt/bin/chromedriver'

#User Info
FIRST_NAME = config['PERSONAL_INFO']['FIRST_NAME']
LAST_NAME = config['PERSONAL_INFO']['LAST_NAME']
EMAIL = config['PERSONAL_INFO']['EMAIL']
PHONE = config['PERSONAL_INFO']['PHONE']
BIRTH_MONTH = config['PERSONAL_INFO']['BIRTH_MONTH']
BIRTH_DAY = config['PERSONAL_INFO']['BIRTH_DAY']
BIRTH_YEAR = config['PERSONAL_INFO']['BIRTH_YEAR']
ADDRESS = config['PERSONAL_INFO']['ADDRESS']
CITY = config['PERSONAL_INFO']['CITY']
STATE = config['PERSONAL_INFO']['STATE']
ZIP = config['PERSONAL_INFO']['ZIP']

#Scheduling Info
CURRENT_TIME = dt.datetime.now()
BOOKING_DATE = dt.datetime.combine(dt.date.today() + dt.timedelta(days=3), dt.time(18, 0))

FROM = BOOKING_DATE.strftime('%-I %p')
TO = (BOOKING_DATE + dt.timedelta(hours=2)).strftime('%-I %p')

API_KEY_2CAPTCHA = config['2CAPTCHA']['API_KEY']
BASE_URL = os.environ['BASE_URL']

ACCOUNT_ID_TWILIO = config['TWILIO']['ACCOUNT_ID']
API_KEY_TWILIO = config['TWILIO']['API_KEY']
PHONE_NUMBER_TWILIO = config['TWILIO']['PHONE_NUMBER']

client = Client(ACCOUNT_ID_TWILIO, API_KEY_TWILIO)

def lambda_handler(event, context):
    
    status = run(CHROMIUM_LOCATION, CHROMEDRIVER_LOCATION)
    
    return {
        'statusCode': 200,
        'body': status
    }
    
def run(chromium_location, chromedriver_location):
    try:
        driver = create_web_driver(chromium_location, chromedriver_location)
        driver.get(BASE_URL)
        sleep(2)
        driver = page_1(driver)
        sleep(2)
        driver = page_2(driver)
        sleep(2)
        driver = page_3(driver)
        sleep(2)
        driver = page_4(driver)
        driver.quit()
        return True
    except Exception as error:
        send_text(PHONE, PHONE_NUMBER_TWILIO, f"Booking Failed: {error}")
        driver.quit()
        return False

def send_text(to, from_, message):
    client.api.account.messages.create(
        to=to,
        from_=from_,
        body=message
    )
    
def create_web_driver(chrome_path, driver_path):
    options = webdriver.ChromeOptions()
    
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280x1696")
    options.add_argument("--disable-application-cache")
    options.add_argument("--disable-infobars")
    options.add_argument("--no-sandbox")
    options.add_argument("--hide-scrollbars")
    options.add_argument("--enable-logging")
    options.add_argument("--log-level=0")
    options.add_argument("--single-process")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--homedir=/tmp")

    options.binary_location = chrome_path

    return webdriver.Chrome(driver_path, chrome_options=options)


def page_1(driver):
    
    #Add participant
    driver.find_element_by_xpath("//a[text()='+']").click()

    # Booking within the same month
    if BOOKING_DATE.month == CURRENT_TIME.month:
        pass
    # Booking in the next month
    elif BOOKING_DATE.month == (CURRENT_TIME + relativedelta(months=1)).month:
        driver.find_element_by_xpath("//a[@title='Next']").click()
    else:
        # Something has gone horribly wrong if we reach here
        raise Exception("Error in selecting booking date")

    driver.find_element_by_xpath(f'//a[@class="ui-state-default" and text()="{BOOKING_DATE.day}"]').click()
    
    sleep(2)
    
    try:
        driver.find_element_by_xpath(
            f'//td[contains(text(), "{FROM}") and contains(text(), "{TO}")]/parent::tr/td/a[@class="book-now-button"]').click()
    except:
        raise Exception("No appointments available at given date/time")

    return driver



def page_2(driver):
    driver.find_element_by_xpath('//input[@id="pfirstname-pindex-1-1"]').send_keys(FIRST_NAME)
    driver.find_element_by_xpath('//input[@id="plastname-pindex-1-1"]').send_keys(LAST_NAME)
    
    driver.find_element_by_xpath(f'//select[@id="participant-birth-pindex-1month"]/option[@value="{BIRTH_MONTH}"]').click()
    driver.find_element_by_xpath(f'//select[@id="participant-birth-pindex-1day"]/option[@value="{BIRTH_DAY}"]').click()
    driver.find_element_by_xpath(f'//select[@id="participant-birth-pindex-1year"]/option[@value="{BIRTH_YEAR}"]').click()

    driver.find_element_by_xpath('//select[contains(@name, "booking")]/option[@value="1"]').click()

    driver.find_element_by_xpath('//a[contains(@class, "navforward")]').click()
    
    return driver
    

def page_3(driver):
    driver.find_element_by_xpath("//input[@id='customer-firstname']").send_keys(FIRST_NAME)
    driver.find_element_by_xpath("//input[@id='customer-lastname']").send_keys(LAST_NAME)
    driver.find_element_by_xpath("//input[@id='customer-email']").send_keys(EMAIL)
    driver.find_element_by_xpath("//input[@id='customer-phone']").send_keys(PHONE)
    driver.find_element_by_xpath(f'//select[@id="customer-birth-month"]/option[@value="{BIRTH_MONTH}"]').click()
    driver.find_element_by_xpath(f'//select[@id="customer-birth-day"]/option[@value="{BIRTH_DAY}"]').click()
    driver.find_element_by_xpath(f'//select[@id="customer-birth-year"]/option[@value="{BIRTH_YEAR}"]').click()

    driver.find_element_by_xpath("//input[@id='customer-address-line1']").send_keys(ADDRESS)
    driver.find_element_by_xpath("//input[@id='customer-city']").send_keys(CITY)
    driver.find_element_by_xpath("//input[@id='customer-state']").send_keys(STATE)
    driver.find_element_by_xpath("//input[@id='customer-zip']").send_keys(ZIP)

    driver.find_element_by_xpath("//input[@data-required-checkbox='1']").click()
    
    #Solving the Captcha
    k = driver.find_element_by_xpath("//div[@class='g-recaptcha']").get_attribute('data-sitekey')
    url = 'https://app.rockgympro.com/b/widget/?a=booking_step2'
    r = requests.get(f'https://2captcha.com/in.php?key={API_KEY_2CAPTCHA}&method=userrecaptcha&googlekey={k}&pageurl={url}')
    
    status, id_ = r.text.split('|')
    
    token, i = None, 0
    if status.strip() == 'OK':
        while not token:
            resp = requests.get(f'https://2captcha.com/res.php?key={API_KEY_2CAPTCHA}&action=get&id={id_}')
            if resp.text[:2].upper() == 'OK':
                token = resp.text.split('|')[1]
            elif resp.text.strip() != "CAPCHA_NOT_READY":
                raise Exception("Captcha Status not in (CAPTCHA_NOT_READY, OK)")

            i += 1
            sleep(1)
            print(i, resp.status_code, resp.text)
    else:
        raise Exception("Captcha Error")

    driver.execute_script('''
    document.getElementById("g-recaptcha-response").innerHTML="{token}";
    document.getElementById("g-recaptcha-response").style.display="block";
    '''.format(token=token))

    driver.find_element_by_xpath("//a[@id='confirm_booking_button']").click()

    return driver
    
def page_4(driver):
    sleep(2)
    if driver.find_element_by_xpath("//div[@id='iframe-or-mobile-modes-page-container-minimal']/h1").text.strip() == "Your booking is complete!":
        send_text(PHONE, PHONE_NUMBER_TWILIO, f"Booking Created for {str(BOOKING_DATE)}")
        return driver
    else:
        raise Exception("Booking Failed")
