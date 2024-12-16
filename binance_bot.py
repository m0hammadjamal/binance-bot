import os
import ccxt
import asyncio
import websockets
from dotenv import load_dotenv
import json
import logging

# Load API keys from key.env file
load_dotenv(dotenv_path='key.env')

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

# Set up logging
logging.basicConfig(level=logging.INFO, filename='bot.log', filemode='w',
                    format='%(name)s - %(levelname)s - %(message)s')
logging.info("Bot started.")
print("Bot started...")

# Define the coin symbol you're interested in
TARGET_COIN = "HMSTRUSDT"  # Ensure no "/" for Binance symbols

# Define how much USDT you want to spend
USDT_AMOUNT = 12  # Replace with the USDT amount you want to spend

async def listen_new_listings():
    uri = "wss://stream.binance.com:9443/ws/!ticker@arr"
    print("Connecting to WebSocket...")
    while True:
        try:
            async with websockets.connect(uri) as websocket:
                print("Connected to WebSocket.")
                logging.info("Listening for new listings...")
                while True:
                    data = await websocket.recv()
                    print(f"Received WebSocket data: {data[:100]}...")
                    await process_new_listing(data)
        except Exception as e:
            logging.error(f"WebSocket connection error: {e}. Retrying...")
            print(f"WebSocket connection error: {e}. Retrying...")
            await asyncio.sleep(5)

async def process_new_listing(data):
    try:
        parsed_data = json.loads(data)
        if isinstance(parsed_data, list):
            for ticker in parsed_data:
                if 's' in ticker and ticker['s'] == TARGET_COIN:
                    logging.info(f"Target coin detected: {ticker['s']}")
                    print(f"Target coin detected: {ticker['s']}")
                    await buy_coin(ticker['s'])
    except Exception as e:
        logging.error(f"Error processing listing: {e}")
        print(f"Error processing listing: {e}")

async def buy_coin(symbol):
    try:
        logging.info(f"Fetching price for {symbol}...")
        ticker_info = binance.fetch_ticker(symbol)  # No 'await' here
        price = ticker_info['last']
        logging.info(f"Price for {symbol}: {price} USDT")
        print(f"Price for {symbol}: {price} USDT")

        # Calculate how many units to buy with the USDT amount
        quantity = USDT_AMOUNT / price
        logging.info(f"Calculated quantity: {quantity:.6f} units")
        print(f"Calculated quantity: {quantity:.6f} units")

        # Check minimum notional value (adjust based on the actual minimum for the pair)
        min_notional = 10  # Example minimum value, change as necessary
        order_value = quantity * price

        if order_value < min_notional:
            logging.error(f"Order value ({order_value:.2f} USDT) is less than minimum required ({min_notional} USDT).")
            print(f"Order value ({order_value:.2f} USDT) is less than minimum required ({min_notional} USDT).")
            return  # Exit if not meeting the minimum

        # Place a market order
        order = binance.create_market_buy_order(symbol, quantity)  # No 'await' here
        logging.info(f"Order successful: {order}")
        print("Buying success")

        # Exit the program after a successful order
        asyncio.get_event_loop().stop()
    except Exception as e:
        logging.error(f"Error during order placement: {e}")
        print(f"Error during order placement: {e}")

# Run the WebSocket listener
asyncio.run(listen_new_listings())
