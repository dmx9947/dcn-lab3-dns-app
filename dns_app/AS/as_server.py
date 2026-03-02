import socket
import os

HOST = "0.0.0.0"
PORT = 53533
DB_FILE = "records.txt"  # persistent storage

def parse_kv_line(line: str) -> dict:
    parts = line.strip().split()
    kv = {}
    for p in parts:
        if "=" in p:
            k, v = p.split("=", 1)
            kv[k.strip().upper()] = v.strip()
    return kv

def load_records() -> dict:
    records = {}
    if not os.path.exists(DB_FILE):
        return records
    with open(DB_FILE, "r", encoding="utf-8") as f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            kv = parse_kv_line(raw)
            name = kv.get("NAME")
            value = kv.get("VALUE")
            ttl = kv.get("TTL", "10")
            if name and value:
                records[(name, "A")] = (value, ttl)
    return records

def save_record(name: str, value: str, ttl: str):
    with open(DB_FILE, "a", encoding="utf-8") as f:
        f.write(f"NAME={name} VALUE={value} TTL={ttl}\n")

def handle_message(msg: str, records: dict) -> str:
    lines = [ln.strip() for ln in msg.splitlines() if ln.strip()]
    if len(lines) < 2:
        return "ERROR\n"

    kv1 = parse_kv_line(lines[0])
    kv2 = parse_kv_line(lines[1])

    rtype = kv1.get("TYPE", "").upper()
    name = kv2.get("NAME")

    if not rtype or not name:
        return "ERROR\n"

    # Registration if VALUE exists
    if "VALUE" in kv2:
        value = kv2.get("VALUE")
        ttl = kv2.get("TTL", "10")
        records[(name, rtype)] = (value, ttl)
        save_record(name, value, ttl)
        return "OK\n"

    # Query
    key = (name, rtype)
    if key not in records:
        return "NOTFOUND\n"
    value, ttl = records[key]
    return f"TYPE={rtype}\nNAME={name} VALUE={value} TTL={ttl}\n"

def main():
    records = load_records()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((HOST, PORT))
    print(f"[AS] UDP server listening on {HOST}:{PORT}")

    while True:
        data, addr = sock.recvfrom(4096)
        msg = data.decode("utf-8", errors="ignore")
        resp = handle_message(msg, records)
        sock.sendto(resp.encode("utf-8"), addr)

if __name__ == "__main__":
    main()