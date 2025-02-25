# utils/ai_error_handler.py

import logging
import time
import functools
from enum import Enum, auto
from dotenv import load_dotenv
import os
import requests

# Ortam değişkenlerini yükleme
load_dotenv()

# Ortam değişkenleri
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
RETRY_LIMIT = int(os.getenv("RETRY_LIMIT", 3))
RETRY_DELAY = int(os.getenv("RETRY_DELAY", 5))  # saniye

# Log yapılandırması
logger = logging.getLogger("AIErrorHandler")

# Hata Öncelik Seviyeleri
class ErrorSeverity(Enum):
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    CRITICAL = auto()

# Özel Hata Sınıfları
class AIError(Exception):
    pass

class SwarmOptimizationError(AIError):
    pass

class ReinforcementLearningError(AIError):
    pass

class QuantumCognitionError(AIError):
    pass

class MetaStrategyError(AIError):
    pass

class DataManagerError(AIError):
    pass

class MissingDataError(DataManagerError):
    pass

class DataIntegrityError(DataManagerError):
    pass

class BaseLayerError(AIError):
    pass

# Hata Bildirim Fonksiyonu
def send_telegram_alert(message):
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        try:
            requests.post(url, data=payload)
        except Exception as e:
            logger.error(f"Telegram bildirimi başarısız: {str(e)}")

# Hata Yönetim Dekoratörü
def handle_errors(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        retries = 0
        while retries < RETRY_LIMIT:
            try:
                return func(*args, **kwargs)
            except AIError as e:
                severity = classify_error(e)
                logger.error(f"Hata [{severity.name}]: {str(e)} - {func.__name__}")
                send_telegram_alert(f"🚨 [{severity.name}] Hata: {str(e)} - Fonksiyon: {func.__name__}")
                if severity == ErrorSeverity.CRITICAL:
                    logger.critical(f"Kritik hata tespit edildi, işlem durduruluyor.")
                    raise e
                retries += 1
                time.sleep(RETRY_DELAY)
            except Exception as e:
                logger.error(f"Beklenmeyen Hata: {str(e)} - {func.__name__}")
                send_telegram_alert(f"❌ Beklenmeyen Hata: {str(e)} - Fonksiyon: {func.__name__}")
                raise e
        logger.error(f"{func.__name__} fonksiyonu {RETRY_LIMIT} deneme sonrası başarısız oldu.")
        send_telegram_alert(f"❌ {func.__name__} fonksiyonu {RETRY_LIMIT} deneme sonrası başarısız oldu.")
    return wrapper

# Hata Öncelik Sınıflandırma Fonksiyonu
def classify_error(error):
    if isinstance(error, (MissingDataError, DataIntegrityError)):
        return ErrorSeverity.LOW
    elif isinstance(error, SwarmOptimizationError):
        return ErrorSeverity.MEDIUM
    elif isinstance(error, (ReinforcementLearningError, QuantumCognitionError)):
        return ErrorSeverity.HIGH
    elif isinstance(error, MetaStrategyError):
        return ErrorSeverity.CRITICAL
    else:
        return ErrorSeverity.MEDIUM
