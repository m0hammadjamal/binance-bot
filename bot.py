import os
import ccxt
import time
from dotenv import load_dotenv
import logging
from datetime import datetime, timedelta

# Load API keys from key.env file
load_dotenv(dotenv_path='.env')

api_key = os.getenv('BINANCE_API_KEY')
api_secret = os.getenv('BINANCE_API_SECRET')

if not api_key or not api_secret:
    raise ValueError("API key and secret must be set in the key.env file.")

# Binance API setup
binance = ccxt.binance({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'spot',
    },
})

# Set up logging with minimal logging to reduce delay
logging.basicConfig(level=logging.WARNING, filename='bot.log', filemode='w',
                    format='%(name)s - %(levelname)s - %(message)s')

TARGET_COIN = "HMSTRUSDT"  # Target coin
USDT_AMOUNT = 12           # How much USDT to spend
LISTING_TIME = "17:30"     # The exact listing time in 24-hour format
PRE_LISTING_BUFFER = 4      # Number of seconds to start early
MAX_RETRIES = 100            # Maximum number of retries

def get_adjusted_listing_time(target_time, buffer):
    # Convert target_time to datetime and subtract the buffer
    target_datetime = datetime.strptime(target_time, "%H:%M")
    adjusted_time = target_datetime - timedelta(seconds=buffer)
    return adjusted_time.strftime("%H:%M:%S")

def time_until_listing(target_time):
    current_time = time.strftime("%H:%M:%S")
    return current_time >= target_time

# Function to buy coin using USDT amount
def buy_coin():
    retries = 0
    while retries < MAX_RETRIES:
        try:
            ticker_info = binance.fetch_ticker(TARGET_COIN)  # Fetch price synchronously
            price = ticker_info['last']
            print(f"Price for {TARGET_COIN}: {price} USDT")

            quantity = USDT_AMOUNT / price  # Calculate quantity based on USDT_AMOUNT
            print(f"Buying {quantity:.6f} units of {TARGET_COIN} with {USDT_AMOUNT} USDT.")

            # Place the market order
            order = binance.create_market_buy_order(TARGET_COIN, quantity)
            print("Order successful:", order)

            logging.info(f"Order successful: {order}")
            break  # Exit loop if order is successful
        except Exception as e:
            retries += 1
            logging.error(f"Error during order placement: {e}. Retry {retries}/{MAX_RETRIES}.")
            print(f"Error during order placement: {e}. Retrying...")
            time.sleep(1)  # Wait a bit before retrying

# Main loop to place the order at the exact time
print("Waiting for coin listing...")
adjusted_listing_time = get_adjusted_listing_time(LISTING_TIME, PRE_LISTING_BUFFER)

while True:
    if time_until_listing(adjusted_listing_time):
        print(f"Target coin {TARGET_COIN} detected at {adjusted_listing_time}.")
        buy_coin()
        break  # Stop the bot after placing the order
