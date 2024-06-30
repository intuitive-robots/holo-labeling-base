from time import strftime
import asyncio
import os
from fileio import FileSaver
import json
import abc
import threading
from websockets import server
import asyncio
from asyncio import sleep as async_sleep

class ServerBase(abc.ABC):
    """
    A abstract class for all server running on a simulation environment.

    The server receives and sends messages to client by websockets.

    Args:
        host (str): the ip address of service
        port (str): the port of service
    """    
    def __init__(
        self, 
        host: str, 
        port: str
    ) -> None:

        self._ws: server.WebSocketServerProtocol = None
        self._wsserver: server.WebSocketServer = None
        self._server_future: asyncio.Future = None
        self.host = host
        self.port = port
        
    def start_server_thread(self, block = False) -> None:
        """
        Start a thread for service.

        Args:
            block (bool, optional): main thread stop running and 
            wait for server thread. Defaults to False.
        """
        self.server_thread = threading.Thread(target=self._start_server_task)
        self.server_thread.daemon = True
        self.server_thread.start()
        if block:
            self.server_thread.join()

    @abc.abstractmethod
    async def process_message(self, msg:str):
        """
        Processing message when receives new messages from clients.

        Args:
            msg (str): message from client.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def create_handler(self, ws: server.WebSocketServerProtocol) -> list[asyncio.Task]:
        """
        Create new tasks such as receiving and stream when start service.

        Args:
            ws (server.WebSocketServerProtocol): WebSocketServerProtocol from websockets.

        Returns:
            list[asyncio.Task]: the list of new tasks
        """        
        raise NotImplementedError

    async def receive_handler(self, ws: server.WebSocketServerProtocol):
        """
        Default messages receiving task handler.

        Args:
        ws (server.WebSocketServerProtocol): WebSocketServerProtocol from websockets.
        """        
        async for msg in ws:
            await self.process_message(msg)

    async def handler(self, ws: server.WebSocketServerProtocol):
        """
        The main task handler of loop in server thread.

        Args:
            ws (server.WebSocketServerProtocol): WebSocketServerProtocol from websockets.
        """        
        await self.on_conncet(ws)
        _, pending = await asyncio.wait(
            self.create_handler(ws),
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()
        await ws.close()
        await self.on_close(ws)

    async def _expect_client(self):
        """
        The coroutine task for running service on loop.
        """        
        self.stop = asyncio.Future()
        async with server.serve(self.handler, self.host, self.port) as self._wsserver:
            await self.stop

    def _start_server_task(self) -> None:
        """
        The thread task for running a service loop.
        """        
        print(f"start a server on {self.host}:{self.port}")
        asyncio.run(self._expect_client())
        print("server task finished")

    async def _send_str_msg_on_loop(
        self, msg: str, 
        ws: server.WebSocketServerProtocol, 
        sleep_time: float = 0
    ):
        """
        Send a str message
         
        It can only be used in the server thread.

        Args:
            msg (str): message to be sent.
            ws (server.WebSocketServerProtocol): WebSocketServerProtocol from websockets.
            sleep_time (float, optional): sleep time after sending the message. Defaults to 0.
        """        
        await ws.send(str.encode(json.dumps(msg)))
        await async_sleep(sleep_time)
 
    def send_str_msg(self, msg: str, sleep_time: float = 0) -> None:
        """
        Send a str message outside the server thread.

        Args:
            msg (str): message to be sent.
            sleep_time (float, optional): sleep time after sending the message. Defaults to 0.
        """            
        if self._ws is None:
            return
        self.create_new_task(self._send_str_msg_on_loop(msg, self._ws, sleep_time))

    def create_new_task(self, task: asyncio.Task) -> None:
        """
        Create a new task on the service loop.

        Args:
            task (asyncio.Task): Task to be ruuning on the loop.
        """        
        loop = self._wsserver.get_loop()
        loop.create_task(task)

    def close_server(self) -> None:
        """
        Stop and close the server.
        """        
        self._wsserver.close()

    async def on_conncet(self, ws: server.WebSocketServerProtocol) -> None:
        """
        This method will be executed once the connection is established.

        Args:
            ws (server.WebSocketServerProtocol): WebSocketServerProtocol from websockets.
        """        
        print(f"connected by: {ws.local_address}")
        self._ws = ws

    async def on_close(self, ws: server.WebSocketServerProtocol) -> None:
        """
        This method will be executed when disconnected.

        Args:
            ws (server.WebSocketServerProtocol): WebSocketServerProtocol from websockets.
        """        
        self._ws = None
        print(f"the connection to {ws.local_address} is closed")


class LabelingServer(ServerBase):

    def __init__(self, file_saver=None, host="127.0.0.1", port=8053):
        self.file_saver = file_saver
        super().__init__(host=host, port=port)

    async def process_message(self, msg:str):
        content = msg.split(":::")

        header = content[0]
        msg = content[1]
        match header:
            case "DAT":
                msg = json.loads(msg)
                file_name = self._save_data(msg)
                print(f"Saved data to {file_name}")
            case _:
                print(msg)


    def create_handler(self, ws) -> list[asyncio.Task]:       
        return [asyncio.create_task(self.receive_handler(ws))]

    def _save_data(self, content : str) -> str: # writes data to file and saves meta data
        folder_name = strftime("%Y-%m-%d/");        
        
        self.file_saver.create_dir(folder_name) # Create the folder if non existent
        
        
        file_name = folder_name + strftime("%H%M%S")
        file_name = self.file_saver.save_file(file_name, content) 
        
        
        meta_content = { "latest_file" : file_name }

        self.file_saver.save_file("meta", meta_content) 
        return file_name



if __name__ == "__main__":
    server = LabelingServer(
        file_saver=FileSaver(root="saves/", file_type="yaml"), 
        host="127.0.0.1", 
        port=8053
    )
    server.start_server_thread(block=True)