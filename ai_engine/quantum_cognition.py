# ai_engine/quantum_cognition.py

import numpy as np
import logging
from utils.ai_error_handler import handle_errors, QuantumCognitionError
from ai_engine.core.base_layer import BaseLayer
from dotenv import load_dotenv
import os

# Ortam değişkenlerini yükleme
load_dotenv()

# Ortam değişkenleri
QUTRIT_COUNT = int(os.getenv("QUTRIT_COUNT", 512))
ENTANGLEMENT_STRENGTH = float(os.getenv("ENTANGLEMENT_STRENGTH", 0.5))
SUPPOSITION_INTENSITY = float(os.getenv("SUPPOSITION_INTENSITY", 0.7))

# Log yapılandırması
logger = logging.getLogger("QuantumCognition")

# Qutrit Nöron Sınıfı
class QutritNeuron:
    def __init__(self):
        self.state = np.random.choice([-1, 0, 1])  # Üç olası durum

    def superpose(self):
        """Süperpozisyon: Qutrit rastgele bir kuantum durumuna geçer."""
        self.state = np.random.choice([-1, 0, 1], p=[SUPPOSITION_INTENSITY / 2, 1 - SUPPOSITION_INTENSITY, SUPPOSITION_INTENSITY / 2])

    def measure(self):
        """Ölçüm: Karar vermek için mevcut durumu belirler."""
        return self.state

# Quantum Cognition Katmanı
class QuantumCognition(BaseLayer):
    def __init__(self):
        super().__init__("Quantum Cognition")
        self.qutrits = [QutritNeuron() for _ in range(QUTRIT_COUNT)]
        self.entanglement_matrix = np.zeros((QUTRIT_COUNT, QUTRIT_COUNT))

    @handle_errors
    def initialize(self):
        logger.info("Quantum Cognition başlatıldı.")
        self._initialize_entanglement()

    def _initialize_entanglement(self):
        """Qutritler arasında kuantum dolanıklık matrisini başlatır."""
        for i in range(QUTRIT_COUNT):
            for j in range(i + 1, QUTRIT_COUNT):
                self.entanglement_matrix[i][j] = np.random.uniform(0, ENTANGLEMENT_STRENGTH)
                self.entanglement_matrix[j][i] = self.entanglement_matrix[i][j]  # Simetrik matris

    @handle_errors
    def process(self, market_data):
        """Kuantum karar süreci."""
        logger.info("Süperpozisyon başlatıldı.")
        for qutrit in self.qutrits:
            qutrit.superpose()
        
        logger.info("Entanglement işlemleri uygulanıyor.")
        self._apply_entanglement()

        decisions = [qutrit.measure() for qutrit in self.qutrits]
        final_decision = self._aggregate_decisions(decisions, market_data)
        logger.info(f"Quantum Karar Alındı: {final_decision}")
        return final_decision

    def _apply_entanglement(self):
        """Qutritler arasındaki dolanıklık etkilerini uygular."""
        for i in range(QUTRIT_COUNT):
            for j in range(i + 1, QUTRIT_COUNT):
                influence = self.entanglement_matrix[i][j] * self.qutrits[j].state
                self.qutrits[i].state += influence

    def _aggregate_decisions(self, decisions, market_data):
        """Tüm kararları toplayarak piyasa koşullarına göre son karar verir."""
        weighted_decision = np.mean(decisions) + np.std(market_data) * 0.1
        if weighted_decision > 0.5:
            return "buy"
        elif weighted_decision < -0.5:
            return "sell"
        else:
            return "hold"

    @handle_errors
    def shutdown(self):
        logger.info("Quantum Cognition kapatılıyor...")

    def status_report(self):
        """Quantum Cognition için durum raporu."""
        report = super().status_report()
        active_states = [qutrit.state for qutrit in self.qutrits]
        report.update({
            "active_states_distribution": {
                "-1": active_states.count(-1),
                "0": active_states.count(0),
                "1": active_states.count(1)
            }
        })
        logger.info(f"Quantum Cognition Status: {report}")
        return report
