# utils/processor_error_handler.py

import logging
from functools import wraps
import traceback

# Log Yapılandırması
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("logs/processor_error_handler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ProcessorErrorHandler")

# 🎯 Özel Hata Sınıfları
class ProcessorDataError(Exception):
    """Veri işleme sırasında oluşan genel hata"""
    pass

class MissingDataError(ProcessorDataError):
    """Eksik veri hatası"""
    pass

class InvalidDataError(ProcessorDataError):
    """Geçersiz veri formatı hatası"""
    pass

# 🚀 Hata Yönetim Dekoratörü
def handle_errors(func):
    """Veri işleme fonksiyonlarında hata yönetimi"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ProcessorDataError as e:
            logger.error(f"Data Processing Error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected Error in {func.__name__}: {str(e)}")
            logger.error(traceback.format_exc())
    return wrapper
