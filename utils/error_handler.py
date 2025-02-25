# utils/error_handler.py

import logging
import asyncio
import traceback
from functools import wraps
from typing import Callable, Any, Tuple, Type

# Gelişmiş Log Yapılandırması
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('logs/error_handler.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('ErrorHandler')

# ===========================
# 📛 Özel Hata Sınıfları 📛
# ===========================

# Temel hata sınıfı
class BaseCustomError(Exception):
    """Tüm özel hatalar için temel sınıf."""
    pass

# Veri Çekme Hataları
class DataFetchError(BaseCustomError):
    """Veri çekme işlemlerinde oluşan genel hata."""
    pass

class NetworkError(DataFetchError):
    """Ağ bağlantı hatası"""
    pass

class RetryLimitExceeded(DataFetchError):
    """Maksimum yeniden deneme sayısına ulaşıldı"""
    pass

# Doğrulama ve Şifreleme Hataları
class ValidationError(BaseCustomError):
    """Veri doğrulama hatası"""
    pass

class DecryptionError(BaseCustomError):
    """Veri şifre çözme hatası"""
    pass

# Dosya İşleme Hataları
class FileProcessingError(BaseCustomError):
    """Dosya işleme sırasında oluşan hata"""
    pass

class FileNotFoundError(FileProcessingError):
    """Dosya bulunamadı hatası"""
    pass

class WritePermissionError(FileProcessingError):
    """Dosya yazma izni hatası"""
    pass

# Yeniden Bağlanma Hataları
class ConnectionClosedError(NetworkError):
    """WebSocket bağlantısı kapandı"""
    pass

class PayloadTooBigError(NetworkError):
    """Alınan veri çok büyük"""
    pass


# ================================
# 🔁 Otomatik Yeniden Deneme 🔁
# ================================

async def retry(
    func: Callable,
    retries: int = 3,
    delay: float = 2.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
) -> Any:
    """Yeniden deneme mekanizması"""
    attempt = 0
    while attempt < retries:
        try:
            return await func()
        except exceptions as e:
            logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
            attempt += 1
            await asyncio.sleep(delay * (backoff ** attempt))
    logger.error(f"Function {func.__name__} failed after {retries} attempts.")
    raise RetryLimitExceeded(f"Function {func.__name__} exceeded retry limit.")


# ==========================================
# 🎯 Genel Hata Yönetim Dekoratörü 🎯
# ==========================================

def handle_errors(func: Callable) -> Callable:
    """Fonksiyon hatalarını yakalayan asenkron dekoratör"""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except BaseCustomError as e:
            logger.error(f"Custom Error in {func.__name__}: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected Error in {func.__name__}: {str(e)}")
            logger.error(traceback.format_exc())
    return async_wrapper


def handle_sync_errors(func: Callable) -> Callable:
    """Senkron fonksiyonlar için hata yönetim dekoratörü"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except BaseCustomError as e:
            logger.error(f"Custom Error in {func.__name__}: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected Error in {func.__name__}: {str(e)}")
            logger.error(traceback.format_exc())
    return wrapper


# =====================================
# 🔍 Hata Seviyelerine Göre Loglama 🔍
# =====================================

def critical_error(message: str):
    """Kritik hata loglama"""
    logger.critical(f"[CRITICAL] {message}")


def warning_error(message: str):
    """Uyarı loglama"""
    logger.warning(f"[WARNING] {message}")


def info_message(message: str):
    """Bilgi mesajı loglama"""
    logger.info(f"[INFO] {message}")


# ===============================
# 🧪 Test Hata Fonksiyonları 🧪
# ===============================

@handle_errors
async def simulate_network_failure():
    """Ağ hatası simülasyonu"""
    raise NetworkError("Simulated network failure for testing.")

@handle_sync_errors
def simulate_file_error():
    """Dosya hatası simülasyonu"""
    raise FileProcessingError("Simulated file processing error for testing.")
