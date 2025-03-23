import logging
import logging.handlers
from pathlib import Path

def setup_logging():
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    console_handler = logging.StreamHandler()
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / "app.log",
        maxBytes=10*1024*1024,
        backupCount=5,
        encoding='utf-8'
    )
    error_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / "error.log",
        maxBytes=10*1024*1024,
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    error_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)
    
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    
    return logging.getLogger(__name__)

logger = setup_logging() 