import asyncio
from socket import socket, AF_INET, AF_INET6, SOCK_DGRAM, SOCK_STREAM, MSG_DONTWAIT, MSG_PEEK
from typing import Union

from config import LARC_USE_IPV6, LARC_ADDRESS, LARC_TCP_PORT, LARC_UDP_PORT, LARC_ENCODING
from connection.larc_messages import LarcMessage, LarcProtocol
from exception.larc_exceptions import LarcInvalidCredentials


class LarcConnection:

    def __init__(self):
        self._tcp_lock = asyncio.Lock()
        self._udp_lock = asyncio.Lock()
        self._tcp_socket: socket = None
        self._udp_socket: socket = socket(family=AF_INET6 if LARC_USE_IPV6 else AF_INET, type=SOCK_DGRAM)

    async def send(self, message: LarcMessage) -> Union[bool, bytes]:
        if message.protocol == LarcProtocol.UDP:
            await self._send_udp(message)
            return True
        return await self._send_tcp(message)

    async def _send_udp(self, message: LarcMessage) -> None:
        with await self._udp_lock:
            self._udp_socket.sendto(message.for_socket, (LARC_ADDRESS, LARC_UDP_PORT))

    async def _send_tcp(self, message: LarcMessage) -> bytes:
        with await self._tcp_lock:
            self._ensure_open_tcp_connection()
            self._tcp_socket.sendall(message.for_socket)

            response = self._get_tcp_response()
            if response == 'Usuário inválido!'.encode(encoding=LARC_ENCODING):
                raise LarcInvalidCredentials(response.decode(encoding=LARC_ENCODING))
            return response

    def _ensure_open_tcp_connection(self) -> None:
        started = self._tcp_socket is not None
        if not started:
            self._tcp_socket = socket(family=AF_INET6 if LARC_USE_IPV6 else AF_INET, type=SOCK_STREAM)

        if not started or self._is_socket_closed():
            self._tcp_socket.connect((LARC_ADDRESS, LARC_TCP_PORT))

    def _is_socket_closed(self) -> bool:
        try:
            data = self._tcp_socket.recv(16, MSG_DONTWAIT | MSG_PEEK)
            if len(data) == 0:
                return True
        except BlockingIOError:
            return False
        except ConnectionResetError:
            return True
        except Exception as e:
            msg = str(e)
            return 'not connected' in msg
        return False

    def _get_tcp_response(self) -> bytes:
        buff: bytes = b''
        while not buff.endswith(b'\r\n'):
            buff += self._tcp_socket.recv(1)
        return buff[:-2]
