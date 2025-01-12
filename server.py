import os
import traceback
from flask import Flask
from web3 import Web3
import threading
import time
from eth_utils import keccak

app = Flask(__name__)

# DigitalOcean App Platform requires a default route for health checks
@app.route('/')
def index():
    return "Worker is running", 200

# Environment Variables
NETWORK_NAME = os.environ.get("networkName", "Unknown Network")
CHAIN_ID = os.environ.get("chainID", "Unknown Chain ID")
SYMBOL = os.environ.get("symbol", "Unknown Symbol")
RPC = os.environ.get("rpc", "http://127.0.0.1:8545")

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

def listen_to_events():
    print("Starting event listener...")
    latest_block = web3.eth.block_number

    # Calculate the event signature for ColorChanged
    event_signature = "ColorChanged(uint256,uint8,uint8,uint8)"
    event_topic = "0x" + keccak(text=event_signature).hex()

    print(f"Using event topic for ColorChanged: {event_topic}")

    while True:
        try:
            print(f"Fetching logs from block {latest_block} to latest...")
            logs = web3.eth.get_logs({
                "fromBlock": latest_block,
                "toBlock": "latest",
                "address": CONTRACT_ADDRESS,
                "topics": [event_topic]
            })

            if logs:
                print(f"Found {len(logs)} logs.")
            else:
                print("No new logs found.")

            for log in logs:
                try:
                    event = contract.events.ColorChanged().process_log(log)
                    token_id = event.args.tokenId
                    r = event.args.r
                    g = event.args.g
                    b = event.args.b

                    print(f"ColorChanged Event - Token ID: {token_id}, RGB: ({r}, {g}, {b})")

                    # Example: Trigger webhook or database update
                    # send_webhook(token_id, r, g, b)
                except Exception as e:
                    print(f"Error processing log: {e}")
                    traceback.print_exc()

            # Update the latest block to avoid processing logs again
            latest_block = web3.eth.block_number + 1

        except Exception as e:
            print(f"Error fetching logs: {e}")
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
