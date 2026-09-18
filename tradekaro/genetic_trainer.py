import random
import numpy as np
import pandas as pd
from src.database import TradingDB
from src.indicators import TechnicalIndicators
import config.settings as settings

# --- GENETIC CONFIGURATION ---
POPULATION_SIZE = 20
GENERATIONS = 5
MUTATION_RATE = 0.1

class StrategyGenome:
    def __init__(self, sl_pct, tp_pct, rsi_period, adx_threshold):
        self.sl_pct = sl_pct
        self.tp_pct = tp_pct
        self.rsi_period = int(rsi_period)
        self.adx_threshold = int(adx_threshold)
        self.fitness = 0

    @staticmethod
    def random():
        return StrategyGenome(
            sl_pct=round(random.uniform(0.5, 3.0), 2),
            tp_pct=round(random.uniform(1.0, 6.0), 2),
            rsi_period=random.randint(10, 30),
            adx_threshold=random.randint(15, 30)
        )

    def __repr__(self):
        return f"Genome(SL:{self.sl_pct}%, TP:{self.tp_pct}%, RSI:{self.rsi_period}, ADX:{self.adx_threshold})"

class GeneticTrainer:
    def __init__(self):
        self.db = TradingDB()
        self.population = [StrategyGenome.random() for _ in range(POPULATION_SIZE)]
        self.best_genome = None

    def load_data(self, symbol="NIFTY"):
        print(f"[Genetic] Loading Data for {symbol}...")
        df = self.db.get_market_data(symbol, '5m', limit=2000)
        if df.empty: return None
        return df

    def fitness_function(self, genome, df):
        """
        Simulates trading with genome parameters.
        Fitness = Total Profit %
        """
        # Apply Indicators (Custom for this genome)
        # Note: Re-calculating indicators for every genome is slow. 
        # Optimization: Pre-calc common indicators or only calc specific ones.
        # For simplicity/speed in demo: We'll assume standard 14 RSI is 'close enough' 
        # or actually calc it if period differs. 
        
        # Let's calc custom RSI for accuracy
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=genome.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=genome.rsi_period).mean()
        rs = gain / loss
        rsi_series = 100 - (100 / (1 + rs))
        
        # Backtest Logic
        balance = 100000
        position = None
        entry_price = 0
        
        # Vectorized or Loop? Loop is easier to write logic for SL/TP
        prices = df['close'].values
        rsis = rsi_series.fillna(50).values
        
        # Simple Strategy:
        # Buy if RSI < 30 (Oversold)
        # Sell if RSI > 70 (Overbought)
        # Exit on SL/TP
        
        for i in range(len(prices)):
            price = prices[i]
            rsi = rsis[i]
            
            if position is None:
                if rsi < 30:
                    position = 'BUY'
                    entry_price = price
            else:
                # Check Exit
                pct_change = (price - entry_price) / entry_price
                
                if pct_change >= (genome.tp_pct / 100):
                    balance *= (1 + pct_change)
                    position = None
                elif pct_change <= -(genome.sl_pct / 100):
                    balance *= (1 + pct_change)
                    position = None
                # Time-based exit? (Optional)
        
        return (balance - 100000) / 100000 * 100 # Profit %

    def evolve(self):
        print(f"🧬 Starting Evolution (Pop: {POPULATION_SIZE}, Gens: {GENERATIONS})")
        
        # Load Data Once
        df = self.load_data("NIFTY")
        if df is None: 
            print("❌ No Data available for Backtest.")
            return

        for gen in range(GENERATIONS):
            # 1. Evaluate Fitness
            for genome in self.population:
                genome.fitness = self.fitness_function(genome, df)
            
            # Sort by Fitness (Desc)
            self.population.sort(key=lambda x: x.fitness, reverse=True)
            
            best = self.population[0]
            print(f"   Generaton {gen+1}: Best Fitness = {best.fitness:.2f}% | {best}")
            
            if self.best_genome is None or best.fitness > self.best_genome.fitness:
                self.best_genome = best

            # 2. Selection (Top 50%)
            survivors = self.population[:POPULATION_SIZE//2]
            
            # 3. Crossover & Mutation
            new_pop = survivors[:] # Keep elites
            
            while len(new_pop) < POPULATION_SIZE:
                parent1 = random.choice(survivors)
                parent2 = random.choice(survivors)
                
                # Crossover
                child = StrategyGenome(
                    sl_pct=parent1.sl_pct if random.random() > 0.5 else parent2.sl_pct,
                    tp_pct=parent1.tp_pct if random.random() > 0.5 else parent2.tp_pct,
                    rsi_period=int((parent1.rsi_period + parent2.rsi_period) / 2),
                    adx_threshold=parent1.adx_threshold
                )
                
                # Mutation
                if random.random() < MUTATION_RATE:
                    child.sl_pct = round(child.sl_pct * random.uniform(0.8, 1.2), 2)
                
                new_pop.append(child)
            
            self.population = new_pop
            
        print(f"\n🏆 Evolution Complete! Best Strategy: {self.best_genome}")
        print(f"💡 Suggestion: Update 'config/settings.py' manually if this outperforms current settings.")

if __name__ == "__main__":
    trainer = GeneticTrainer()
    trainer.evolve()
