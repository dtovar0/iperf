import logging
import os

# Configurar un logger para depuración de callbacks
def setup_debug_logger():
    log_file = "/home/dtovar/bayblade/iperf/logs/dash_debug.log"
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    logger = logging.getLogger("dash_debug")
    logger.setLevel(logging.DEBUG)
    
    # Evitar duplicar handlers
    if not logger.handlers:
        fh = logging.FileHandler(log_file)
        fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(fh)
    
    return logger

debug_logger = setup_debug_logger()
