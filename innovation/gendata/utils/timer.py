
import functools
import time
from innovation.gendata.utils.logger import setup_logger

logger = setup_logger(__name__)

def timeit(func):
    """Decorator to measure execution time."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        logger.info(f"Start {func.__name__}...")

        result = func(*args, **kwargs)

        elapsed_time = (time.time() - start_time) / 60
        logger.info(f"Done {func.__name__}: {elapsed_time:.5f} minutes\n")

        return result

    return wrapper