import os
import asyncio

from utils.logger import setup_logger

from modules import ReadmeGenerator
from modules import RepoDownloader

if __name__ == "__main__":
    # 1. 현재 실행 중인 파일(app.py)의 절대 경로를 구함
    current_file_path = os.path.abspath(__file__)

    # 2. 그 파일이 있는 폴더(디렉토리) 경로만 추출
    root_dir = os.path.dirname(current_file_path)

    # 3. 그 폴더 안에 'downloads' 경로 생성
    download_dir = os.path.join(root_dir, "downloads")
    os.makedirs(download_dir, exist_ok=True)

    logger = setup_logger()

    # repo_downloader 테스트
    repo_downloader = RepoDownloader(logger)

    repos = repo_downloader.get_repos_from_git_hub("vbn930")
    logger.debug(f"Total {len(repos)} repos loaded")
    archive_pairs = repo_downloader.get_archive_links(repos)
    logger.debug(f"Total {len(archive_pairs)} archive loaded")

    downloaded_file_paths = asyncio.run(repo_downloader.download_all_repos_async(archive_pairs, download_dir))
    
    logger.debug(f"Total {len(downloaded_file_paths)}  downloaded")