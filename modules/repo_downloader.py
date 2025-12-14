import os
import logging

from dotenv import load_dotenv
from github import Github

import utils
    
class RepoDownloader:
    def __init__(self, logger: logging.Logger):
        load_dotenv()
        ACCESS_TOKEN = os.getenv("GITHUB_TOKEN")

        self.git_hub = Github(ACCESS_TOKEN)
        self.logger = logger
    
    def get_repos_from_git_hub(self, target_username: str) -> list:
        user = self.git_hub.get_user(target_username)
        repos = user.get_repos()
        repos = list(repos) # PagenatedList를 모두 다운받아서 리스트로 변환 후 반환
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
    
    async def download_all_repos_async(self, archive_pairs: list, download_dir: str) -> list:
        downloaded_file_paths = []
        success_list, file_names = await utils.downloader.download_all_async(archive_pairs, download_dir, self.logger)
        
        for is_success, filename in zip(success_list, file_names):
            if is_success:
                downloaded_file_path = os.path.join(download_dir, filename)
                downloaded_file_paths.append(downloaded_file_path)
                
                utils.file_manager.unzip_and_clean(downloaded_file_path, download_dir, self.logger)
                
        
        return downloaded_file_paths