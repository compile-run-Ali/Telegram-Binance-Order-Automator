from telethon import TelegramClient, events
import logging
import threading
from configparser import ConfigParser
import createTestOrder
import asyncio
from data import Data
from utils import setup_logger
import price_socket
logger = setup_logger("telegram-listener")



# Setting configation values
# Replace 'YOUR_API_KEY' and 'YOUR_API_SECRET' with your actual Binance API credentials
config = ConfigParser()
config.read('default_config.ini')

api_key = config.get('Telegram','API_ID')
api_secret = config.get('Telegram','API_HASH')
username = config.get('Telegram','USERNAME')
user_input_channel = int(config.get('Telegram','TARGET_GROUP'))
excluded_symbols = config.get('Binance','EXCLUDED_SYMBOLS').strip('][').split(',')

WORDS_DICT = {
    'buy': [['buy', 'setup'], ['long', 'setup'], ['buy', 'high', 'sell', 'higher']],
    'sell': [['sell', 'short'], ['sell', 'setup'], ['short', 'setup'], ['sell', 'low', 'buy', 'lower']]
}


print(excluded_symbols)

client = TelegramClient(username, api_key, api_secret)

def sell(symbol):
    obj = createTestOrder.Binance(symbol)
    obj.sell()

async def buy(symbol):
    obj = createTestOrder.Binance(symbol)
    await obj.buy()


def buy_callback(symbol):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(buy(symbol))
    loop.close()

@client.on(events.NewMessage(chats=user_input_channel))
async def newMessageListener(event):
    try:
        newMessage = event.message.message
        newMessage = newMessage.lower()
        symbol = newMessage.split("#")[1].split(" ")[0].upper()
    except Exception as e:
        print(e)
        return

    if symbol in Data.data:
        logger.info(f'Already recieved message for {symbol}')
        return

    logger.info(f'Recieved new message : {newMessage}')

    if symbol in excluded_symbols:
        logger.info(f'Symbol {symbol} is excluded')
        return

    # checking for targeted keywords in message
        # logic for selling    
    if ('buy' in newMessage and 'setup' in newMessage) or ('long' in newMessage and 'setup' in newMessage):
        s_thread = threading.Thread(target=buy_callback, args=(symbol,))
        s_thread.daemon = True
        s_thread.start()
        
        # logic for buying
    elif ('sell' in newMessage and 'setup' in newMessage) or ('short' in newMessage and 'setup' in newMessage):
        s_thread = threading.Thread(target=sell, args=(symbol,))
        s_thread.daemon = True
        s_thread.start()
    
    # un comment this line to save messages in telegram :
    # await client.forward_messages(entity='me',messages=event.message) 

with client:
    client.run_until_disconnected()


