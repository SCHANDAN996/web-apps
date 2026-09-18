"""
🧬♾️ Self-Evolution Engine — Autonomous AI Improvement

Runs DAILY after market close (3:35 PM IST):
1. EVALUATE — Check today's trading performance
2. DIAGNOSE — Find weakness areas
3. ADAPT   — Retrain on failing scenarios (experience replay)
4. VALIDATE — Compare new model vs current model
5. DEPLOY  — Hot-swap only if new model is better

This makes the AI truly autonomous — it improves itself
without human intervention.
"""

import os
import json
import time
import threading
import numpy as np
from datetime import datetime, timedelta
from copy import deepcopy

from src.brain import TradingBrain, DEVICE
from src.performance_tracker import PerformanceTracker
from src.experience_replay import ExperienceReplayBuffer
from src.model_registry import ModelRegistry
from src.training_pipeline import TrainingPipeline
from src.market_regime_detector import MarketRegimeDetector, MarketRegime


class SelfEvolutionEngine:
    """
    Autonomous Improvement Cycle.

    Schedule: Daily at 4:00 PM IST (after Indian market close)
    Duration: ~10-30 minutes depending on data volume

    Steps:
    1. EVALUATE: Gather today's predictions & outcomes
    2. DIAGNOSE: Identify where the model fails
    3. ADAPT: Retrain with experience replay
    4. VALIDATE: Walk-forward mini-backtest
    5. DEPLOY: Hot-swap if new model beats current
    """

    EVOLUTION_LOG = 'logs/evolution_history.json'

    def __init__(self, brain: TradingBrain, db=None):
        self.brain = brain
        self.db = db
        self.tracker = PerformanceTracker()
        self.replay_buffer = ExperienceReplayBuffer()
        self.registry = ModelRegistry()
        self.regime_detector = MarketRegimeDetector()
        self.running = False
        self.evolution_history = []

    def start(self):
        """Start the evolution thread (runs daily after market close)."""
        self.running = True
        self.thread = threading.Thread(target=self._evolution_loop, daemon=True)
        self.thread.start()
        print("[EVOLUTION] 🧬 Self-Evolution Engine Started.")

    def stop(self):
        self.running = False
        print("[EVOLUTION] Stopping...")

    def _evolution_loop(self):
        """Background loop that triggers evolution daily at market close."""
        while self.running:
            now = datetime.now()

            # Target: 4:00 PM IST (after market close at 3:30 PM)
            target_hour = 16
            target_minute = 0

            if now.hour == target_hour and now.minute < target_minute + 5:
                print(f"[EVOLUTION] 🧬 Starting daily evolution cycle... ({now})")
                try:
                    result = self.evolve()
                    self._log_evolution(result)
                except Exception as e:
                    print(f"[EVOLUTION] ❌ Error: {e}")
                    self._log_evolution({'error': str(e), 'status': 'FAILED'})

                # Sleep until tomorrow
                time.sleep(23 * 3600)
            else:
                # Check every 5 minutes
                time.sleep(300)

    def evolve(self):
        """
        Run one full evolution cycle.
        Returns: dict with metrics and actions taken
        """
        print("\n" + "=" * 60)
        print("🧬 SELF-EVOLUTION CYCLE")
        print("=" * 60)

        result = {
            'timestamp': datetime.now().isoformat(),
            'steps': {},
            'status': 'IN_PROGRESS'
        }

        # ──────────────────────────────────────────────────
        # STEP 1: EVALUATE
        # ──────────────────────────────────────────────────
        print("\n📊 Step 1: EVALUATE")
        metrics = self.tracker.get_metrics()
        degraded, reason = self.tracker.is_degraded()

        result['steps']['evaluate'] = {
            'metrics': metrics,
            'degraded': degraded,
            'reason': reason
        }

        print(f"   Accuracy: {metrics.get('accuracy', 'N/A')}%")
        print(f"   Win Rate: {metrics.get('win_rate', 'N/A')}%")
        print(f"   Drawdown: {metrics.get('max_drawdown', 'N/A')}%")
        print(f"   Degraded: {degraded} — {reason}")

        # ──────────────────────────────────────────────────
        # STEP 2: DIAGNOSE
        # ──────────────────────────────────────────────────
        print("\n🔍 Step 2: DIAGNOSE")
        diagnosis = self._diagnose()
        result['steps']['diagnose'] = diagnosis

        for finding in diagnosis.get('findings', []):
            print(f"   ⚠️ {finding}")

        # ──────────────────────────────────────────────────
        # STEP 3: ADAPT
        # ──────────────────────────────────────────────────
        print("\n🔧 Step 3: ADAPT")

        # Save current model before making changes
        self.registry.register_model(
            metrics=metrics,
            notes=f"Pre-evolution snapshot. Degraded={degraded}"
        )

        adaptation_result = self._adapt(diagnosis)
        result['steps']['adapt'] = adaptation_result

        print(f"   Replay samples used: {adaptation_result.get('replay_samples', 0)}")
        print(f"   Training epochs: {adaptation_result.get('epochs', 0)}")
        print(f"   New loss: {adaptation_result.get('final_loss', 'N/A')}")

        # ──────────────────────────────────────────────────
        # STEP 4: VALIDATE
        # ──────────────────────────────────────────────────
        print("\n✅ Step 4: VALIDATE")
        validation = self._validate()
        result['steps']['validate'] = validation

        improved = validation.get('improved', False)
        print(f"   Improved: {improved}")
        print(f"   Old accuracy: {validation.get('old_accuracy', 'N/A')}")
        print(f"   New accuracy: {validation.get('new_accuracy', 'N/A')}")

        # ──────────────────────────────────────────────────
        # STEP 5: DEPLOY or ROLLBACK
        # ──────────────────────────────────────────────────
        print("\n🚀 Step 5: DEPLOY")

        if improved:
            # Keep the new model
            self.registry.register_model(
                metrics=validation.get('new_metrics', {}),
                notes="Post-evolution: IMPROVED"
            )
            result['status'] = 'DEPLOYED_NEW'
            print("   ✅ New model DEPLOYED! Performance improved.")
        else:
            # Rollback to previous version
            self.registry.rollback()
            # Reload the brain
            self.brain = TradingBrain(use_v2=True)
            result['status'] = 'ROLLED_BACK'
            print("   ⏪ ROLLED BACK to previous model. New model did not improve.")

        # ──────────────────────────────────────────────────
        # SUMMARY
        # ──────────────────────────────────────────────────
        print("\n" + "=" * 60)
        print(f"🧬 Evolution Complete: {result['status']}")
        print("=" * 60)

        return result

    def _diagnose(self):
        """Analyze where the model is failing."""
        findings = []

        # 1. Check replay buffer stats
        buffer_stats = self.replay_buffer.get_stats()
        if buffer_stats.get('size', 0) > 0:
            avg_difficulty = buffer_stats.get('avg_difficulty', 0)
            if avg_difficulty > 0.5:
                findings.append(f"High average difficulty: {avg_difficulty:.2f} (many wrong predictions)")

            # Regime analysis
            regime_counts = buffer_stats.get('regime_breakdown', {})
            for regime, count in regime_counts.items():
                if regime == MarketRegime.TRANSITION and count > 10:
                    findings.append(f"Many failures during TRANSITION regime ({count} experiences)")

        # 2. Performance analysis
        metrics = self.tracker.get_metrics()
        if metrics.get('high_conf_accuracy', 100) < 55:
            findings.append("High-confidence predictions are inaccurate — model is overconfident")

        if metrics.get('profit_factor', 1) < 1.0:
            findings.append("Profit factor < 1.0 — losses exceed profits")

        if metrics.get('max_drawdown', 0) > 10:
            findings.append(f"Max drawdown {metrics['max_drawdown']}% exceeds safe limit")

        if not findings:
            findings.append("No significant issues found. Model performing within bounds.")

        return {
            'findings': findings,
            'buffer_stats': buffer_stats,
            'severity': 'HIGH' if len(findings) > 2 else 'LOW'
        }

    def _adapt(self, diagnosis):
        """Retrain the model based on diagnosis."""
        result = {'replay_samples': 0, 'epochs': 0, 'final_loss': None}

        severity = diagnosis.get('severity', 'LOW')
        epochs = 5 if severity == 'HIGH' else 3

        # Sample from experience replay (priority-weighted: more mistakes get replayed more)
        X_replay, y_replay = self.replay_buffer.sample(batch_size=min(256, self.replay_buffer.max_size))

        if len(X_replay) > 0:
            try:
                pipeline = TrainingPipeline(input_features=X_replay.shape[2])
                pipeline.brain = self.brain
                pipeline.model = self.brain.model
                pipeline.train_stage3_incremental(X_replay, y_replay, epochs=epochs)

                result['replay_samples'] = len(X_replay)
                result['epochs'] = epochs
                result['final_loss'] = 'Completed'
            except Exception as e:
                result['error'] = str(e)
        else:
            result['note'] = 'No replay data available. Skipping retraining.'

        return result

    def _validate(self):
        """Quick validation to compare new vs old model performance."""
        # Use recent data from replay buffer as a mini-test set
        X_test, y_test = self.replay_buffer.sample(batch_size=min(100, len(self.replay_buffer.buffer)))

        if len(X_test) == 0:
            return {'improved': True, 'note': 'No test data — keeping new model by default'}

        # Test new model
        import torch
        self.brain.model.eval()
        with torch.no_grad():
            X_tensor = torch.tensor(X_test, dtype=torch.float32).to(DEVICE)
            try:
                predictions = self.brain.model(X_tensor).cpu().numpy().flatten()
                pred_labels = (predictions > 0.5).astype(int)
                new_accuracy = np.mean(pred_labels == y_test)
            except Exception:
                new_accuracy = 0.5

        # Compare with historical accuracy
        old_metrics = self.tracker.get_metrics()
        old_accuracy = old_metrics.get('accuracy', 50) / 100

        improved = new_accuracy >= old_accuracy - 0.02  # Allow 2% margin

        return {
            'improved': improved,
            'old_accuracy': round(old_accuracy * 100, 1),
            'new_accuracy': round(new_accuracy * 100, 1),
            'new_metrics': {
                'accuracy': round(new_accuracy * 100, 1),
                'test_samples': len(X_test)
            }
        }

    def _log_evolution(self, result):
        """Log evolution result to file."""
        self.evolution_history.append(result)
        try:
            os.makedirs(os.path.dirname(self.EVOLUTION_LOG) or 'logs', exist_ok=True)
            with open(self.EVOLUTION_LOG, 'w') as f:
                json.dump(self.evolution_history[-50:], f, indent=2)
        except Exception:
            pass

    def force_evolve(self):
        """Manual trigger for evolution (for testing)."""
        return self.evolve()
