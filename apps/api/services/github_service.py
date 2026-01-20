# backend/services/github_service.py
from github import Github
from config import Config
from utils.logger import Logger

logger = Logger(__name__)

class GitHubService:
    def __init__(self):
        logger.step("GitHub Service", "initializing")
        try:
            self.client = Github(Config.GITHUB_TOKEN)
            self.user = self.client.get_user()
            logger.success(f"✅ GitHub Service initialized for user: {self.user.login}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize GitHub service: {str(e)}")
            raise
    
    def create_repository(self, name: str, private: bool = True):
        """Create a new repository"""
        logger.debug(f"Creating repository: {name} (private: {private})")
        try:
            repo = self.user.create_repo(name, private=private)
            logger.success(f"✅ Repository created: {repo.html_url}")
            return repo
        except Exception as e:
            logger.error(f"❌ Failed to create repository: {str(e)}")
            raise
    
    def create_file(self, repo, path: str, content: str, message: str = "Created by Codeless AI"):
        """Create a file in repository"""
        logger.debug(f"Creating file: {path}")
        try:
            repo.create_file(path, message, content)
            logger.success(f"✅ File created: {path}")
        except Exception as e:
            logger.error(f"❌ Failed to create file {path}: {str(e)}")
            raise
    
    def create_multiple_files(self, repo, files: list):
        """Create multiple files in repository"""
        logger.debug(f"Creating {len(files)} files")
        success_count = 0
        
        for file in files:
            try:
                self.create_file(repo, file["path"], file["content"])
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to create file {file['path']}: {str(e)}")
                continue
        
        logger.info(f"Created {success_count}/{len(files)} files successfully")
        return success_count

# Singleton instance
github_service = GitHubService()