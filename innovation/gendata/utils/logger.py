import logging
import os

def setup_logger(log_file_name: str):
    
    """
    Setup logger to print logs to the console with a configurable log level.

    Parameters:
    log_file_name (str): The name of the log source, used for the logger name.
    log_level (str): The level of logging (e.g., 'DEBUG', 'INFO', 'WARNING'). Default is 'INFO'.
    """

    log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    # Map string log level to actual logging level
    log_levels = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }

    # Get the log level from user input, defaulting to INFO if the input is invalid
    level = log_levels.get(log_level.upper(), logging.INFO)
    
    # Create a logger
    logger = logging.getLogger(log_file_name)
    logger.setLevel(level)
    
    # Create a console handler to log to the console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)  # Adjust log level as needed

    # Define a formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    
    # Add the handler to the logger
    logger.addHandler(console_handler)
    
    return logger