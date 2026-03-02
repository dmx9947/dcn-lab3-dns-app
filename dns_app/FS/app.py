from flask import Flask, request, jsonify, Response
import socket

app = Flask(__name__)

def fibonacci(n: int) -> int:
    if n < 0:
        raise ValueError("number must be non-negative")
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a

def udp_send(host: str, port: int, message: str, timeout_s: float = 2.0) -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout_s)
    sock.sendto(message.encode("utf-8"), (host, port))
    data, _ = sock.recvfrom(4096)
    return data.decode("utf-8", errors="ignore")

@app.put("/register")
def register():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "invalid JSON"}), 400

    hostname = data.get("hostname")
    ip = data.get("ip")
    as_ip = data.get("as_ip")
    as_port = data.get("as_port")

    if not all([hostname, ip, as_ip, as_port]):
        return jsonify({"error": "missing fields: hostname, ip, as_ip, as_port"}), 400

    try:
        as_port = int(as_port)
    except Exception:
        return jsonify({"error": "as_port must be an integer"}), 400

    msg = f"TYPE=A\nNAME={hostname} VALUE={ip} TTL=10\n"

    try:
        resp = udp_send(as_ip, as_port, msg)
        if not resp.strip().startswith("OK"):
            return jsonify({"error": f"AS registration failed: {resp.strip()}"}), 500
    except Exception as e:
        return jsonify({"error": f"AS not reachable: {str(e)}"}), 500

    return Response(status=201)

@app.get("/fibonacci")
def fib():
    num = request.args.get("number", None)
    if num is None:
        return jsonify({"error": "missing number"}), 400
    try:
        n = int(num)
    except Exception:
        return jsonify({"error": "number must be an integer"}), 400
    if n < 0:
        return jsonify({"error": "number must be non-negative"}), 400

    return str(fibonacci(n)), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9090)