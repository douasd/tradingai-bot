# tradingai-bot/processor/data_processor.py

import os
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from ta import add_all_ta_features
from sklearn.preprocessing import MinMaxScaler, StandardScaler
import logging
import json
from utils.processor_error_handler import handle_errors, ProcessorDataError, MissingDataError, InvalidDataError

# Ortam Değişkenlerini Yükleme
load_dotenv()

# Ortam Değişkenleri
PROCESSED_DATA_PATH = os.getenv("PROCESSED_DATA_PATH", "data/processed")
HISTORICAL_DATA_PATH = os.getenv("HISTORICAL_DATA_PATH", "data/historical")
REALTIME_DATA_PATH = os.getenv("REALTIME_DATA_PATH", "data/realtime")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Log Yapılandırması
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(f"logs/data_processor_{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("DataProcessor")

# ================================
# 📊 Veri Temizleme ve Hazırlama
# ================================

class DataProcessor:
    def __init__(self):
        self.historical_data_path = Path(HISTORICAL_DATA_PATH)
        self.realtime_data_path = Path(REALTIME_DATA_PATH)
        self.processed_data_path = Path(PROCESSED_DATA_PATH)
        self.processed_data_path.mkdir(parents=True, exist_ok=True)

    @handle_errors
    def load_data(self, file_path: Path) -> pd.DataFrame:
        """Verileri okur ve temizlenmiş bir DataFrame döndürür"""
        if not file_path.exists():
            raise MissingDataError(f"{file_path} bulunamadı.")
        
        logger.info(f"{file_path} yükleniyor...")
        df = pd.read_parquet(file_path)
        df = self._clean_data(df)
        return df

    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Veri temizleme işlemleri"""
        if df.isnull().sum().sum() > 0:
            logger.warning("Eksik veriler tespit edildi, dolduruluyor...")
            df.fillna(method='ffill', inplace=True)
            df.fillna(method='bfill', inplace=True)
        
        if df.duplicated().any():
            logger.warning("Yinelenen veriler tespit edildi ve kaldırıldı.")
            df.drop_duplicates(inplace=True)
        
        if not pd.api.types.is_datetime64_any_dtype(df['open_time']):
            df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')

        df.set_index('open_time', inplace=True)
        return df

    # ================================
    # 📈 Teknik Göstergeler Hesaplama
    # ================================

    @handle_errors
    def compute_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Tüm teknik göstergeleri hesaplar"""
        logger.info("Teknik göstergeler hesaplanıyor...")
        df = add_all_ta_features(
            df, open="open", high="high", low="low", close="close", volume="volume", fillna=True
        )
        logger.info("Teknik göstergeler hesaplandı.")
        return df

    # ================================
    # 🔍 Veri Dönüşümü ve Ölçekleme
    # ================================

    @handle_errors
    def normalize_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Veriyi normalize eder"""
        logger.info("Veri normalize ediliyor...")
        scaler = MinMaxScaler()
        scaled_values = scaler.fit_transform(df.select_dtypes(include=[np.number]))
        df_scaled = pd.DataFrame(scaled_values, index=df.index, columns=df.select_dtypes(include=[np.number]).columns)
        logger.info("Veri normalizasyonu tamamlandı.")
        return df_scaled

    # ================================
    # 💾 Veriyi Kaydetme
    # ================================

    @handle_errors
    def save_processed_data(self, df: pd.DataFrame, filename: str):
        """İşlenmiş verileri kaydeder"""
        file_path = self.processed_data_path / f"{filename}.parquet"
        df.to_parquet(file_path, compression="zstd")
        logger.info(f"İşlenmiş veri kaydedildi: {file_path}")

    # ================================
    # 🚀 İşleme Akışı
    # ================================

    def process_all_data(self):
        """Tüm veri işleme akışı"""
        logger.info("Veri işleme süreci başlatıldı...")

        # Tüm tarihsel verileri işleme
        for file in self.historical_data_path.glob("**/*.parquet"):
            df = self.load_data(file)
            df = self.compute_technical_indicators(df)
            df = self.normalize_data(df)
            self.save_processed_data(df, file.stem)

        # Tüm gerçek zamanlı verileri işleme
        for file in self.realtime_data_path.glob("**/*.json.gz"):
            df = self.load_data(file)
            df = self.compute_technical_indicators(df)
            df = self.normalize_data(df)
            self.save_processed_data(df, file.stem)

        logger.info("Veri işleme tamamlandı.")


# =======================================
# 🚀 Ana Çalıştırma Fonksiyonu
# =======================================

if __name__ == "__main__":
    processor = DataProcessor()
    processor.process_all_data()
