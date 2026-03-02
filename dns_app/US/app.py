from flask import Flask, request, jsonify
import socket
import requests

app = Flask(__name__)

def udp_query(as_ip: str, as_port: int, hostname: str, timeout_s: float = 2.0) -> str:
    msg = f"TYPE=A\nNAME={hostname}\n"
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout_s)
    sock.sendto(msg.encode("utf-8"), (as_ip, as_port))
    data, _ = sock.recvfrom(4096)
    return data.decode("utf-8", errors="ignore")

def parse_value(resp: str) -> str | None:
    # Expected:
    # TYPE=A
    # NAME=fibonacci.com VALUE=127.0.0.1 TTL=10
    lines = [ln.strip() for ln in resp.splitlines() if ln.strip()]
    if len(lines) < 2:
        return None
    parts = lines[1].split()
    for p in parts:
        if p.startswith("VALUE="):
            return p.split("=", 1)[1]
    return None

@app.get("/fibonacci")
def fib():
    hostname = request.args.get("hostname")
    fs_port = request.args.get("fs_port")
    number = request.args.get("number")
    as_ip = request.args.get("as_ip")
    as_port = request.args.get("as_port")

    if not all([hostname, fs_port, number, as_ip, as_port]):
        return jsonify({"error": "missing query params: hostname, fs_port, number, as_ip, as_port"}), 400

    try:
        fs_port = int(fs_port)
        as_port = int(as_port)
        n = int(number)
    except Exception:
        return jsonify({"error": "fs_port, as_port, and number must be integers"}), 400

    # 1) Query AS via UDP
    try:
        resp = udp_query(as_ip, as_port, hostname)
        fs_ip = parse_value(resp)
        if not fs_ip:
            return jsonify({"error": f"hostname not found in AS: {resp.strip()}"}), 404
    except Exception as e:
        return jsonify({"error": f"AS query failed: {str(e)}"}), 500

    # 2) Query FS via HTTP
    try:
        url = f"http://{fs_ip}:{fs_port}/fibonacci"
        r = requests.get(url, params={"number": n}, timeout=2.0)
        return (r.text, r.status_code, {"Content-Type": "text/plain"})
    except Exception as e:
        return jsonify({"error": f"FS request failed: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)