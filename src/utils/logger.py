from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler

import json
import logging
import os
import sys

# Configure logging
def setup_logging():
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok = True)
    
    # Create formatters
    json_formatter = logging.Formatter('%(message)s')
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create handlers
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    
    # File handler with rotation (10MB per file, max 5 files)
    file_handler = RotatingFileHandler(
        'logs/app.log',
        maxBytes = 10*1024*1024,  # 10MB
        backupCount = 5
    )
    file_handler.setFormatter(json_formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Create a custom JSON logger
    class JsonLogger(logging.Logger):
        def _log(self, level, msg, _, exc_info = None, extra = None, stack_info = False, stacklevel = 1):
            if extra is None:
                extra = {}
            
            # Create JSON log entry
            log_entry = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'level': level,
                'logger': self.name,
                'message': msg,
                **extra
            }
            
            if exc_info:
                log_entry['exception'] = self.formatException(exc_info)
            
            super()._log(level, json.dumps(log_entry), (), exc_info, extra, stack_info, stacklevel)
    
    # Register the custom logger
    logging.setLoggerClass(JsonLogger)