"""
AEGIS-SWARM :: Caspian Outbound Dispatch — Isolation Test
============================================================
RUN THIS ALONE. Do NOT run caspian_handler.py at the same time as this
script's first run (Test 1) -- we want to see if send works using ONLY
the already-connected account channels, without a second connect_telegram
call fighting over the same bot token.

WHY THIS SCRIPT EXISTS:
server.py's dispatch code calls connect_telegram() and connect_email()
INSIDE the request handler, using the SAME bot token that
caspian_handler.py already connected and is actively listening on. Two
processes registering the same bot token is a likely source of silent
conflict. This script isolates the actual send capability from that
conflict so we can see the real error (if any) instead of a swallowed
exception.
"""

import os
from dotenv import load_dotenv
from caspian_sdk import CommClient

load_dotenv()

client = CommClient()

print("=" * 60)
print("STEP 1: Discover the real outbound-send method name")
print("=" * 60)
methods = sorted(m for m in dir(client) if not m.startswith("_"))
for m in methods:
    print(" -", m)

print()
print("=" * 60)
print("STEP 2: Attempt to send WITHOUT reconnecting channels")
print("=" * 60)
print("(No connect_telegram() / connect_email() call here on purpose --")
print(" testing whether the account-level connection from")
print(" caspian_handler.py is enough on its own.)")
print()

tg_chat_id = os.environ.get("DISPATCH_TELEGRAM_CHAT_ID")
admin_email = os.environ.get("DISPATCH_ADMIN_EMAIL")

# Try the guessed method name first, but show the FULL error if it fails
# -- not just str(e), so we can see exactly what's wrong.
try:
    result = client.send_message(conversation_id=tg_chat_id, text="AEGIS-SWARM isolation test — Telegram")
    print("Telegram send result:", result)
except Exception:
    import traceback
    print("Telegram send FAILED. Full traceback:")
    traceback.print_exc()

try:
    result = client.send_message(conversation_id=admin_email, text="AEGIS-SWARM isolation test — Email")
    print("Email send result:", result)
except Exception:
    import traceback
    print("Email send FAILED. Full traceback:")
    traceback.print_exc()