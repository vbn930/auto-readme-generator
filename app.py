import os
import asyncio

import streamlit as st

from utils.logger import setup_logger

from modules import ReadmeGenerator
from modules import RepoDownloader

# 페이지 기본 설정 (화면을 넓게 씀)
st.set_page_config(page_title="GitHub README Generator", layout="wide")

# 세션 상태 초기화 (우측 미리보기 인덱스 관리를 위해 필요)
if 'preview_index' not in st.session_state:
    st.session_state.preview_index = 0

# --- [목업 데이터] 실제 로직 연결 시 삭제될 부분 ---
MOCK_REPOS = [
    {"name": "Distributed-System-Engine", "content": "# Distributed System Engine\n\n이 프로젝트는 분산 시스템을 위한..."},
    {"name": "Real-Time-Network-Lib", "content": "# Real-Time Network Lib\n\nUDP 기반의 신뢰성 있는 전송을 보장하는..."},
    {"name": "AI-Pathfinding-Study", "content": "# AI Pathfinding\n\nA* 알고리즘과 JPS를 비교 분석한..."},
]

def get_current_repo():
    """현재 인덱스에 해당하는 레포지토리 정보를 반환"""
    idx = st.session_state.preview_index % len(MOCK_REPOS)
    return MOCK_REPOS[idx]

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
    username = st.text_input("GitHub Username", placeholder="e.g., dohun-lee")
    
    # 프라이빗 레포 체크박스
    include_private = st.checkbox("Private Repo 포함 가져오기")
    
    st.write("") # 여백
    
    # 레포 가져오기 버튼
    if st.button("유저 레포 가져오기", use_container_width=True):
        # TODO: GitHub API를 통해 레포지토리 리스트를 불러오는 함수 호출
        st.info("API 호출: 레포지토리 목록을 가져옵니다 (Mock)")

# ==========================================
# 2. 중간: 레포 목록 및 선택
# ==========================================
with col_mid:
    st.subheader("2. 레포지토리 선택")
    
    # 컨테이너를 사용하여 영역 구분
    with st.container(border=True):
        st.write("가져온 레포지토리 목록")
        
        # 전체 선택/해제 기능 (선택 사항)
        select_all = st.checkbox("전체 선택")
        
        st.divider()
        
        # 레포지토리 리스트 출력 (체크박스)
        # TODO: 실제 데이터가 들어오면 for문으로 동적 생성
        selected_repos = []
        for repo in MOCK_REPOS:
            is_checked = st.checkbox(f"📁 {repo['name']}", value=select_all)
            if is_checked:
                selected_repos.append(repo['name'])
    
    st.write("") # 여백
    
    # 생성 버튼
    if st.button("다운로드 및 README 생성", type="primary", use_container_width=True):
        if not selected_repos:
            st.warning("레포지토리를 하나 이상 선택해주세요.")
        else:
            # TODO: 선택된 레포들을 다운로드하고 AI로 리드미를 생성하는 로직 호출
            st.success(f"{len(selected_repos)}개의 README 생성을 시작합니다.")

# ==========================================
# 3. 오른쪽: 미리보기 및 개별 제어
# ==========================================
with col_right:
    st.subheader("3. 결과 미리보기")
    
    # 현재 보고 있는 레포 정보 가져오기
    current_repo = get_current_repo()
    
    # --- 카루셀 (네비게이션) ---
    nav_col1, nav_col2, nav_col3 = st.columns([1, 4, 1], vertical_alignment="center")
    
    with nav_col1:
        if st.button("◀", key="prev"):
            st.session_state.preview_index -= 1
            st.rerun()
            
    with nav_col2:
        # 가운데 정렬된 레포 이름
        st.markdown(f"<h3 style='text-align: center; margin:0;'>{current_repo['name']}</h3>", unsafe_allow_html=True)
        
    with nav_col3:
        if st.button("▶", key="next"):
            st.session_state.preview_index += 1
            st.rerun()
            
    st.divider()
    
    # --- README 미리보기 영역 ---
    # 실제 마크다운이 렌더링되어 보임
    preview_container = st.container(height=500, border=True) # 스크롤 가능한 영역
    with preview_container:
        st.markdown(current_repo['content'])
    
    st.write("") # 여백
    
    # --- 개별 재생성 버튼 ---
    if st.button(f"🔄 '{current_repo['name']}' 리드미만 다시 재생성", use_container_width=True):
        # TODO: 현재 인덱스의 레포지토리만 다시 생성하는 함수 호출
        st.toast(f"{current_repo['name']} 리드미를 재생성 중입니다...", icon="🔄")