import os
import logging

from dotenv import load_dotenv
from github import Github

from utils import logger
    
class RepoDownloader:
    def __init__(self, logger: logging.Logger):
        load_dotenv()
        ACCESS_TOKEN = os.getenv("GITHUB_TOKEN")

        self.git_hub = Github(ACCESS_TOKEN)
        self.logger = logger
    
    def get_repos_from_git_hub(self, target_username: str) -> list:
        user = self.git_hub.get_user(target_username)
        repos = user.get_repos()
        return repos
    
    def get_archive_links(self, repos: list, only_download_public: bool = True) -> list:
        archive_names = list()
        archive_links = list()
        
        for repo in repos:
            if only_download_public: 
                if not repo.private:
                    archive_names.append(repo.name)
                    archive_links.append(repo.get_archive_link('zipball'))
            else:
                archive_names.append(repo.name)
                archive_links.append(repo.get_archive_link('zipball'))
                
        archive_pairs = list(zip(archive_names, archive_links))
        
        return archive_pairs