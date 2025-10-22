"""Utility functions"""
import logging
from pathlib import Path
from typing import Optional


def setup_logging(log_file: Optional[Path] = None, level: int = logging.INFO):
    """
    Configure logging for the project
    
    Args:
        log_file: Optional path to log file
        level: Logging level
    """
    handlers = [logging.StreamHandler()]
    
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )


def validate_file_exists(file_path: Path) -> bool:
    """Check if a file exists"""
    return file_path.exists() and file_path.is_file()


def validate_directory_exists(dir_path: Path) -> bool:
    """Check if a directory exists"""
    return dir_path.exists() and dir_path.is_dir()
