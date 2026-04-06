"""Minimal LAN networking plus room discovery."""

from __future__ import annotations

import json
import random
import socket
import string
import time
from typing import Any

import settings

DISCOVERY_PORT = settings.NETWORK_PORT + 1


def local_ip_address() -> str:
    """Best-effort local IP detection for host instructions."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        sock.close()


def generate_room_code() -> str:
    """Create a short friendly room code."""
    alphabet = string.ascii_uppercase + string.digits
    return "".join(random.choice(alphabet) for _ in range(6))


class _BaseSession:
    def __init__(self) -> None:
        self.socket: socket.socket | None = None
        self.buffer = ""
        self.connected = False
        self.error_message = ""

    def _send_json(self, payload: dict[str, Any]) -> None:
        if self.socket is None:
            return
        try:
            message = json.dumps(payload, separators=(",", ":")) + "\n"
            self.socket.sendall(message.encode("utf-8"))
        except OSError as exc:
            self.error_message = str(exc)
            self.connected = False

    def _receive_messages(self) -> list[dict[str, Any]]:
        if self.socket is None:
            return []
        messages: list[dict[str, Any]] = []
        try:
            while True:
                chunk = self.socket.recv(4096)
                if not chunk:
                    self.connected = False
                    break
                self.buffer += chunk.decode("utf-8")
                while "\n" in self.buffer:
                    raw, self.buffer = self.buffer.split("\n", 1)
                    if raw.strip():
                        messages.append(json.loads(raw))
        except BlockingIOError:
            pass
        except (OSError, json.JSONDecodeError) as exc:
            self.error_message = str(exc)
            self.connected = False
        return messages

    def close(self) -> None:
        if self.socket is not None:
            try:
                self.socket.close()
            except OSError:
                pass
        self.socket = None
        self.connected = False


class DiscoveryBroadcaster:
    """Broadcasts room presence on the local network."""

    def __init__(self, room_code: str, host_ip: str, room_name: str) -> None:
        self.room_code = room_code
        self.host_ip = host_ip
        self.room_name = room_name
        self.live_status: dict[str, Any] = {
            "players": 1,
            "host_score": 0,
            "remote_score": 0,
            "mode_id": "lan_duel",
        }
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.socket.setblocking(False)
        self.last_send_at = 0.0

    def tick(self) -> None:
        now = time.time()
        if now - self.last_send_at < 1.0:
            return
        self.last_send_at = now
        payload = {
            "type": "room_beacon",
            "room_code": self.room_code,
            "host_ip": self.host_ip,
            "port": settings.NETWORK_PORT,
            "room_name": self.room_name,
            "live_status": self.live_status,
            "timestamp": now,
        }
        try:
            self.socket.sendto(
                json.dumps(payload, separators=(",", ":")).encode("utf-8"),
                ("255.255.255.255", DISCOVERY_PORT),
            )
        except OSError:
            pass

    def close(self) -> None:
        try:
            self.socket.close()
        except OSError:
            pass

    def update_status(self, **kwargs: Any) -> None:
        """Refresh beacon metadata for room browsers and HUD previews."""

        self.live_status.update(kwargs)


class DiscoveryBrowser:
    """Listens for LAN room beacons and keeps a short recent list."""

    def __init__(self) -> None:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(("", DISCOVERY_PORT))
        self.socket.setblocking(False)
        self.rooms: dict[str, dict[str, Any]] = {}

    def poll(self) -> list[dict[str, Any]]:
        now = time.time()
        try:
            while True:
                data, address = self.socket.recvfrom(4096)
                payload = json.loads(data.decode("utf-8"))
                if payload.get("type") != "room_beacon":
                    continue
                room_code = payload.get("room_code", "------")
                host_ip = payload.get("host_ip") or address[0]
                self.rooms[room_code] = {
                    "room_code": room_code,
                    "host_ip": host_ip,
                    "port": int(payload.get("port", settings.NETWORK_PORT)),
                    "room_name": payload.get("room_name", "Snake Legends"),
                    "live_status": payload.get("live_status", {}),
                    "seen_at": now,
                }
        except BlockingIOError:
            pass
        except (OSError, json.JSONDecodeError):
            pass

        self.rooms = {
            code: room
            for code, room in self.rooms.items()
            if now - room["seen_at"] <= 4.0
        }
        return sorted(self.rooms.values(), key=lambda room: room["room_code"])

    def close(self) -> None:
        try:
            self.socket.close()
        except OSError:
            pass


class HostSession(_BaseSession):
    """Authoritative host for a LAN duel."""

    def __init__(self, host_ip: str) -> None:
        super().__init__()
        self.room_code = generate_room_code()
        self.room_name = "Snake Legends LAN"
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(("", settings.NETWORK_PORT))
        self.server_socket.listen(1)
        self.server_socket.setblocking(False)
        self.broadcaster = DiscoveryBroadcaster(self.room_code, host_ip, self.room_name)
        self.live_status: dict[str, Any] = {
            "players": 1,
            "host_score": 0,
            "remote_score": 0,
            "mode_id": "lan_duel",
            "winner": "",
        }

    def poll(self) -> list[dict[str, Any]]:
        self.broadcaster.tick()
        if not self.connected:
            try:
                client, _ = self.server_socket.accept()
                client.setblocking(False)
                self.socket = client
                self.connected = True
                self.update_live_status(players=2)
                self._send_json({"type": "welcome", "role": "remote"})
            except BlockingIOError:
                return []
            except OSError as exc:
                self.error_message = str(exc)
                return []
        return self._receive_messages()

    def send_snapshot(self, snapshot: dict[str, Any]) -> None:
        self._send_json({"type": "snapshot", "payload": snapshot})

    def update_live_status(self, **kwargs: Any) -> None:
        """Store live LAN-room stats and expose them to discovery beacons."""

        self.live_status.update(kwargs)
        self.broadcaster.update_status(**self.live_status)

    def close(self) -> None:
        super().close()
        self.broadcaster.close()
        try:
            self.server_socket.close()
        except OSError:
            pass


class ClientSession(_BaseSession):
    """Remote client that sends input and receives snapshots."""

    def __init__(self, host_ip: str) -> None:
        super().__init__()
        self.host_ip = host_ip
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(3)
        self.socket.connect((host_ip, settings.NETWORK_PORT))
        self.socket.setblocking(False)
        self.connected = True

    def poll(self) -> list[dict[str, Any]]:
        return self._receive_messages()

    def send_direction(self, direction: tuple[int, int]) -> None:
        self._send_json({"type": "input", "direction": list(direction)})
