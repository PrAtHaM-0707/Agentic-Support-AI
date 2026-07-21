import logging
import sys

def setup_logger(name: str) -> logging.Logger:
    """
    Setup a logger with standard formatting for the application.
    """
    logger = logging.getLogger(name)
    
    # Avoid adding multiple handlers if the logger is already setup
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Create console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger

# Create a default logger for the app
app_logger = setup_logger("agentic_support")
