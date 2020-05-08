"""
Серверное приложение для соединений
"""
import asyncio
from asyncio import transports


class ClientProtocol(asyncio.Protocol):
    login: str
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server
        self.login = None

    _login_prefix = "login:"

    def data_received(self, data: bytes):
        decoded = data.decode()
        print(decoded)

        if self.login is None:
            # assuming 'login:User'

            if not decoded.startswith(self._login_prefix):
                self.print_back(
                    f"Сперва нужно ввести имя пользователя в формате (без кавычек):\n"
                    f"{self._login_prefix}'имя пользователя'"
                )
                return

            login = decoded.replace(self._login_prefix, "").strip()  # strip() is cleaner then manual \r\n replacement

            if not login:
                self.print_back("Необходимо ввести имя пользователя")
                return

            if any(login == c.login for c in self.server.clients):
                self.print_back(f"Логин {login} занят, попробуйте другой")
                self.connection_lost(None)
                return

            self.login = login
            self.print_back(f"Привет, {self.login}!")
        else:
            self.send_message(decoded)

    def print_back(self, message: str):
        """Print a message in the client"""
        self.transport.write(message.encode())

    def send_message(self, message: str):
        format_string = f"<{self.login}> {message}"

        for client in self.server.clients:
            if client.login != self.login:
                client.print_back(format_string)

    def connection_made(self, transport: transports.Transport):
        self.transport = transport
        self.server.clients.append(self)
        print("Соединение установлено")

    def connection_lost(self, exception):
        try:
            self.server.clients.remove(self)
        except ValueError:
            pass
        print("Соединение разорвано")


class Server:
    clients: list

    def __init__(self):
        self.clients = []

    def create_protocol(self):
        return ClientProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.create_protocol,
            "127.0.0.1",
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()
try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
