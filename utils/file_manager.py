import os
import shutil
import zipfile
import logging

# 1. 설정: 무시할 폴더 및 텍스트로 읽을 확장자 정의
IGNORE_DIRS = {
    '.git', '.svn', '.hg', '.idea', '.vscode', '.vs', 
    'venv', 'env', 'node_modules', '__pycache__', 
    'dist', 'build', 'bin', 'obj', 'target', 
    'DerivedData', 'Archives', 'Artifacts', # iOS/Mac
    'Intermediate', 'Saved', 'DerivedDataCache' # Unreal Engine
}

# 텍스트로 취급할 확장자 (필요하면 추가하세요)
TEXT_EXTENSIONS = {
    '.py', '.java', '.c', '.cpp', '.h', '.hpp', '.cs', '.js', '.ts', '.jsx', '.tsx',
    '.html', '.css', '.scss', '.less', '.json', '.xml', '.yaml', '.yml', '.toml',
    '.md', '.txt', '.sh', '.bat', '.ps1', '.lua', '.sql', '.ini', '.cfg', '.conf',
    '.gradle', '.properties', '.dockerfile', 'makefile', 'cmake', '.cmake'
}

def get_top_level_folder(zip_path):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        # 1. 모든 파일/폴더 목록 가져오기
        all_names = zip_ref.namelist()
        
        if not all_names:
            return None # 빈 파일 처리

        # 2. 각 경로의 가장 첫 번째 부분(루트 폴더명)만 추출해서 집합(Set)으로 만듦
        # 예: 'project/src/main.py' -> 'project'
        # 예: 'file.txt' -> 'file.txt'
        root_items = {name.split('/')[0] for name in all_names}

        # 3. 루트 항목이 딱 1개라면, 그게 최상위 폴더임
        if len(root_items) == 1:
            return list(root_items)[0]
        else:
            # 루트에 여러 파일이나 폴더가 섞여 있는 경우 (최상위 폴더 없음)
            return None

def unzip_and_clean(zip_path, extract_to, logger: logging.Logger):
    """
    1. 압축 해제
    2. 원본 zip 파일 삭제
    3. 단일 폴더로 감싸져 있다면 껍질 벗기기 (내용물을 상위로 이동)
    """
    top_level_folder = get_top_level_folder(zip_path)
    # 1. 압축 해제
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
    except zipfile.BadZipFile:
        logger.error(f"Error: 잘못된 Zip 파일입니다 - {zip_path}")
        return

    # 2. 원본 Zip 파일 삭제
    os.remove(zip_path)
    
    full_path = os.path.join(extract_to, top_level_folder)

    print(full_path)
    
    return os.path.abspath(extract_to), full_path

def get_tree_structure(root_dir, prefix=""):
    """폴더 구조를 문자열 트리로 반환"""
    tree_str = ""
    try:
        files = sorted(os.listdir(root_dir))
        # 무시할 폴더 필터링
        files = [f for f in files if f not in IGNORE_DIRS]
        
        for i, file in enumerate(files):
            path = os.path.join(root_dir, file)
            is_last = (i == len(files) - 1)
            connector = "└── " if is_last else "├── "
            
            tree_str += prefix + connector + file + "\n"
            
            if os.path.isdir(path):
                extension = "    " if is_last else "│   "
                tree_str += get_tree_structure(path, prefix + extension)
    except PermissionError:
        tree_str += prefix + "└── [Permission Denied]\n"
    
    return tree_str

def folder_to_markdown(root_path, output_file, logger: logging.Logger):
    """
    지정된 폴더를 읽어 하나의 MD 파일로 생성
    """
    output = []
    root_abs_path = os.path.abspath(root_path)
    project_name = os.path.basename(root_abs_path)
    logger.debug(f"📂 폴더 경로: {root_abs_path}")
    logger.debug(f"📝 출력 파일: {output_file}")
    logger.debug(f"📦 패키징 시작: {project_name}...")

    # 1. 프로젝트 정보 헤더
    output.append(f"# Project Context: {project_name}\n")
    output.append("> This file was automatically generated for AI code analysis.\n\n")

    # 2. 폴더 구조 (Tree)
    output.append("## 1. Project Structure\n")
    output.append("```text\n")
    output.append(get_tree_structure(root_path))
    output.append("```\n\n")

    # 3. 파일 내용 순회
    output.append("## 2. File Contents\n")
    
    file_count = 0
    
    for root, dirs, files in os.walk(root_path):
        # 무시할 폴더는 탐색에서 제외 (in-place modification)
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, root_path).replace("\\", "/") # 윈도우 경로 호환
            ext = os.path.splitext(file)[1].lower()
            
            # Dockerfile 등 확장자 없는 파일 처리
            if file.lower() == 'dockerfile':
                ext = '.dockerfile'

            # 텍스트 파일인지 확인
            if ext in TEXT_EXTENSIONS:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        # Markdown 포맷팅
                        # 언어 힌트 (py, cpp 등) 추출 (점 제거)
                        lang_hint = ext[1:] if ext else ""
                        
                        output.append(f"\n### File: `{rel_path}`\n")
                        output.append(f"```{lang_hint}\n")
                        output.append(content)
                        output.append("\n```\n")
                        output.append("---\n") # 파일 간 구분선
                        
                        file_count += 1
                except Exception as e:
                    # 인코딩 에러 등으로 못 읽은 경우
                    output.append(f"\n### File: `{rel_path}` (Read Error)\n")
                    output.append(f"> Error reading file: {e}\n")
            else:
                # 바이너리 파일 등은 목록에는 표시하되 내용은 생략
                output.append(f"\n### File: `{rel_path}` (Binary/Asset)\n")
                output.append("> Content skipped (Non-text file)\n")

    # 4. 파일 저장
    final_text = "".join(output)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(final_text)
    
    logger.debug(f"✅ 완료! 총 {file_count}개의 코드 파일이 포함되었습니다.")
    logger.debug(f"📁 생성된 파일: {os.path.abspath(output_file)}")
    
    return final_text