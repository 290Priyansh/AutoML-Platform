import subprocess
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

class DVCManager:
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
    
    def init(self, force: bool = False) -> bool:
        """Initialize DVC in the repository"""
        try:
            cmd = ["dvc", "init"]
            if force:
                cmd.append("--force")
            result = subprocess.run(cmd, cwd=self.repo_path, capture_output=True, text=True)
            return result.returncode == 0
        except Exception as e:
            logger.error(f"DVC init failed: {e}")
            return False
    
    def add(self, file_path: str) -> bool:
        """Add a file to DVC tracking"""
        try:
            result = subprocess.run(
                ["dvc", "add", file_path], 
                cwd=self.repo_path, 
                capture_output=True, 
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"DVC add failed: {e}")
            return False
    
    def push(self, remote: str = "origin") -> bool:
        """Push DVC tracked files to remote storage"""
        try:
            result = subprocess.run(
                ["dvc", "push", "-r", remote], 
                cwd=self.repo_path, 
                capture_output=True, 
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"DVC push failed: {e}")
            return False
    
    def pull(self, remote: str = "origin") -> bool:
        """Pull DVC tracked files from remote storage"""
        try:
            result = subprocess.run(
                ["dvc", "pull", "-r", remote], 
                cwd=self.repo_path, 
                capture_output=True, 
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"DVC pull failed: {e}")
            return False
    
    def fetch(self, remote: str = "origin") -> bool:
        """Fetch DVC tracked files metadata from remote"""
        try:
            result = subprocess.run(
                ["dvc", "fetch", "-r", remote], 
                cwd=self.repo_path, 
                capture_output=True, 
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"DVC fetch failed: {e}")
            return False
    
    def checkout(self) -> bool:
        """Checkout DVC tracked files to working directory"""
        try:
            result = subprocess.run(
                ["dvc", "checkout"], 
                cwd=self.repo_path, 
                capture_output=True, 
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"DVC checkout failed: {e}")
            return False

# Global instance
dvc_manager = DVCManager()