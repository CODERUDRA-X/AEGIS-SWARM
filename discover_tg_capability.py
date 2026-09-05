"""
AEGIS-SWARM :: Telegram Capability Discovery
================================================
The 422 error confirms: the Telegram connection exists but lacks the
'initiate' capability that Email's connection has. This checks the
real signatures of the methods most likely able to fix that --
connect_telegram (does it even take a capabilities kwarg?), edit
(seen in the earlier full method listing -- likely for updating an
existing connection), and get_connection (to inspect what capabilities
the current Telegram connection actually has right now).
"""

import inspect
import os
from dotenv import load_dotenv
from caspian_sdk import CommClient

load_dotenv()
client = CommClient()

print("=" * 60)
print("1. connect_telegram() signature:")
print("=" * 60)
print(inspect.signature(client.connect_telegram))
print(client.connect_telegram.__doc__)

print()
print("=" * 60)
print("2. edit() signature:")
print("=" * 60)
print(inspect.signature(client.edit))
print(client.edit.__doc__)

print()
print("=" * 60)
print("3. get_connection() signature:")
print("=" * 60)
print(inspect.signature(client.get_connection))
print(client.get_connection.__doc__)

print()
print("=" * 60)
print("4. list_connections() -- find the actual Telegram connection_id")
print("=" * 60)
print(inspect.signature(client.list_connections))
try:
    connections = client.list_connections()
    print(connections)
except Exception as e:
    print(f"Call failed (signature only, not a blocker): {e}")