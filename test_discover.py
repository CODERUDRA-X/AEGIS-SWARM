import inspect
from caspian_sdk import CommClient

client = CommClient()
# Ye script client ke andar ke saare 'send' ya 'message' wale methods dhoondh legi
print("AVAILABLE METHODS:", [m for m in dir(client) if 'send' in m.lower() or 'message' in m.lower() or 'broadcast' in m.lower()])

print(inspect.signature(CommClient.send_message))