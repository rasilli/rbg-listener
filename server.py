import os
from flask import Flask
from web3 import Web3
import threading

app = Flask(__name__)

# DigitalOcean App Platform requires a default route for health checks
@app.route('/')
def index():
    return "Worker is running", 200

NETWORK_NAME = os.environ.get("networkName")
CHAIN_ID = os.environ.get("chainID")
SYMBOL = os.environ.get("symbol")
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

# Connect to Monad Devnet
web3 = Web3(Web3.HTTPProvider(RPC))
contract = web3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=CONTRACT_ABI)

def listen_to_events():
    # Event listener
    print("Listening for events...")
    event_filter = contract.events.ColorChanged.createFilter(fromBlock="latest")

    while True:
        for event in event_filter.get_new_entries():
            token_id = event.args.tokenId
            r = event.args.r
            g = event.args.g
            b = event.args.b

            print(f"ColorChanged: Token ID: {token_id}, RGB: ({r}, {g}, {b})")

            # Trigger webhook or update database if needed
            # Example: send_webhook(token_id, r, g, b)

        web3.middleware_onion.sleep(2)

# Background thread to listen for events
thread = threading.Thread(target=listen_to_events, daemon=True)
thread.start()

# Flask keeps the app running
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
