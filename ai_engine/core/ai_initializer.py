# ai_engine/core/ai_initializer.py

import asyncio
import logging
import os
import psutil
import time
from dotenv import load_dotenv
from ai_engine.meta_strategy import MetaStrategyOrchestrator
from ai_engine.core.data_manager import DataManager
from ai_engine.swarm_intelligence import QuantumSwarm
from ai_engine.reinforcement_core import ReinforcementLearningCore
from ai_engine.quantum_cognition import QuantumCognition
from utils.ai_error_handler import handle_errors, AIError

# Ortam değişkenlerini yükleme
load_dotenv()

# Log yapılandırması
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/ai_strategy.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AI_Initializer")

class AIInitializer:
    def __init__(self):
        self.data_manager = DataManager()
        self.meta_orchestrator = MetaStrategyOrchestrator()
        self.swarm = QuantumSwarm()
        self.reinforcement = ReinforcementLearningCore()
        self.quantum_cognition = QuantumCognition()
        self.running = True

    @handle_errors
    async def health_check(self):
        """Sistem kaynaklarını kontrol eder."""
        while self.running:
            cpu_usage = psutil.cpu_percent(interval=1)
            memory_usage = psutil.virtual_memory().percent
            logger.info(f"CPU Kullanımı: {cpu_usage}% | RAM Kullanımı: {memory_usage}%")
            await asyncio.sleep(10)

    @handle_errors
    async def anomaly_detection(self):
        """Veri akışı ve işlem sırasında anomali tespiti yapar."""
        while self.running:
            data = self.data_manager.get_latest_data()
            if data.isnull().any().any():
                logger.warning("Anomali Tespit Edildi: Eksik veri!")
            await asyncio.sleep(5)

    @handle_errors
    async def restart_on_failure(self, task_name, task_function):
        """Kritik hata oluşursa ilgili modülü yeniden başlatır."""
        while self.running:
            try:
                await task_function()
            except AIError as e:
                logger.error(f"{task_name} hata ile karşılaştı: {str(e)}. Yeniden başlatılıyor...")
                await asyncio.sleep(5)  # Yeniden başlatma öncesi kısa gecikme

    @handle_errors
    async def start_ai_system(self):
        """AI Motorunu başlatır ve tüm görevleri eş zamanlı yürütür."""
        logger.info("AI Strateji Motoru başlatılıyor...")
        self.data_manager.load_data()
        
        tasks = [
            asyncio.create_task(self.health_check()),
            asyncio.create_task(self.anomaly_detection()),
            asyncio.create_task(self.restart_on_failure("Swarm Intelligence", self.swarm.optimize_strategy)),
            asyncio.create_task(self.restart_on_failure("Reinforcement Learning", self.reinforcement.train)),
            asyncio.create_task(self.restart_on_failure("Quantum Cognition", self.quantum_cognition.run_decision_process)),
            asyncio.create_task(self.restart_on_failure("Meta-Strategy Orchestrator", self.meta_orchestrator.run))
        ]

        await asyncio.gather(*tasks)

    def stop(self):
        """Sistemi kapatır."""
        self.running = False
        logger.info("AI Strateji Motoru durduruluyor...")

# Ana çalıştırma fonksiyonu
if __name__ == "__main__":
    initializer = AIInitializer()
    try:
        asyncio.run(initializer.start_ai_system())
    except KeyboardInterrupt:
        initializer.stop()
        logger.info("Kullanıcı tarafından durduruldu.")
