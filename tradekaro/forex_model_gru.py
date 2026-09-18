"""
🎯 Model 2: GRU Sequence Predictor
Predicts direction from 60-bar sequence of 12 curated features.
Captures temporal patterns (momentum buildup, trend exhaustion).
3-class output: HOLD (0), BUY (1), SELL (2)
"""

import numpy as np
import os
import torch
import torch.nn as nn
import torch.optim as optim
from datetime import datetime

DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
MODEL_PATH = 'models/forex_sequence_gru.pth'


class LightweightForexNet(nn.Module):
    """Causal Transformer for forex sequence classification. Much faster than GRU on CPU."""

    def __init__(self, input_size=17, hidden_size=64, num_classes=3, max_len=60):
        super().__init__()
        # hidden_size acts as d_model
        d_model = hidden_size
        nhead = 4
        num_layers = 2
        
        self.input_proj = nn.Linear(input_size, d_model)
        self.pos_embed = nn.Embedding(max_len, d_model)
        
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=128,
            dropout=0.2,
            activation='gelu',
            batch_first=True,
            norm_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        
        self.classifier = nn.Sequential(
            nn.Linear(d_model, 32),
            nn.GELU(),
            nn.Dropout(0.2),
            nn.Linear(32, num_classes)
        )

    def forward(self, x):
        # x: (batch, seq_len, features)
        batch, seq_len, _ = x.shape
        positions = torch.arange(seq_len, device=x.device).unsqueeze(0)
        
        x = self.input_proj(x) + self.pos_embed(positions)
        
        # Causal mask: upper triangle is True (True means masked out in PyTorch)
        causal_mask = torch.triu(torch.ones(seq_len, seq_len, device=x.device), diagonal=1).bool()
        
        transformer_out = self.transformer(x, mask=causal_mask, is_causal=True)
        
        # We only care about the final prediction
        last_token = transformer_out[:, -1, :]
        logits = self.classifier(last_token)
        return logits

    def predict_proba(self, x):
        """Get softmax probabilities."""
        self.eval()
        with torch.no_grad():
            logits = self.forward(x)
            return torch.softmax(logits, dim=1)


class SequencePredictor:
    """Wrapper for training and using the GRU model."""

    def __init__(self, input_size=14, hidden_size=128, num_classes=3):
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_classes = num_classes
        self.model = None
        self.best_val_loss = float('inf')

    def build(self):
        self.model = LightweightForexNet(
            input_size=self.input_size, 
            hidden_size=self.hidden_size, 
            num_classes=self.num_classes
        ).to(DEVICE)

    def train(self, X_train, y_train, X_val=None, y_val=None,
               epochs=30, batch_size=256, lr=0.001, patience=10):
        """Train GRU with early stopping."""
        if self.model is None:
            self.input_size = X_train.shape[2]
            self.build()

        criterion = nn.CrossEntropyLoss(
            weight=self._class_weights(y_train).to(DEVICE)
        )
        optimizer = optim.Adam(self.model.parameters(), lr=lr, weight_decay=1e-5)
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, patience=5, factor=0.5, min_lr=1e-5
        )

        n = len(X_train)
        patience_counter = 0

        print(f"  [GRU] Training: {n:,} samples, {epochs} epochs, "
              f"bs={batch_size}, lr={lr}")
        print(f"  [Sequence] Architecture: CausalTransformer({self.input_size}→{self.hidden_size}) "
              f"→ Dense(32) → {self.num_classes}-class")

        for epoch in range(epochs):
            # ── TRAIN ──
            self.model.train()
            indices = np.random.permutation(n)
            total_loss = 0
            n_batches = 0

            for start in range(0, n, batch_size):
                end = min(start + batch_size, n)
                bi = indices[start:end]

                xb = torch.tensor(X_train[bi], dtype=torch.float32).to(DEVICE)
                yb = torch.tensor(y_train[bi], dtype=torch.long).to(DEVICE)

                xb = torch.nan_to_num(xb, nan=0.0, posinf=1.0, neginf=-1.0)

                optimizer.zero_grad()
                out = self.model(xb)
                loss = criterion(out, yb)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                optimizer.step()

                total_loss += loss.item()
                n_batches += 1
                del xb, yb, out

            train_loss = total_loss / max(n_batches, 1)

            # ── VALIDATE ──
            if X_val is not None:
                val_loss, val_acc, val_pred = self._validate(
                    X_val, y_val, criterion
                )
                scheduler.step(val_loss)

                if (epoch + 1) % 5 == 0 or epoch == 0:
                    print(f"    Ep{epoch+1:02d}: TrLoss={train_loss:.4f} "
                          f"VlLoss={val_loss:.4f} VlAcc={val_acc:.1%}")

                # Early stopping
                if val_loss < self.best_val_loss:
                    self.best_val_loss = val_loss
                    patience_counter = 0
                    self._save_checkpoint(val_loss, val_acc)
                else:
                    patience_counter += 1
                    if patience_counter >= patience:
                        print(f"    ⏹ Early stopping at epoch {epoch + 1}")
                        break
            else:
                if (epoch + 1) % 5 == 0:
                    print(f"    Ep{epoch+1:02d}: Loss={train_loss:.4f}")

        # Load best model
        if os.path.exists(MODEL_PATH):
            self.load()

        return self

    def _validate(self, X_val, y_val, criterion):
        """Run validation and return loss, accuracy, predictions."""
        self.model.eval()
        all_preds = []

        with torch.no_grad():
            total_loss = 0
            n_batches = 0
            for start in range(0, len(X_val), 512):
                end = min(start + 512, len(X_val))
                xv = torch.tensor(X_val[start:end], dtype=torch.float32).to(DEVICE)
                yv = torch.tensor(y_val[start:end], dtype=torch.long).to(DEVICE)
                xv = torch.nan_to_num(xv, nan=0.0, posinf=1.0, neginf=-1.0)

                out = self.model(xv)
                loss = criterion(out, yv)
                total_loss += loss.item()
                n_batches += 1

                preds = torch.argmax(out, dim=1).cpu().numpy()
                all_preds.extend(preds)
                del xv, yv, out

        val_loss = total_loss / max(n_batches, 1)
        all_preds = np.array(all_preds)
        val_acc = (all_preds == y_val[:len(all_preds)]).mean()

        return val_loss, val_acc, all_preds

    def _class_weights(self, y):
        """Compute inverse frequency class weights."""
        counts = np.bincount(y.astype(int), minlength=self.num_classes)
        counts = np.maximum(counts, 1)  # Prevent division by zero
        weights = 1.0 / counts.astype(float)
        weights = weights / weights.sum() * self.num_classes
        return torch.tensor(weights, dtype=torch.float32)

    def predict(self, X):
        """Predict class labels."""
        self.model.eval()
        all_preds = []
        with torch.no_grad():
            for start in range(0, len(X), 512):
                end = min(start + 512, len(X))
                xb = torch.tensor(X[start:end], dtype=torch.float32).to(DEVICE)
                xb = torch.nan_to_num(xb, nan=0.0, posinf=1.0, neginf=-1.0)
                out = self.model(xb)
                preds = torch.argmax(out, dim=1).cpu().numpy()
                all_preds.extend(preds)
                del xb, out
        return np.array(all_preds)

    def predict_proba(self, X):
        """Get class probabilities."""
        self.model.eval()
        all_probs = []
        with torch.no_grad():
            for start in range(0, len(X), 512):
                end = min(start + 512, len(X))
                xb = torch.tensor(X[start:end], dtype=torch.float32).to(DEVICE)
                xb = torch.nan_to_num(xb, nan=0.0, posinf=1.0, neginf=-1.0)
                probs = self.model.predict_proba(xb).cpu().numpy()
                all_probs.append(probs)
                del xb
        return np.concatenate(all_probs, axis=0)

    def predict_with_confidence(self, X):
        """Returns (direction, confidence)."""
        proba = self.predict_proba(X)
        direction = np.argmax(proba, axis=1)
        confidence = np.max(proba, axis=1)
        return direction, confidence

    def _save_checkpoint(self, val_loss, val_acc):
        os.makedirs('models', exist_ok=True)
        torch.save({
            'model_state': self.model.state_dict(),
            'input_size': self.input_size,
            'hidden_size': self.hidden_size,
            'num_classes': self.num_classes,
            'val_loss': val_loss,
            'val_acc': float(val_acc),
            'timestamp': datetime.now().isoformat()
        }, MODEL_PATH)

    def save(self, path=MODEL_PATH):
        self._save_checkpoint(self.best_val_loss, 0)
        print(f"  [Sequence] Saved to {path}")

    def load(self, path=MODEL_PATH):
        if os.path.exists(path):
            ckpt = torch.load(path, map_location=DEVICE, weights_only=False)
            self.input_size = ckpt.get('input_size', 12)
            self.hidden_size = ckpt.get('hidden_size', 96)
            self.num_classes = ckpt.get('num_classes', 3)
            self.model = LightweightForexNet(
                input_size=self.input_size, 
                hidden_size=self.hidden_size, 
                num_classes=self.num_classes
            ).to(DEVICE)
            self.model.load_state_dict(ckpt['model_state'])
            self.model.eval()
            print(f"  [Sequence] Loaded from {path} "
                  f"(val_loss={ckpt.get('val_loss', '?'):.4f}, "
                  f"acc={ckpt.get('val_acc', '?')})")
            return True
        return False
