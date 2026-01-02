import requests
import config

def buy_call():
    return requests.post(config.CALL_WEBHOOK).text
def buy_put():
    return requests.post(config.PUT_WEBHOOK).text
