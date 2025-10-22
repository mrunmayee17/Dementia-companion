import time
from src.core.logging import get_logger

logger = get_logger(__name__)

class RateLimiter:
    """
    A simple rate limiter to manage API call frequency.
    """
    def __init__(self, rpm: int):
        if rpm <= 0:
            raise ValueError("RPM must be a positive integer.")
        self.interval = 60.0 / rpm
        self.last_call_time = 0
        logger.info(f"Rate limiter initialized for {rpm} RPM (interval: {self.interval:.2f}s).")

    def wait(self):
        """
        Blocks execution until the configured interval has passed since the last call.
        """
        elapsed = time.time() - self.last_call_time
        if elapsed < self.interval:
            sleep_time = self.interval - elapsed
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
            time.sleep(sleep_time)
        self.last_call_time = time.time()

# Global rate limiter for NVIDIA API, set slightly below the 40 RPM limit to be safe.
nvapi_rate_limiter = RateLimiter(rpm=38)
