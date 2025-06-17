class HNSystemError(Exception):
    """自定义系统异常类"""
    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return f"HNSystemError: {self.message}"