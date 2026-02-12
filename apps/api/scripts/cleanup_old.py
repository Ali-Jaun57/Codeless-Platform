"""
Script to clean up old local deployments
Run this periodically or on startup
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.local_dev_service import local_dev_service
from utils.logger import Logger

logger = Logger("cleanup")

def main():
    logger.info("Starting cleanup of old local deployments...")
    
    # Clean up folders older than 1 hour
    local_dev_service.cleanup_old(hours_old=1)
    
    logger.success("Cleanup completed")

if __name__ == "__main__":
    main()