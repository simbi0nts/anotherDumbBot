# -*- coding: utf-8 -*-
import os

token = 'token:token'

dev_mode = str(os.getenv('DEV', False))
if dev_mode == '1' or dev_mode.lower() == 'true':
    dev_mode = True
else:
    dev_mode = False

CHROME_PATH = '/usr/bin/chromium-browser'
CHROMEDRIVER_PATH = '/usr/bin/chromedriver'
WINDOW_SIZE = "1920,1080"

db = 'db'
us = "us:us"

proxy = {
  'http': 'socks5://anonymous:anonymous@proxy:port',
  'https': 'socks5://anonymous:anonymous@proxy:port'
}

ocp_key = 'ocp_key'