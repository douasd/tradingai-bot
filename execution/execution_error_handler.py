# execution/execution_error_handler.py

import logging
import time
import functools
from enum import Enum, auto
import requests
import os
from dotenv import load_dotenv

# Ortam değişkenlerini yükleme
load_dotenv()

# Ortam değişkenleri
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
RETRY_LIMIT = int(os.getenv("RETRY_LIMIT", 3))
RETRY_DELAY = int(os.getenv("RETRY_DELAY", 5))

# Log yapılandırması
logger = logging.getLogger("ExecutionErrorHandler")
logger.setLevel(logging.INFO)

# Hata Öncelik Seviyeleri
class ExecutionErrorSeverity(Enum):
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    CRITICAL = auto()

# Özel Hata Sınıfları
class ExecutionError(Exception):
    pass

class OrderExecutionError(ExecutionError):
    pass

class RiskManagementError(ExecutionError):
    pass

class CircuitBreakerError(ExecutionError):
    pass

# Hata Yönetim Dekoratörü
def handle_execution_errors(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        retries = 0
        while retries < RETRY_LIMIT:
            try:
                return func(*args, **kwargs)
            except ExecutionError as e:
                severity = classify_execution_error(e)
                logger.error(f"Hata [{severity.name}]: {str(e)} - {func.__name__}")
                send_telegram_alert(f"🚨 [{severity.name}] Execution Error: {str(e)} - Function: {func.__name__}")
                if severity == ExecutionErrorSeverity.CRITICAL:
                    logger.critical(f"Kritik hata tespit edildi, işlem durduruluyor.")
                    raise e
                retries += 1
                time.sleep(RETRY_DELAY)
            except Exception as e:
                logger.error(f"Beklenmeyen Hata: {str(e)} - {func.__name__}")
                send_telegram_alert(f"❌ Beklenmeyen Hata: {str(e)} - Function: {func.__name__}")
                raise e

        logger.error(f"{func.__name__} fonksiyonu {RETRY_LIMIT} deneme sonrası başarısız oldu.")
        send_telegram_alert(f"❌ {func.__name__} fonksiyonu {RETRY_LIMIT} deneme sonrası başarısız oldu.")
    return wrapper

# Hata Öncelik Sınıflandırma Fonksiyonu
def classify_execution_error(error):
    if isinstance(error, OrderExecutionError):
        return ExecutionErrorSeverity.MEDIUM
    elif isinstance(error, RiskManagementError):
        return ExecutionErrorSeverity.HIGH
    elif isinstance(error, CircuitBreakerError):
        return ExecutionErrorSeverity.CRITICAL
    else:
        return ExecutionErrorSeverity.LOW

# Telegram Bildirim Fonksiyonu
def send_telegram_alert(message):
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        try:
            requests.post(url, data=payload)
        except Exception as e:
            logger.error(f"Telegram bildirimi başarısız: {str(e)}")
