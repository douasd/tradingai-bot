# datafetch/realtimedatafetch.py

import os
import asyncio
import aiohttp
import pandas as pd
import numpy as np
from datetime import datetime
from enum import Enum, auto
from aiolimiter import AsyncLimiter
import logging
from pathlib import Path
import json
import gzip
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from dotenv import load_dotenv
from utils.error_handler import handle_errors, retry, DataFetchError, NetworkError, RetryLimitExceeded
from websockets.client import connect
from websockets.exceptions import ConnectionClosed, PayloadTooBig

# Ortam Değişkenlerini Yükleme
load_dotenv()

# Ortam Değişkenleri
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
API_RATE_LIMIT = int(os.getenv("API_RATE_LIMIT", 100))
REALTIME_DATA_PATH = os.getenv("REALTIME_DATA_PATH", "data/realtime")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
ENV_MODE = os.getenv("ENV_MODE", "development")
NODE_ID = os.getenv("NODE_ID", "default-node")

# Log Yapılandırması
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(f'logs/realtime_data_{ENV_MODE}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('RealTimeFetcher')

# Enum Sınıfları
class Exchange(Enum):
    BINANCE = auto()
    BYBIT = auto()
    OKX = auto()
    KRAKEN = auto()
    DERIBIT = auto()

class DataType(Enum):
    BOOK_DEPTH = auto()
    TRADES = auto()
    FUNDING_RATE = auto()

class Symbol(Enum):
    BTCUSDT = auto()
    ETHUSDT = auto()
    SOLUSDT = auto()

# Ana Veri Çekici Sınıf
class RealTimeDataFetcher:
    def __init__(self):
        self.sessions = self._init_sessions()
        self.limiter = AsyncLimiter(API_RATE_LIMIT, 1)
        self.cipher = AESGCM(ENCRYPTION_KEY.encode())
        self.realtime_data_path = Path(REALTIME_DATA_PATH)
        self.realtime_data_path.mkdir(parents=True, exist_ok=True)

    def _init_sessions(self):
        return {
            exchange: aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(limit=100, ssl=False),
                headers={'User-Agent': 'RealTimeFetcher'},
                timeout=aiohttp.ClientTimeout(total=10)
            ) for exchange in Exchange
        }

    @handle_errors
    async def fetch_data(self, exchange: Exchange, data_type: DataType, symbol: Symbol):
        """Gerçek zamanlı veri akışı başlatma"""
        ws_url = self._get_ws_endpoint(exchange)
        stream_name = self._get_stream_name(data_type, symbol)

        try:
            async with connect(f"{ws_url}/{stream_name}") as ws:
                logger.info(f"{exchange.name} üzerinde {symbol.name} için {data_type.name} verisi dinleniyor...")
                while True:
                    try:
                        raw = await ws.recv()
                        decrypted_data = self._decrypt_data(raw)
                        await self._process_data(decrypted_data, exchange, data_type, symbol)
                    except (ConnectionClosed, PayloadTooBig) as e:
                        logger.warning(f"Bağlantı hatası: {str(e)} - Yeniden bağlanıyor...")
                        await asyncio.sleep(2)
                        break
        except Exception as e:
            logger.error(f"{exchange.name} veri akışı başarısız: {str(e)}")

    def _get_ws_endpoint(self, exchange: Exchange) -> str:
        endpoints = {
            Exchange.BINANCE: "wss://fstream.binance.com/ws",
            Exchange.BYBIT: "wss://stream.bybit.com/realtime",
            Exchange.OKX: "wss://ws.okx.com:8443/ws/v5/public",
            Exchange.KRAKEN: "wss://ws.kraken.com",
            Exchange.DERIBIT: "wss://www.deribit.com/ws/api/v2"
        }
        return endpoints[exchange]

    def _get_stream_name(self, data_type: DataType, symbol: Symbol) -> str:
        symbol_map = {
            Symbol.BTCUSDT: "btcusdt",
            Symbol.ETHUSDT: "ethusdt",
            Symbol.SOLUSDT: "solusdt"
        }
        stream_map = {
            DataType.BOOK_DEPTH: f"{symbol_map[symbol]}@depth",
            DataType.TRADES: f"{symbol_map[symbol]}@aggTrade",
            DataType.FUNDING_RATE: f"{symbol_map[symbol]}@fundingRate"
        }
        return stream_map[data_type]

    async def _process_data(self, data: dict, exchange: Exchange, data_type: DataType, symbol: Symbol):
        """Verileri işleme ve kaydetme"""
        timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
        file_path = self.realtime_data_path / f"{exchange.name}/{symbol.name}/{timestamp}.json.gz"
        file_path.parent.mkdir(parents=True, exist_ok=True)

        encrypted_data = self._encrypt_data(json.dumps(data).encode())
        compressed_data = gzip.compress(encrypted_data)

        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(compressed_data)

    def _encrypt_data(self, data: bytes) -> bytes:
        nonce = os.urandom(12)
        return nonce + self.cipher.encrypt(nonce, data, None)

    def _decrypt_data(self, data: bytes) -> dict:
        nonce = data[:12]
        decrypted = self.cipher.decrypt(nonce, data[12:], None)
        return json.loads(decrypted.decode())

    async def close(self):
        """Bağlantıları düzgün bir şekilde kapatma"""
        for session in self.sessions.values():
            await session.close()

# Ana Çalıştırma Fonksiyonu
async def main():
    fetcher = RealTimeDataFetcher()
    try:
        await asyncio.gather(
            fetcher.fetch_data(Exchange.BINANCE, DataType.BOOK_DEPTH, Symbol.BTCUSDT),
            fetcher.fetch_data(Exchange.BINANCE, DataType.TRADES, Symbol.ETHUSDT),
            fetcher.fetch_data(Exchange.BINANCE, DataType.FUNDING_RATE, Symbol.SOLUSDT)
        )
    finally:
        await fetcher.close()

if __name__ == "__main__":
    asyncio.run(main())
