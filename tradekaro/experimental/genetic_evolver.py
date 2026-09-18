"""
🧬 Genetic Algorithm Strategy Evolver — Evolve Trading Strategies

Breed, mutate, and select winning strategy parameters:
  - Population of strategy configs (RSI thresholds, SL/TP, etc.)
  - Fitness = Sharpe ratio from backtest
  - Crossover: combine best strategies
  - Mutation: random parameter tweaks
"""

import numpy as np
import random


class GeneticEvolver:
    
    GENE_RANGES = {
        'rsi_buy': (20, 40), 'rsi_sell': (60, 80),
        'stop_loss_pct': (0.5, 3.0), 'take_profit_pct': (1.0, 5.0),
        'confidence_threshold': (0.5, 0.8),
        'lookback': (20, 100), 'ema_fast': (5, 20), 'ema_slow': (20, 60),
    }
    
    def __init__(self, population_size=50, mutation_rate=0.1):
        self.pop_size = population_size
        self.mutation_rate = mutation_rate
        self.population = []
        self.generation = 0
        self.best_ever = None
    
    def initialize(self):
        self.population = [self._random_genes() for _ in range(self.pop_size)]
        self.generation = 0
    
    def evolve(self, fitness_func, generations=20):
        if not self.population: self.initialize()
        
        for gen in range(generations):
            scored = [(genes, fitness_func(genes)) for genes in self.population]
            scored.sort(key=lambda x: x[1], reverse=True)
            
            if not self.best_ever or scored[0][1] > self.best_ever[1]:
                self.best_ever = scored[0]
            
            # Select top 20% as parents
            top = [s[0] for s in scored[:self.pop_size // 5]]
            
            new_pop = list(top)  # Elitism
            while len(new_pop) < self.pop_size:
                p1, p2 = random.sample(top, 2)
                child = self._crossover(p1, p2)
                child = self._mutate(child)
                new_pop.append(child)
            
            self.population = new_pop
            self.generation += 1
        
        return {
            'best_genes': self.best_ever[0] if self.best_ever else None,
            'best_fitness': self.best_ever[1] if self.best_ever else 0,
            'generation': self.generation,
            'population_size': self.pop_size
        }
    
    def _random_genes(self):
        return {name: round(random.uniform(*rng), 2) for name, rng in self.GENE_RANGES.items()}
    
    def _crossover(self, p1, p2):
        child = {}
        for key in self.GENE_RANGES:
            child[key] = p1[key] if random.random() < 0.5 else p2[key]
        return child
    
    def _mutate(self, genes):
        for key, (lo, hi) in self.GENE_RANGES.items():
            if random.random() < self.mutation_rate:
                genes[key] = round(random.uniform(lo, hi), 2)
        return genes
