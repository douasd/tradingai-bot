# ai_engine/core/base_layer.py

import logging
from abc import ABC, abstractmethod
import time
from utils.ai_error_handler import handle_errors, BaseLayerError

# Log yapılandırması
logger = logging.getLogger("BaseLayer")

class BaseLayer(ABC):
    """
    Tüm AI katmanlarının temel sınıfı.
    Genişletilebilir ve soyut metotlarla her katmana özel işlevsellik sağlar.
    """
    def __init__(self, name):
        self.name = name
        self.is_active = False
        self.last_execution_time = None
        logger.info(f"{self.name} katmanı başlatıldı.")

    @abstractmethod
    def initialize(self):
        """Katmanın başlangıç işlemlerini başlatır."""
        pass

    @abstractmethod
    def process(self, data):
        """Veri işleme işlevi. Tüm katmanlar tarafından özelleştirilir."""
        pass

    @abstractmethod
    def shutdown(self):
        """Katmanı güvenli bir şekilde kapatır."""
        pass

    @handle_errors
    def run(self, data):
        """
        Katmanı çalıştırır, işlemleri zamanlar ve hata yönetimi uygular.
        """
        try:
            self.is_active = True
            self.last_execution_time = time.time()
            logger.info(f"{self.name} katmanı çalışıyor...")
            result = self.process(data)
            execution_duration = time.time() - self.last_execution_time
            logger.info(f"{self.name} işlemi tamamlandı. Süre: {execution_duration:.2f} saniye.")
            return result
        except BaseLayerError as e:
            logger.error(f"{self.name} katmanında hata: {str(e)}")
        finally:
            self.is_active = False
            self.shutdown()

    def status_report(self):
        """
        Katmanın mevcut durumunu raporlar.
        """
        status = "Aktif" if self.is_active else "Pasif"
        logger.info(f"{self.name} Katman Durumu: {status} | Son Çalışma: {self.last_execution_time}")
        return {
            "name": self.name,
            "is_active": self.is_active,
            "last_execution_time": self.last_execution_time
        }
