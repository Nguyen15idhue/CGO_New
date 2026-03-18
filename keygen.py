import sys
import re


# Admin License Tool - Console only
def normalize_code(raw):
    return raw.strip().upper().replace("-", "").replace(" ", "")


def generate_key(code):
    return f"CHC-{code[:4]}-{code[4:8]}-{code[8:12]}"


print("=" * 50)
print("ADMIN - LICENSE TOOL")
print("=" * 50)
print("\nEnter customer code (16 HEX chars): ", end="")

try:
    code = normalize_code(input())
except:
    sys.exit(1)

if not re.fullmatch(r"[0-9A-F]{16}", code):
    print("\nError: Invalid code format!")
    print("Expected: 16 hex characters from customer screen.")
    sys.exit(1)

key = generate_key(code)

print(f"\nActivation Key: {key}")
print("\nSend this key to customer.")
print("\nPress Enter to exit...")
input()
