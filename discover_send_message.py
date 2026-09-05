"""
AEGIS-SWARM :: send_message() Real Signature Discovery
==========================================================
Confirmed via list_connections(): the Telegram connection has 'send'
and 'reply' capabilities, NOT 'initiate' -- this is expected, since
Telegram bots cannot cold-start a conversation with a user (a real
platform restriction, not a Caspian limitation). Since the user has
an existing active chat with this bot, send_message() -- matching the
'send' capability -- is the correct method, not initiate().

We hit a TypeError on send_message(to=..., text=...) early in this
project and pivoted to Email's initiate() instead of finishing this
discovery. This closes that gap.
"""

import inspect
from caspian_sdk import CommClient

client = CommClient()

print("=" * 60)
print("send_message() real signature:")
print("=" * 60)
print(inspect.signature(client.send_message))
print()
print("DOCSTRING:")
print(client.send_message.__doc__)