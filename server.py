import os
import traceback
from flask import Flask
from web3 import Web3
import threading
import time

app = Flask(__name__)

# DigitalOcean App Platform requires a default route for health checks
@app.route('/')
def index():
    return "Worker is running", 200

# Environment Variables
NETWORK_NAME = os.environ.get("networkName", "Unknown Network")
CHAIN_ID = os.environ.get("chainID", "Unknown Chain ID")
SYMBOL = os.environ.get("symbol", "Unknown Symbol")
RPC = os.environ.get("rpc")

CONTRACT_ADDRESS = "0x64376a051E77b7D7181C3DfBb49c3c83e127704b"
CONTRACT_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "uint256", "name": "tokenId", "type": "uint256"},
            {"indexed": False, "internalType": "uint8", "name": "r", "type": "uint8"},
            {"indexed": False, "internalType": "uint8", "name": "g", "type": "uint8"},
            {"indexed": False, "internalType": "uint8", "name": "b", "type": "uint8"}
        ],
        "name": "ColorChanged",
        "type": "event"
    }
]

# Connect to RPC
try:
    web3 = Web3(Web3.HTTPProvider(RPC))
    if not web3.is_connected():
        raise ConnectionError(f"Failed to connect to RPC endpoint: {RPC}")
    print(f"Connected to network: {NETWORK_NAME} (Chain ID: {CHAIN_ID}, Symbol: {SYMBOL})")
except Exception as e:
    print(f"Error connecting to RPC endpoint: {e}")
    traceback.print_exc()
    raise

# Load Contract
try:
    contract = web3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=CONTRACT_ABI)
    print(f"Contract loaded: {CONTRACT_ADDRESS}")
except Exception as e:
    print(f"Error loading contract: {e}")
    traceback.print_exc()
    raise

# Event Listener Function
def listen_to_events():
    print("Starting event listener...")

    try:
        event_filter = contract.events.ColorChanged.create_filter(fromBlock="latest")
        print("Event filter created successfully.")
    except Exception as e:
        print(f"Error creating event filter: {e}")
        traceback.print_exc()
        return

    while True:
        try:
            print("Checking for new events...")
            events = event_filter.get_new_entries()
            print(f"Found {len(events)} new events.")
            for event in events:
                try:
                    token_id = event.args.tokenId
                    r = event.args.r
                    g = event.args.g
                    b = event.args.b
                    print(f"ColorChanged Event - Token ID: {token_id}, RGB: ({r}, {g}, {b})")

                    # Example: Trigger webhook or database update
                    # send_webhook(token_id, r, g, b)
                except Exception as e:
                    print(f"Error processing event: {e}")
                    traceback.print_exc()

        except Exception as e:
            print(f"Error fetching events: {e}")
            traceback.print_exc()

        time.sleep(2)  # Prevent tight polling

# Start Event Listener in Background Thread
try:
    thread = threading.Thread(target=listen_to_events, daemon=True)
    thread.start()
    print("Background thread started for event listening.")
except Exception as e:
    print(f"Error starting background thread: {e}")
    traceback.print_exc()
    raise

# Flask App to Keep the Service Running
if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=8080)
    except Exception as e:
        print(f"Error starting Flask app: {e}")
        traceback.print_exc()
