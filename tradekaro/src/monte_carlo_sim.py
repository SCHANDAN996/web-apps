"""
🎲 Monte Carlo Portfolio Simulator — Future Path Simulation

Simulates thousands of possible portfolio outcomes:
  - 10,000 random walk simulations
  - Probability of hitting profit targets
  - Risk of ruin estimation
  - Expected portfolio range at any future date
"""

import numpy as np


class MonteCarloSimulator:
    
    def simulate_portfolio(self, initial_capital, daily_return_mean, daily_return_std,
                           days=252, n_simulations=10000):
        paths = np.zeros((n_simulations, days + 1))
        paths[:, 0] = initial_capital
        
        for i in range(1, days + 1):
            returns = np.random.normal(daily_return_mean, daily_return_std, n_simulations)
            paths[:, i] = paths[:, i-1] * (1 + returns)
        
        final = paths[:, -1]
        
        return {
            'mean_outcome': round(float(np.mean(final)), 0),
            'median_outcome': round(float(np.median(final)), 0),
            'best_case': round(float(np.percentile(final, 95)), 0),
            'worst_case': round(float(np.percentile(final, 5)), 0),
            'prob_profit': round(float(np.mean(final > initial_capital) * 100), 1),
            'prob_10pct_gain': round(float(np.mean(final > initial_capital * 1.1) * 100), 1),
            'prob_20pct_loss': round(float(np.mean(final < initial_capital * 0.8) * 100), 1),
            'expected_return_pct': round(float((np.mean(final) / initial_capital - 1) * 100), 2),
            'simulations': n_simulations, 'days': days
        }
    
    def risk_of_ruin(self, capital, daily_std, ruin_level=0.5, n_sims=10000, days=252):
        """Probability of losing X% of capital."""
        ruin_threshold = capital * ruin_level
        ruined = 0
        
        for _ in range(n_sims):
            equity = capital
            for _ in range(days):
                equity *= (1 + np.random.normal(0, daily_std))
                if equity < ruin_threshold:
                    ruined += 1
                    break
        
        return {
            'risk_of_ruin': round(ruined / n_sims * 100, 2),
            'ruin_level': f'{ruin_level:.0%}',
            'safe': ruined / n_sims < 0.05
        }
    
    def target_probability(self, capital, target, daily_mean, daily_std, days=252, n_sims=10000):
        final = capital * np.cumprod(1 + np.random.normal(daily_mean, daily_std, (n_sims, days)), axis=1)[:, -1]
        prob = float(np.mean(final >= target) * 100)
        return {
            'target': target, 'probability': round(prob, 1),
            'interpretation': f'{prob:.0f}% chance of reaching ₹{target:,.0f} in {days} days'
        }
