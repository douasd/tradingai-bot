# datafetch/historicaldatafetch.py

import os
import asyncio
import aiohttp
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum, auto
from typing import List, Optional
from aiolimiter import AsyncLimiter
import logging
import hashlib
import zipfile
import io
import pyarrow.parquet as pq
import pyarrow as pa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import gzip
from dotenv import load_dotenv
from utils.error_handler import handle_errors, retry, DataFetchError, NetworkError, RetryLimitExceeded

# Ortam Değişkenlerini Yükleme
load_dotenv()

# Ortam Değişkenleri
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
API_RATE_LIMIT = int(os.getenv("API_RATE_LIMIT", 100))
HISTORICAL_DATA_PATH = os.getenv("HISTORICAL_DATA_PATH", "data/historical")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
ENV_MODE = os.getenv("ENV_MODE", "development")
NODE_ID = os.getenv("NODE_ID", "default-node")

# Log Yapılandırması
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(f'logs/historical_data_{ENV_MODE}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('HistoricalDataFetcher')

# Enum Sınıfları
class Symbol(Enum):
    BTCUSDT = "BTCUSDT"
    SOLUSDT = "SOLUSDT"
    ETHUSDT = "ETHUSDT"

class DataType(Enum):
    KLINES = "klines"
    INDEX_PRICE_KLINES = "indexPriceKlines"
    MARK_PRICE_KLINES = "markPriceKlines"
    PREMIUM_INDEX_KLINES = "premiumIndexKlines"

class KlineInterval(Enum):
    _1M = "1m"
    _5M = "5m"
    _15M = "15m"
    _1H = "1h"
    _4H = "4h"
    _1D = "1d"
    _1W = "1w"

class TimeInterval(Enum):
    DAILY = "daily"
    MONTHLY = "monthly"

# Ana Veri Çekici Sınıf
class HistoricalDataFetcher:
    BASE_URL = "https://data.binance.vision/data/futures/um"
    RETRY_DELAY = 2
    MAX_RETRIES = 5

    def __init__(self, symbol: Symbol, data_dir: str = HISTORICAL_DATA_PATH):
        self.symbol = symbol
        self.data_dir = Path(data_dir) / symbol.value
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.session = aiohttp.ClientSession()
        self.limiter = AsyncLimiter(API_RATE_LIMIT, 1)
        self.cipher = AESGCM(ENCRYPTION_KEY.encode())

    @handle_errors
    async def fetch_all_data(self, start_date: datetime, end_date: Optional[datetime] = None):
        """Tüm veri türlerini ve intervalleri indir"""
        end_date = end_date or datetime.utcnow()
        date_ranges = self._generate_date_ranges(start_date, end_date)

        tasks = []
        for data_type in DataType:
            for interval in KlineInterval:
                for date in date_ranges:
                    tasks.append(
                        self.fetch_kline_data(data_type, interval, date)
                    )

        await asyncio.gather(*tasks)

    @handle_errors
    async def fetch_kline_data(self, data_type: DataType, interval: KlineInterval, date: datetime):
        """Kline verisini indirme ve işleme"""
        url = self._build_url(data_type, interval, date)
        local_path = self._get_local_path(data_type, interval, date)

        if local_path.exists():
            logger.info(f"{local_path} zaten mevcut, atlanıyor.")
            return

        for attempt in range(self.MAX_RETRIES):
            try:
                async with self.limiter:
                    logger.info(f"{url} indiriliyor...")
                    content = await retry(lambda: self._download_with_retry(url), retries=self.MAX_RETRIES)

                    if content:
                        df = self._process_kline_content(content, data_type, interval)
                        self._save_to_parquet(df, local_path)
                        logger.info(f"Veri başarıyla kaydedildi: {local_path}")
                    return
            except RetryLimitExceeded:
                logger.error(f"{url} {self.MAX_RETRIES} denemede başarısız oldu.")
                break

    async def _download_with_retry(self, url: str) -> Optional[bytes]:
        """Retry mekanizmalı dosya indirme"""
        async with self.session.get(url) as response:
            response.raise_for_status()
            return await response.read()

    def _build_url(self, data_type: DataType, interval: KlineInterval, date: datetime) -> str:
        filename = f"{self.symbol.value}-{data_type.value}-{interval.value}-{date.strftime('%Y-%m-%d')}.zip"
        return f"{self.BASE_URL}/{TimeInterval.DAILY.value}/{data_type.value}/{filename}"

    def _get_local_path(self, data_type: DataType, interval: KlineInterval, date: datetime) -> Path:
        path = self.data_dir / data_type.value / interval.value
        path.mkdir(parents=True, exist_ok=True)
        return path / f"{date.strftime('%Y-%m-%d')}.parquet.gz"

    def _process_kline_content(self, content: bytes, data_type: DataType, interval: KlineInterval) -> pd.DataFrame:
        """İndirilen KLINE verisini işleme"""
        with zipfile.ZipFile(io.BytesIO(content)) as z:
            csv_file = [f for f in z.namelist() if f.endswith('.csv')][0]
            with z.open(csv_file) as f:
                df = pd.read_csv(f)

        df.columns = ['open_time', 'open', 'high', 'low', 'close', 'volume',
                      'close_time', 'quote_volume', 'count', 'taker_buy_volume',
                      'taker_buy_quote_volume', 'ignore']
        df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
        df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
        df['hlc3'] = (df['high'] + df['low'] + df['close']) / 3
        df['variance'] = df['high'] - df['low']

        return df

    def _save_to_parquet(self, df: pd.DataFrame, local_path: Path):
        """Veriyi sıkıştırılmış ve şifrelenmiş olarak kaydetme"""
        encrypted_data = self._encrypt_data(df.to_parquet(index=False))
        compressed_data = gzip.compress(encrypted_data)
        with open(local_path, 'wb') as f:
            f.write(compressed_data)

    def _encrypt_data(self, data: bytes) -> bytes:
        nonce = os.urandom(12)
        return nonce + self.cipher.encrypt(nonce, data, None)

    def _generate_date_ranges(self, start: datetime, end: datetime) -> List[datetime]:
        """Veri için tarih aralıklarını oluştur"""
        dates = []
        current = start
        while current <= end:
            dates.append(current)
            current += timedelta(days=1)
        return dates

    async def close(self):
        await self.session.close()

# Ana Çalıştırma Fonksiyonu
async def main():
    fetcher = HistoricalDataFetcher(Symbol.BTCUSDT)
    try:
        start_date = datetime(2020, 1, 1)
        await fetcher.fetch_all_data(start_date)
    finally:
        await fetcher.close()

if __name__ == "__main__":
    asyncio.run(main())
