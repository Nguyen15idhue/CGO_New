import sys
import os
import hashlib
import json


# Admin KeyGen - Console only
def generate_key(password):
    return f"CHC-{password[:4]}-{password[4:8]}-{password[8:12]}"


print("=" * 50)
print("ADMIN - GENERATE ACTIVATION KEY")
print("=" * 50)
print("\nEnter customer code: ", end="")

try:
    code = input().strip().upper()
except:
    sys.exit(1)

if len(code) < 12:
    print("\nError: Code too short!")
    sys.exit(1)

key = generate_key(code)

print(f"\nActivation Key: {key}")
print("\nSend this key to customer.")
print("\nPress Enter to exit...")
input()
