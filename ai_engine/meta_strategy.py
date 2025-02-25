# ai_engine/meta_strategy.py

import logging
from utils.ai_error_handler import handle_errors, MetaStrategyError
from ai_engine.swarm_intelligence import QuantumSwarm
from ai_engine.reinforcement_core import ReinforcementLearningCore
from ai_engine.quantum_cognition import QuantumCognition
from ai_engine.core.base_layer import BaseLayer
from dotenv import load_dotenv
import os

# Ortam değişkenlerini yükleme
load_dotenv()

# Ortam değişkenleri
SWARM_WEIGHT = float(os.getenv("SWARM_WEIGHT", 0.3))
REINFORCEMENT_WEIGHT = float(os.getenv("REINFORCEMENT_WEIGHT", 0.4))
QUANTUM_WEIGHT = float(os.getenv("QUANTUM_WEIGHT", 0.3))
RISK_TOLERANCE = float(os.getenv("RISK_TOLERANCE", 0.5))

# Log yapılandırması
logger = logging.getLogger("MetaStrategyOrchestrator")

# Meta-Strategy Orchestrator Katmanı
class MetaStrategyOrchestrator(BaseLayer):
    def __init__(self):
        super().__init__("Meta Strategy Orchestrator")
        self.swarm = QuantumSwarm()
        self.reinforcement = ReinforcementLearningCore()
        self.quantum = QuantumCognition()

    @handle_errors
    def initialize(self):
        logger.info("Meta Strategy Orchestrator başlatıldı.")
        self.swarm.initialize()
        self.reinforcement.initialize()
        self.quantum.initialize()

    @handle_errors
    def process(self, market_data):
        """Tüm AI katmanlarından gelen kararların ağırlıklı ortalamasını hesaplar."""
        logger.info("Katmanlardan kararlar toplanıyor.")
        swarm_decision = self.swarm.process(lambda x: x)  # Dummy fitness function
        reinforcement_decision = self.reinforcement.process(market_data)
        quantum_decision = self.quantum.process(market_data)

        logger.info("Kararlar ağırlıklı olarak birleştiriliyor.")
        final_decision = self._aggregate_decisions(swarm_decision, reinforcement_decision, quantum_decision)
        logger.info(f"Meta Strategy Nihai Kararı: {final_decision}")
        return final_decision

    def _aggregate_decisions(self, swarm, reinforcement, quantum):
        """Kararları birleştirerek nihai stratejiyi oluşturur."""
        decision_map = {"buy": 1, "hold": 0, "sell": -1}
        total_score = (
            decision_map.get(swarm, 0) * SWARM_WEIGHT +
            decision_map.get(reinforcement, 0) * REINFORCEMENT_WEIGHT +
            decision_map.get(quantum, 0) * QUANTUM_WEIGHT
        )

        if total_score > RISK_TOLERANCE:
            return "buy"
        elif total_score < -RISK_TOLERANCE:
            return "sell"
        else:
            return "hold"

    @handle_errors
    def shutdown(self):
        logger.info("Meta Strategy Orchestrator kapatılıyor...")
        self.swarm.shutdown()
        self.reinforcement.shutdown()
        self.quantum.shutdown()

    def status_report(self):
        """Meta Strategy Orchestrator için durum raporu."""
        report = super().status_report()
        report.update({
            "swarm_status": self.swarm.status_report(),
            "reinforcement_status": self.reinforcement.status_report(),
            "quantum_status": self.quantum.status_report()
        })
        logger.info(f"Meta Strategy Status: {report}")
        return report
