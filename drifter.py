from sim_pub.base import ServerBase # requires https://github.com/intuitive-robots/SimPublisher.git
from time import strftime
import asyncio
import os
from fileio import FileSaver
import json


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