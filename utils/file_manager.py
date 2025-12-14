import os
import shutil
import zipfile
import logging

def unzip_and_clean(zip_path, extract_to, logger: logging.Logger):
    """
    1. 압축 해제
    2. 원본 zip 파일 삭제
    3. 단일 폴더로 감싸져 있다면 껍질 벗기기 (내용물을 상위로 이동)
    """
    
    # 1. 압축 해제
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
    except zipfile.BadZipFile:
        logger.error(f"Error: 잘못된 Zip 파일입니다 - {zip_path}")
        return

    # 2. 원본 Zip 파일 삭제
    os.remove(zip_path)

    # 3. 폴더 껍질 벗기기 (Flatten)
    # 압축 푼 폴더 안에 아이템이 딱 하나 있고, 그게 폴더람면? (예: repo/repo-main/...)
    items = os.listdir(extract_to)
    
    if len(items) == 1:
        inner_folder_name = items[0]
        inner_folder_path = os.path.join(extract_to, inner_folder_name)

        if os.path.isdir(inner_folder_path):
            # 내용물들을 전부 상위 폴더(extract_to)로 이동
            for filename in os.listdir(inner_folder_path):
                shutil.move(
                    os.path.join(inner_folder_path, filename), # 원래 위치
                    os.path.join(extract_to, filename)         # 이동할 위치
                )
            
            # 빈 껍데기 폴더 삭제
            os.rmdir(inner_folder_path)