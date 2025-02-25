# ai_engine/reinforcement_core.py

import numpy as np
import logging
from utils.ai_error_handler import handle_errors, ReinforcementLearningError
from ai_engine.core.base_layer import BaseLayer
from dotenv import load_dotenv
import os

# Ortam değişkenlerini yükleme
load_dotenv()

# Ortam değişkenleri
DISCOUNT_FACTOR = float(os.getenv("DISCOUNT_FACTOR", 0.95))
LEARNING_RATE = float(os.getenv("LEARNING_RATE", 0.01))
EXPLORATION_RATE = float(os.getenv("EXPLORATION_RATE", 0.1))
EXPLORATION_DECAY = float(os.getenv("EXPLORATION_DECAY", 0.995))
ARENA_COUNT = int(os.getenv("ARENA_COUNT", 5))

# Log yapılandırması
logger = logging.getLogger("ReinforcementLearningCore")

class ReinforcementLearningCore(BaseLayer):
    def __init__(self):
        super().__init__("Reinforcement Learning Core")
        self.q_table = {}
        self.exploration_rate = EXPLORATION_RATE

    @handle_errors
    def initialize(self):
        logger.info("Reinforcement Learning Core başlatıldı.")

    @handle_errors
    def process(self, market_environment):
        """Multi-Arena Eğitim ve Portföy Simülasyonu"""
        logger.info(f"{ARENA_COUNT} arena ile eğitim başlatıldı.")
        for arena_id in range(ARENA_COUNT):
            logger.info(f"Arena {arena_id+1} eğitim ortamı başlatıldı.")
            self._train_in_arena(market_environment)
        logger.info("Multi-arena eğitimi tamamlandı.")

    def _train_in_arena(self, market_environment):
        state = market_environment.reset()
        done = False
        while not done:
            action = self._choose_action(state)
            next_state, reward, done, info = market_environment.step(action)
            self._update_q_table(state, action, reward, next_state)
            state = next_state

    def _choose_action(self, state):
        """Eylem seçim mekanizması (Epsilon-Greedy)"""
        if np.random.uniform(0, 1) < self.exploration_rate:
            return np.random.choice(["buy", "sell", "hold"])
        else:
            return max(self.q_table.get(state, {}), key=self.q_table.get(state, {}).get, default="hold")

    def _update_q_table(self, state, action, reward, next_state):
        """Q-Table güncellemesi"""
        if state not in self.q_table:
            self.q_table[state] = {}
        if action not in self.q_table[state]:
            self.q_table[state][action] = 0

        max_future_reward = max(self.q_table.get(next_state, {}).values(), default=0)
        new_value = (1 - LEARNING_RATE) * self.q_table[state][action] + LEARNING_RATE * (reward + DISCOUNT_FACTOR * max_future_reward)
        self.q_table[state][action] = new_value
        logger.info(f"State: {state}, Action: {action}, Reward: {reward}, Updated Q-Value: {new_value}")

    @handle_errors
    def calculate_reward(self, sharpe_ratio, omega_ratio, fomo_penalty, regret_minimization):
        """Risk ayarlı ödül hesaplaması"""
        risk_adjusted = sharpe_ratio * omega_ratio
        behavioral = fomo_penalty * regret_minimization
        quantum_randomness = np.random.uniform(0, 1)  # Kuantum rastgelelik simülasyonu
        reward = risk_adjusted + behavioral + quantum_randomness
        logger.info(f"Reward Hesaplandı: {reward:.4f}")
        return reward

    @handle_errors
    def simulate_flash_crash(self, market_environment):
        """Ani piyasa çöküşlerini simüle eder."""
        logger.info("Flash Crash Senaryosu başlatıldı.")
        market_environment.simulate_crash()
        logger.info("Flash Crash tamamlandı.")

    @handle_errors
    def shutdown(self):
        logger.info("Reinforcement Learning Core kapatılıyor...")

    def status_report(self):
        """Reinforcement Learning Core için durum raporu."""
        report = super().status_report()
        report.update({
            "exploration_rate": self.exploration_rate,
            "total_states_tracked": len(self.q_table)
        })
        logger.info(f"RL Core Status: {report}")
        return report
