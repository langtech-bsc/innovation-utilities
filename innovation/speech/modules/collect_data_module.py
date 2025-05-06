from innovation.speech.utils import io_utils
import logging
import os

class collect_data():

    def __init__(self, config: dict):
        self.config = config
        io_utils.setup_logging(self.config["log_level"])
        logging.info("[collect_data module] Setting and validating configuration")
        self._validate()

    def _validate(self):
        """
        Validate the configuration for the collect_data module.
        """
        
        self.config["data"]["input_folder"] = os.path.abspath(self.config["data"]["input_folder"])  

        # Check if input folder exists
        if not io_utils.check_folder_exists(self.config["data"]["input_folder"]):
            raise FileNotFoundError(f"Input folder '{self.config['data']['input_folder']}' does not exist.")

    def __call__(self):
        logging.info("[collect_data module] Listing files")
        files = io_utils.get_files_by_extension(self.config["data"]["input_folder"], 
                                                self.config["data"]["input_extensions"])
        
        if self.config["data"]["max_files"] != -1:
            logging.info(f"[collect_data module] getting only {self.config['data']['max_files']} files")
            files = files[:self.config["data"]["max_files"]]

        logging.info(f"[collect_data module] {len(files)} listed")
        self.files = files