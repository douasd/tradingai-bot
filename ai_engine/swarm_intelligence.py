# ai_engine/swarm_intelligence.py

import numpy as np
import logging
from utils.ai_error_handler import handle_errors, SwarmOptimizationError
from ai_engine.core.base_layer import BaseLayer
from dotenv import load_dotenv
import os

# Ortam değişkenlerini yükleme
load_dotenv()

# Ortam değişkenleri
PARTICLE_COUNT = int(os.getenv("PARTICLE_COUNT", 1024))
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", 1000))
CONVERGENCE_THRESHOLD = float(os.getenv("CONVERGENCE_THRESHOLD", 0.0001))

# Log yapılandırması
logger = logging.getLogger("SwarmIntelligence")

# Qubit Partikül Yapısı
class QubitParticle:
    def __init__(self):
        self.position = np.random.uniform(-1, 1)
        self.velocity = np.random.uniform(-0.1, 0.1)
        self.best_position = self.position
        self.best_fitness = -np.inf

# Klein Bottle Topolojisi
class KleinBottleTopology:
    @staticmethod
    def wrap_position(position):
        """Klein Şişesi topolojisine göre pozisyonu günceller."""
        return np.mod(position + 1, 2) - 1  # Değerleri -1 ile 1 arasında tutar

# Quantum Swarm Intelligence Katmanı
class QuantumSwarm(BaseLayer):
    def __init__(self):
        super().__init__("Swarm Intelligence")
        self.particles = [QubitParticle() for _ in range(PARTICLE_COUNT)]
        self.global_best_position = None
        self.global_best_fitness = -np.inf

    @handle_errors
    def initialize(self):
        logger.info("Swarm Intelligence başlatıldı.")

    @handle_errors
    def process(self, fitness_fn):
        logger.info(f"{PARTICLE_COUNT} parçacık ile optimizasyon başlatıldı.")
        iteration = 0
        while iteration < MAX_ITERATIONS:
            for particle in self.particles:
                # Fitness hesapla
                fitness = fitness_fn(particle.position)

                # Parçacığın en iyi konumu güncelle
                if fitness > particle.best_fitness:
                    particle.best_fitness = fitness
                    particle.best_position = particle.position

                # Küresel en iyi konumu güncelle
                if fitness > self.global_best_fitness:
                    self.global_best_fitness = fitness
                    self.global_best_position = particle.position

                # Quantum entanglement ve hareket güncellemesi
                self._update_particle(particle)

            logger.info(f"Iterasyon {iteration+1}: En iyi fitness {self.global_best_fitness:.5f}")
            
            # Erken durdurma koşulu
            if abs(self.global_best_fitness) < CONVERGENCE_THRESHOLD:
                logger.info("Erken durdurma koşulu sağlandı.")
                break
            iteration += 1

        logger.info("Optimizasyon tamamlandı.")
        return self.global_best_position

    def _update_particle(self, particle):
        """Parçacık hareket güncellemesi ve kuantum entanglement uygulanması."""
        random_influence = np.random.uniform(-0.1, 0.1)
        global_influence = (self.global_best_position - particle.position) * np.random.random()
        particle.velocity = 0.7 * particle.velocity + random_influence + global_influence
        particle.position += particle.velocity
        particle.position = KleinBottleTopology.wrap_position(particle.position)

    @handle_errors
    def shutdown(self):
        logger.info("Swarm Intelligence kapanıyor...")

    def entangle_particles(self):
        """Parçacıklar arasında kuantum dolanıklık oluşturur."""
        for i in range(len(self.particles) - 1):
            self.particles[i].position = (self.particles[i].position + self.particles[i+1].position) / 2

    def status_report(self):
        """Swarm Intelligence katmanı için durum raporu."""
        report = super().status_report()
        report.update({
            "global_best_fitness": self.global_best_fitness,
            "global_best_position": self.global_best_position
        })
        logger.info(f"Swarm Status: {report}")
        return report
