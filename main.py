# main.py

import os
import logging
import asyncio
from dotenv import load_dotenv
from data.historicaldatafetch import BinanceHistoricalFetcher
from data.realtimedatafetch import QuantumRealTimeFetcher
from processor.data_processor import DataProcessor
from ai_engine.swarm_intelligence import QuantumSwarm
from ai_engine.reinforcement_core import ReinforcementCore
from ai_engine.quantum_cognition import QuantumCognition
from ai_engine.meta_strategy import MetaStrategy
from execution.execution_engine import ExecutionEngine
from execution.execution_error_handler import handle_execution_errors

# Ortam değişkenlerini yükle
load_dotenv()

# Log yapılandırması
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('GodModeMain')

# Sistem Bileşenlerini Başlat
@handle_execution_errors
async def initialize_system():
    logger.info("📡 Sistemi başlatıyorum...")
    # Veri çekme modülleri
    historical_fetcher = BinanceHistoricalFetcher(symbol="BTCUSDT")
    realtime_fetcher = QuantumRealTimeFetcher()

    # Veri işleme modülü
    data_processor = DataProcessor()

    # AI katmanları başlatılıyor
    logger.info("🤖 AI Katmanları başlatılıyor...")
    swarm_ai = QuantumSwarm()
    reinforcement_ai = ReinforcementCore()
    quantum_cognition = QuantumCognition()

    # Meta-strateji motoru
    meta_strategy = MetaStrategy(swarm_ai, reinforcement_ai, quantum_cognition)

    # Execution Engine
    execution_engine = ExecutionEngine()

    logger.info("✅ Tüm sistem başlatıldı.")

    return {
        'historical_fetcher': historical_fetcher,
        'realtime_fetcher': realtime_fetcher,
        'data_processor': data_processor,
        'meta_strategy': meta_strategy,
        'execution_engine': execution_engine
    }

# Ana döngü
@handle_execution_errors
async def main():
    system = await initialize_system()

    # Tarihsel verileri işleme
    logger.info("🗂️ Tarihsel veriler işleniyor...")
    await system['historical_fetcher'].fetch_all_data(start_date='2020-01-01')

    # Gerçek zamanlı veri akışı başlatma
    logger.info("🚀 Gerçek zamanlı veri akışı başlatılıyor...")
    realtime_data = await system['realtime_fetcher'].fetch()

    # Sürekli veri işleme ve karar verme döngüsü
    logger.info("🔄 Veri işleme ve strateji yürütme başlıyor...")
    async for data in realtime_data:
        processed_data = system['data_processor'].process(data)
        decision = system['meta_strategy'].generate_strategy(processed_data)
        execution_result = system['execution_engine'].run(decision)
        logger.info(f"🎯 İşlem sonucu: {execution_result}")

# Programı Çalıştır
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Sistem kapatılıyor...")
