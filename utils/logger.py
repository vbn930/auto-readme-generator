import logging
import streamlit as st

class StreamlitHandler(logging.Handler):
    """
    로그가 발생하면 Streamlit session_state에 저장하는 핸들러
    """
    def __init__(self):
        super().__init__()
        
    def emit(self, record):
        try:
            msg = self.format(record)
            # 세션 스테이트에 'log_lines' 리스트가 없으면 생성
            if 'log_lines' not in st.session_state:
                st.session_state['log_lines'] = []
            
            # 로그 추가
            st.session_state['log_lines'].append(msg)
        except Exception:
            self.handleError(record)

def setup_logger(name="README.ai"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # 중복 추가 방지 (이미 핸들러가 있으면 그대로 반환)
    if logger.hasHandlers():
        return logger

    # 포맷 설정
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')

    # 1. 콘솔 핸들러 (터미널용)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # 2. 파일 핸들러 (파일 저장용)
    file_handler = logging.FileHandler('app.log', encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # 3. Streamlit 핸들러 (대시보드 출력용) 👈 [새로 추가된 부분]
    st_handler = StreamlitHandler()
    st_handler.setFormatter(formatter)
    logger.addHandler(st_handler)

    return logger