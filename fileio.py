import json, yaml
import os



class FileSaver():
    
    def __init__(self, root="", file_type="yaml", inline=True):

        OPTIONS = { 
            "yaml" : self._save_to_yaml,
            "json" : self._save_to_json 
        }

        if file_type not in OPTIONS.keys(): print("Invalid file type selected", file_type)
        self.save_fn = OPTIONS[file_type]
        self.inline = inline

        self.root = root if root.endswith("/") else root + "/"
        self.create_dir("")

    def save_file(self, file_name : str, content) -> str:
        return self.save_fn(self.root + file_name, content)



    def create_dir(self, folder_name : str):
        folder_name = self.root + folder_name
        if not os.path.isdir(folder_name): os.mkdir(folder_name)

    #--- private
    def _save_to_json(self, file_name : str, content):
        file_name += ".json"
        json_str = json.dumps(content, indent = 4)
        FileSaver._save_to_file(file_name, json_str)

        return file_name

    def _save_to_yaml(self, file_name : str, content):
        file_name += ".yaml"
        yaml_str = yaml.dump(content, indent = 4, Dumper=InlineArrayDumper if self.inline else yaml.Dumper)
        FileSaver._save_to_file(file_name, yaml_str)
        return file_name

    @staticmethod
    def _save_to_file(file_name : str, content : str): 
        mode = "w" if os.path.isfile(file_name) else "x"
        with open(file_name, mode) as fp:
            fp.write(content)


class InlineArrayDumper(yaml.Dumper):
    def represent_sequence(self, tag, sequence, flow_style=None):
        return super(InlineArrayDumper, self).represent_sequence(tag, sequence, flow_style=True) # Force inline style for sequences

def read_yaml(file_path : str) -> dict:
    content = None
    with open(file_path, "r") as fp:
        content = yaml.load(fp, Loader=yaml.FullLoader)
    return content

if __name__ == "__main__":
  pass