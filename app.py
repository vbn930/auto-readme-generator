import os
import asyncio
import time

import streamlit as st
import google.generativeai as genai

from utils.logger import setup_logger
from utils.file_manager import folder_to_markdown

from modules import ReadmeGenerator
from modules import RepoDownloader
from modules.ai_providers import get_ai_provider

# 페이지 기본 설정 (화면을 넓게 씀)
st.set_page_config(page_title="GitHub README Generator", layout="wide")

# Static Resource
@st.cache_resource
def get_logger():
    return setup_logger()
    
@st.cache_resource
def get_repo_downloader(_logger):
    return RepoDownloader(logger=_logger)

# Creation order: logger -> others...
logger = get_logger()
repo_downloader = get_repo_downloader(logger)

# 세션 상태 초기화 (우측 미리보기 인덱스 관리를 위해 필요)
if 'preview_index' not in st.session_state:
    st.session_state.preview_index = 0

# Repo and archive_pair
if 'repos' not in st.session_state:
    st.session_state.repos = []

if 'archive_pairs' not in st.session_state:
    st.session_state.archive_pairs = []

if 'user_name' not in st.session_state:
    st.session_state.user_name = None

if 'loaded_repos' not in st.session_state:
    st.session_state.loaded_repos = []

if 'download_dir' not in st.session_state:
    current_file_path = os.path.abspath(__file__)
    root_dir = os.path.dirname(current_file_path)
    download_dir = os.path.join(root_dir, "downloads")
    os.makedirs(download_dir, exist_ok=True)
    st.session_state.download_dir = download_dir
    
if 'results' not in st.session_state:
    st.session_state.results = []

def get_current_repo():
    """현재 인덱스에 해당하는 레포지토리 정보를 반환"""
    if 'results' not in st.session_state or not st.session_state.results:
        return None
    idx = st.session_state.preview_index % len(st.session_state.results)
    return st.session_state.results[idx]

# ==========================================
# 헬퍼 함수: 사용 가능한 Gemini 모델 가져오기
# ==========================================
@st.cache_data(ttl=3600) # 1시간 동안 캐싱 (API 호출 절약)
def get_available_gemini_models(api_key):
    """API 키를 이용해 실제 사용 가능한 모델 리스트를 가져옴"""
    try:
        genai.configure(api_key=api_key)
        models = []
        for m in genai.list_models():
            # 텍스트 생성이 가능한 모델만 필터링
            if 'generateContent' in m.supported_generation_methods:
                # 'models/gemini-pro' 형태에서 'models/' 제거하고 깔끔하게
                models.append(m.name.replace("models/", ""))
        return models
    except Exception as e:
        # 에러 발생 시(키가 틀렸거나 등) 기본 목록 반환
        return ["gemini-1.5-flash", "gemini-pro", "gemini-1.0-pro"]

# ==========================================
# 사이드바: 설정 영역
# ==========================================

with st.sidebar:
    st.header("⚙️ 환경 설정")
    
    # 1. AI 서비스 선택
    # (변수명을 service_provider로 명확히 함)
    service_provider = st.selectbox(
        "AI 서비스 선택", 
        ["Gemini", "OpenAI"],
        index=0
    )
    
    # 2. API 키 입력
    api_key = st.text_input(
        f"{service_provider} API Key", 
        type="password",
        placeholder="sk-..." if service_provider == "OpenAI" else "AIza..."
    )
    
    # 3. [NEW] 모델 선택 로직
    selected_model_name = ""
    
    if service_provider == "Gemini":
        if api_key:
            # 키가 있으면 실제 목록을 가져옴
            with st.spinner("모델 목록 불러오는 중..."):
                gemini_options = get_available_gemini_models(api_key)
                
            selected_model_name = st.selectbox(
                "사용할 모델 (Model)", 
                gemini_options,
                index=0 
            )
            # 1.5-flash가 안되면 여기서 gemini-pro 등을 선택하면 됨!
        else:
            # 키가 없으면 그냥 보여주기용 더미
            st.selectbox("사용할 모델", ["API 키를 먼저 입력하세요"], disabled=True)
            
    else: # OpenAI인 경우
        selected_model_name = st.selectbox(
            "사용할 모델",
            ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
            index=0
        )
        
    st.info("API Key는 저장되지 않습니다.")
    
# --- [UI 레이아웃] ---
st.title("Auto README Generator Dashboard")
st.markdown("---")

# 3개의 컬럼으로 분할 (비율 조정 가능)
col_left, col_mid, col_right = st.columns([1, 1.5, 2])

# ==========================================
# 1. 왼쪽: 사용자 입력 및 가져오기
# ==========================================
with col_left:
    st.subheader("1. GitHub 설정")
    
    # 유저네임 입력
    username = st.text_input("GitHub Username", placeholder="e.g., user-name")
    
    # 프라이빗 레포 체크박스
    include_private = st.checkbox("Private Repo 포함 가져오기")
    
    st.write("") # 여백
    
    # 레포 가져오기 버튼
    if st.button("유저 레포 가져오기", use_container_width=True):
        if not username:
            st.error("GitHub 유저 네임을 입력해주세요!")
        else:
            # Initailize user name
            st.session_state.user_name = username
            # 로딩 시작 (스피너)
            with st.spinner(f"GitHub에서 '{username}'님의 저장소를 찾고 있습니다..."):
                
                repos = repo_downloader.get_repos_from_git_hub(username)
                archive_pairs = repo_downloader.get_archive_links(repos, not include_private)
                time.sleep(1.5) # (로딩 느낌을 주기 위한 가짜 딜레이)
                
            # 로딩이 끝나면 실행되는 부분
            st.success("레포지토리 목록 갱신 완료!")
            
            st.session_state.repos = repos
            st.session_state.archive_pairs = archive_pairs

# ==========================================
# 2. 중간: 레포 목록 및 선택
# ==========================================
with col_mid:
    st.subheader("2. 레포지토리 선택")
    
    # 컨테이너를 사용하여 영역 구분
    with st.container(height=400, border=True):
        st.write("가져온 레포지토리 목록")
        
        # 전체 선택/해제 기능 (선택 사항)
        select_all = st.checkbox("전체 선택")
        
        st.divider()
        
        # 레포지토리 리스트 출력 (체크박스)
        selected_repos = []
        for repo in st.session_state.archive_pairs:
            is_checked = st.checkbox(f"📁 {repo[0]}", value=select_all)
            if is_checked:
                selected_repos.append(repo)
    
    st.write("") # 여백
    st.divider() # 구분선 추가
    
    # ---------------------------------------------------------
    # [NEW] 3. 생성 옵션 설정 UI
    # ---------------------------------------------------------
    st.subheader("3. 생성 옵션")
    
    with st.container(border=True):
        # 1. 언어 선택 (라디오 버튼)
        target_lang = st.radio(
            "작성 언어 (Language)", 
            ["Korean", "English"], 
            index=0, 
            horizontal=True
        )
        
        # 2. 강조 키워드 (텍스트 입력)
        user_keywords = st.text_input(
            "강조할 키워드 (선택 사항)", 
            placeholder="예: Real-time, UDP, Zero-copy, Lock-free"
        )
        st.caption("💡 입력한 키워드를 중심으로 리드미가 작성됩니다.")

    st.write("") # 여백
    
    # ---------------------------------------------------------
    # [Mock] 2. AI 생성 Async 함수 (다운로드 로직과 구조 동일)
    # ---------------------------------------------------------
    async def generate_all_readmes_async(repo_names, contents):
        """
        [새로 추가된 부분]
        다운로드된 파일 경로들을 받아, 내부적으로 비동기(gather)로
        AI 생성을 수행하고 결과 내용을 반환하는 함수
        """
        if not api_key:
            st.error("API 키를 입력해주세요.")
            return []
        
        ai_provider = get_ai_provider(service_provider, api_key, model_name=selected_model_name)
        
        logger.debug(f"🧠 AI Provider: {type(ai_provider).__name__} 사용하여 README 생성 시작")
        # 내부 함수: 개별 생성 작업
        async def generate_single(name, content):
            return await ai_provider.generate_readme(name, content, user_keywords, target_lang)

        # asyncio.gather를 사용하여 모든 생성을 병렬로 실행!
        # 다운로드 함수처럼 모든 작업이 끝날 때까지 기다렸다가 결과를 리스트로 받음
        results = await asyncio.gather(*[
            generate_single(name, content) 
            for name, content in zip(repo_names, contents)
        ])
        
        return results

    async def generate_readme_async(repo_name, content):
        """
        [새로 추가된 부분]
        다운로드된 파일 경로들을 받아, 내부적으로 비동기(gather)로
        AI 생성을 수행하고 결과 내용을 반환하는 함수
        """
        if not api_key:
            st.error("API 키를 입력해주세요.")
            return None

        ai_provider = get_ai_provider(service_provider, api_key, model_name=selected_model_name)

        readme = await ai_provider.generate_readme(repo_name, content, user_keywords, target_lang)
        
        return repo_name, readme
    # ---------------------------------------------------------
    # 3. 버튼 클릭 핸들러 (매우 깔끔해짐)
    # ---------------------------------------------------------
    if st.button("다운로드 및 README 생성", type="primary", use_container_width=True):
        if not selected_repos:
            st.warning("레포지토리를 선택해주세요.")
        else:
            # 전체 프로세스를 비동기로 실행하는 메인 함수 정의
            async def run_pipeline():
                # [Step 1] 다운로드 (Spinner)
                # -------------------------------------------------
                with st.spinner(f"📦 {len(selected_repos)}개의 레포지토리 다운로드 중..."):
                    repo_names, file_paths = await repo_downloader.download_all_repos_async(st.session_state.user_name, selected_repos, st.session_state.download_dir)
                    
                
                # Folder to one mark down file
                with st.status("📦 폴더를 하나의 마크다운 파일로 패키징 중입니다...", expanded=True) as status:
                    
                    mk_dir = os.path.join(st.session_state.download_dir, st.session_state.user_name)
                    contents = []
                    for repo_name, file_path in zip(repo_names, file_paths):
                        output_path = os.path.join(mk_dir, f"{repo_name}.md")
                        contents.append(folder_to_markdown(file_path, output_path, logger))
                        
                    
                
                st.toast("다운로드 및 패키징 완료! AI 생성을 시작합니다.", icon="✅")
                
                # [Step 2] AI 생성 (Spinner or Status)
                # -------------------------------------------------
                # 로직이 함수 안으로 숨었기 때문에 UI에서는 단순히 '대기'만 하면 됨
                with st.status("🧠 AI가 README를 생성하고 있습니다...", expanded=True) as status:
                    
                    # 여기서 '생성 함수'를 호출 (일괄 처리)
                    readme_contents = await generate_all_readmes_async(repo_names, contents)
                    logger.debug(f"📝 생성된 README 개수: {len(readme_contents)}")
                    status.update(label="✨ 모든 작업 완료!", state="complete", expanded=False)
                
                return repo_names, readme_contents, contents

            # -------------------------------------------------
            # 실행 진입점 (asyncio.run)
            # -------------------------------------------------
            try:
                # 파이프라인 실행 및 결과 받아오기
                final_names, final_contents, contexts = asyncio.run(run_pipeline())
                
                st.success(f"총 {len(final_names)}개의 README가 생성되었습니다.")
                
                # (선택) 결과를 세션에 저장하거나 미리보기에 바로 반영
                st.session_state.results = list(zip(final_names, final_contents, contexts))
                
            except Exception as e:
                st.error(f"작업 중 오류 발생: {e}")

# ==========================================
# 3. 오른쪽: 미리보기 및 개별 제어
# ==========================================
with col_right:
    st.subheader("3. 결과 미리보기")
    
    current_repo = get_current_repo()
    idx = st.session_state.preview_index % len(st.session_state.results) if st.session_state.results else 0
    
    # [수정됨] 데이터가 없을 때의 처리 (Empty State)
    if current_repo is None:
        # 깔끔한 안내 박스 표시
        with st.container(border=True):
            st.info("👈 왼쪽에서 레포지토리를 가져오고 생성 버튼을 눌러주세요.")
            st.markdown("""
            **사용 방법:**
            1. GitHub 유저네임 입력
            2. '유저 레포 가져오기' 클릭
            3. 원하는 프로젝트 선택 후 '생성' 클릭
            """)
            
    else:
        # [기존 로직] 데이터가 있을 때만 렌더링
        
        # --- 카루셀 (네비게이션) ---
        nav_col1, nav_col2, nav_col3 = st.columns([1, 4, 1], vertical_alignment="center")
        
        with nav_col1:
            if st.button("◀", key="prev"):
                st.session_state.preview_index -= 1
                st.rerun()
                
        with nav_col2:
            st.markdown(f"<h3 style='text-align: center; margin:0;'>{current_repo[0]}</h3>", unsafe_allow_html=True)

        with nav_col3:
            if st.button("▶", key="next"):
                st.session_state.preview_index += 1
                st.rerun()
                
        st.divider()
        
        # --- README 미리보기 ---
        preview_container = st.container(height=500, border=True)
        with preview_container:
            content = current_repo[1]
            st.markdown(content)
        
        st.write("") 
        
        # --- 개별 재생성 버튼 ---
        if st.button(f"🔄 '{current_repo[0]}' 리드미만 다시 재생성", use_container_width=True):
            with st.spinner(f"'{current_repo[0]}'를 다시 분석하고 있습니다..."):
                repo_name, readme = asyncio.run(generate_readme_async(current_repo[0], current_repo[2]))
                st.session_state.results[idx] = (repo_name, readme, current_repo[2])
                current_repo = st.session_state.results[idx]
            st.toast("재생성 완료!", icon="✅")
            st.rerun()