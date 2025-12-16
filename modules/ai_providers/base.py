from abc import ABC, abstractmethod

class BaseAIProvider(ABC):
    """
    모든 AI Provider가 상속받아야 하는 추상 클래스
    """
    
    @abstractmethod
    async def generate_readme(self, repo_name: str, code_context: str) -> str:
        """
        레포 이름과 코드 내용을 받아 README 문자열을 반환해야 함.
        """
        pass