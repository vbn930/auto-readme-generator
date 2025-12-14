import os
import asyncio
import aiohttp
import aiofiles  # 비동기 파일 쓰기용

# 한 번에 동시에 다운로드할 최대 개수 (GitHub API 제한 방지용)
MAX_CONCURRENT_DOWNLOADS = 10

async def download_file(session, url, save_path, semaphore, logger=None):
    """
    세마포어를 사용하여 동시 실행 수를 제한하며 파일을 다운로드합니다.
    """
    async with semaphore: # 여기서 자리가 날 때까지 기다림
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    if logger: logger.error(f"다운로드 실패({response.status}): {url}")
                    return False
                
                # 파일 쓰기 (Chunk 단위로 끊어서 써야 메모리 절약됨)
                async with aiofiles.open(save_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(1024 * 1024): # 1MB씩
                        await f.write(chunk)
                        
            if logger: logger.info(f"다운로드 완료: {save_path}")
            return True
            
        except Exception as e:
            if logger: logger.error(f"에러 발생 {url}: {e}")
            return False

async def download_all_async(pairs, download_dir, logger=None):
    """
    pairs: [(이름, 링크), (이름, 링크), ...] 형태의 리스트
    """
    # 세마포어 생성 (동시 5개 제한)
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)
    
    zips = []
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for name, link in pairs:
            # 저장 경로 생성
            file_name  = f"{name}.zip"
            save_path = os.path.join(download_dir, f"{name}.zip")
            zips.append(file_name)
            
            # 작업 예약 (바로 실행되는 게 아니라 Task 리스트에 담김)
            task = download_file(session, link, save_path, semaphore, logger)
            tasks.append(task)
        
        # 여기서 모든 작업이 병렬로 시작되고, 다 끝날 때까지 기다림
        results = await asyncio.gather(*tasks)
        
    return results, zips # [True, False, True, ...] 성공 여부 리스트 반환