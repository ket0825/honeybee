from paddleocr import PaddleOCR

class OCREngine:
    _instance = None
    
    # singleton: 한번 만든 객체를 다시 재사용하게...
    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls._instance = PaddleOCR(lang="korean")
        return cls._instance
