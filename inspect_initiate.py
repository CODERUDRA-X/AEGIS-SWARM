"""
AEGIS-SWARM :: initiate() Signature Discovery
=================================================
Checks whether Caspian's initiate() method accepts html/subject
parameters, so we know if rich HTML email formatting is possible
without guessing.
"""

import inspect
from caspian_sdk import CommClient

client = CommClient()

print("=" * 60)
print("REAL SIGNATURE of initiate():")
print("=" * 60)
print(inspect.signature(client.initiate))

print()
print("DOCSTRING:")
print(client.initiate.__doc__)