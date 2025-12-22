#!/usr/bin/env python3

import os
import struct
import time

TARGET_EXPIRY = 0xFFFFFFFF
NEW_LICENSE   = b"free"
MIN_HEADER_LENGTHS = [0, 4, 4, 4, 16, 16, 4, 5, 4]

# ============================================================
# Low-level helpers (crypto)
# ============================================================

def rolling_xor_decrypt(ciphertext, key_table):
    """Decrypt payload using WildTangent rolling XOR."""
    plaintext = bytearray(len(ciphertext))
    last_byte = 0

    for i, c in enumerate(ciphertext):
        plaintext[i] = c ^ last_byte ^ key_table[i % len(key_table)]
        last_byte = c

    return bytes(plaintext)


def rolling_xor_encrypt(plaintext, key_table):
    """Encrypt payload using WildTangent rolling XOR."""
    ciphertext = bytearray(len(plaintext))
    last_byte = 0

    for i, p in enumerate(plaintext):
        c = p ^ last_byte ^ key_table[i % len(key_table)]
        ciphertext[i] = c
        last_byte = c

    return bytes(ciphertext)

# ============================================================
# Key table generation
# ============================================================

def build_model_key_table(headers):
    """Key table for .wt (MODEL) files."""
    max_len = max(len(h) for h in headers)

    seed = 0
    for h in headers:
        for i in range(max_len):
            seed ^= h[i % len(h)]

    table = [seed & 0xFF] * max_len

    for i in range(max_len):
        for h in headers:
            table[i] ^= h[i % len(h)]
        table[i] &= 0xFF

    return bytes(table)


def build_media_key_table(headers):
    """Key table for .wjp (MEDIA) files."""
    max_len = max(len(h) for h in headers)

    seed = 0
    for index, h in enumerate(headers):
        for j in range(max_len):
            seed ^= index + j + h[j % len(h)] * (j + 1)

    table = [seed & 0xFF] * max_len

    for i in range(max_len):
        for j, h in enumerate(headers):
            table[i] ^= h[(j + i) % len(h)]
        table[i] &= 0xFF

    return bytes(table)

# ============================================================
# File parsing
# ============================================================

def parse_wld3_file(data):
    """
    Split a WLD3 file into:
      - prefix (everything up to .START)
      - header list
      - encrypted payload
    """
    start = data.index(b".START\n")
    prefix = data[:start + 7]
    pos = start + 7

    header_count = data[pos] - 0xC5
    pos += 1

    header_lengths = []
    decode_key = 0x39

    for i in range(header_count):
        length = (data[pos] - decode_key) & 0xFF
        pos += 1

        if length < MIN_HEADER_LENGTHS[i]:
            raise ValueError("Invalid header length")

        header_lengths.append(length)
        decode_key = (decode_key + 13) & 0xFF

    headers = []
    for length in header_lengths:
        headers.append(bytearray(data[pos:pos + length]))
        pos += length

    payload = data[pos:]
    return prefix, headers, payload


def read_expiry_from_file(path):
    """Read expiry timestamp from a WLD3 file."""
    with open(path, "rb") as f:
        data = f.read()

    if not data.startswith(b"WLD3"):
        return None

    _, headers, _ = parse_wld3_file(data)
    return struct.unpack("<I", headers[3][:4])[0]

# ============================================================
# Scanning
# ============================================================

def scan_files():
    """Scan directory and print expiry information."""
    results = []

    for name in os.listdir("."):
        if not name.lower().endswith((".wjp", ".wt")):
            continue
        if not os.path.isfile(name):
            continue

        try:
            ts = read_expiry_from_file(name)
            if ts is None:
                continue

            if ts == 0:
                year = 0
                date_str = "NONE"
            else:
                t = time.gmtime(ts)
                year = t.tm_year
                date_str = time.strftime("%Y-%m-%d %H:%M:%S UTC", t)

            results.append((year, ts, date_str, name))
        except Exception:
            pass

    results.sort(key=lambda r: r[0], reverse=True)

    print(f"{'YEAR':<6} {'TIMESTAMP':<12} {'DATE (UTC)':<20} FILE")
    print("-" * 72)

    for year, ts, date_str, name in results:
        y = "NONE" if year == 0 else str(year)
        print(f"{y:<6} {ts:<12} {date_str:<20} {name}")

    return [r[3] for r in results]

# ============================================================
# Patching
# ============================================================

def patch_file_in_place(path):
    """Patch a single WJP or WT file."""
    with open(path, "rb") as f:
        data = f.read()

    prefix, headers, enc_payload = parse_wld3_file(data)

    is_model = path.lower().endswith(".wt")
    key_table_old = (
        build_model_key_table(headers)
        if is_model else
        build_media_key_table(headers)
    )

    plaintext = rolling_xor_decrypt(enc_payload, key_table_old)

    # Modify headers
    headers[3][:4] = struct.pack("<I", TARGET_EXPIRY)
    headers[6][:4] = NEW_LICENSE

    key_table_new = (
        build_model_key_table(headers)
        if is_model else
        build_media_key_table(headers)
    )

    new_payload = rolling_xor_encrypt(plaintext, key_table_new)

    # Rebuild file
    out = bytearray(prefix)
    out.append(len(headers) + 0xC5)

    encode_key = 0x39
    for h in headers:
        out.append((len(h) + encode_key) & 0xFF)
        encode_key = (encode_key + 13) & 0xFF

    for h in headers:
        out += h

    out += new_payload

    with open(path, "wb") as f:
        f.write(out)

# ============================================================
# Main program flow
# ============================================================

def main():
    print("\n=== BEFORE PATCH ===\n")
    files = scan_files()

    if not files:
        print("\nNo files found.")
        return

    answer = input("\nPatch ALL listed files? [Y/N]: ").strip().lower()
    if answer != "y":
        print("Aborted.")
        return

    print("\nPatching files...\n")
    for f in files:
        try:
            patch_file_in_place(f)
            print(f"[OK] {f}")
        except Exception as e:
            print(f"[ERR] {f}: {e}")

    print("\n=== AFTER PATCH ===\n")
    scan_files()

if __name__ == "__main__":
    main()
