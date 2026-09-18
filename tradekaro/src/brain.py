"""
🧠 Trade Karo AI Brain V2 — Transformer + LSTM Hybrid Architecture

Architecture:
  Input (batch, 60, features)
    → Positional Encoding (sinusoidal time awareness)
    → 2x Transformer Encoder Layers (4 heads, 128 dim)
    → Bidirectional LSTM (128 hidden, 2 layers)
    → Attention Pooling (learn which timesteps matter most)
    → FC → Dropout(0.3) → FC → Sigmoid
  Output: Probability 0.0 - 1.0

Backward Compatible: Old LSTMModel class retained for loading legacy checkpoints.
"""

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import os
import math
import time
import logging
import joblib

from config.feature_config import FEATURES, FEATURE_VERSION

# Check for GPU (Fast Training) or CPU
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


# ====================================================================== #
#                     LEGACY MODEL (Backward Compatibility)               #
# ====================================================================== #

class LSTMModel(nn.Module):
    """Original LSTM model — kept for loading old checkpoints."""

    def __init__(self, input_size, hidden_size=64, num_layers=2, output_size=1):
        super(LSTMModel, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers

        self.lstm = nn.LSTM(input_size, hidden_size, num_layers,
                            batch_first=True, dropout=0.2)
        self.fc = nn.Linear(hidden_size, output_size)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(DEVICE)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(DEVICE)
        out, _ = self.lstm(x, (h0, c0))
        out = self.fc(out[:, -1, :])
        out = self.sigmoid(out)
        return out


# ====================================================================== #
#                    SIMPLE BRAIN V3 (Anti-Collapse)                       #
# ====================================================================== #

class SimpleBrainV3(nn.Module):
    """
    Simple GRU + Dense with high dropout + batch norm.
    Designed to NOT collapse to constant like the complex Transformer+LSTM.
    
    Key differences:
    - Single-layer GRU (much fewer params)
    - BatchNorm1d prevents mode collapse
    - High dropout (0.5) forces generalization
    - Uses last 10 timesteps avg (not attention)
    """

    def __init__(self, input_size, hidden_size=64, output_size=1):
        super(SimpleBrainV3, self).__init__()
        self.hidden_size = hidden_size
        
        # Input batch norm
        self.input_bn = nn.BatchNorm1d(input_size)
        
        # Single GRU layer
        self.gru = nn.GRU(input_size, hidden_size, num_layers=1,
                          batch_first=True, dropout=0.0)
        
        # Classification head with batch norm + high dropout
        self.classifier = nn.Sequential(
            nn.BatchNorm1d(hidden_size),
            nn.Dropout(0.5),
            nn.Linear(hidden_size, 16),
            nn.ReLU(),
            nn.BatchNorm1d(16),
            nn.Dropout(0.3),
            nn.Linear(16, output_size),
            nn.Sigmoid()
        )

    def forward(self, x):
        # x: (batch, seq_len, features)
        batch_size = x.size(0)
        
        # BatchNorm on features (transpose to batch, features, seq)
        x = x.transpose(1, 2)  # (batch, features, seq)
        x = self.input_bn(x)
        x = x.transpose(1, 2)  # (batch, seq, features)
        
        # GRU
        out, _ = self.gru(x)  # (batch, seq, hidden)
        
        # Use mean of last 10 timesteps (more robust than single last)
        out = out[:, -10:, :].mean(dim=1)  # (batch, hidden)
        
        # Classify
        return self.classifier(out)


# ====================================================================== #
#                    NEW V2 ARCHITECTURE COMPONENTS                       #
# ====================================================================== #

class PositionalEncoding(nn.Module):
    """
    Injects time-sequence positional information using sinusoidal encoding.
    Candle at position 0 (oldest) gets different encoding than position 59 (latest).
    """

    def __init__(self, d_model, max_len=200, dropout=0.1):
        super(PositionalEncoding, self).__init__()
        self.dropout = nn.Dropout(p=dropout)

        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))

        pe[:, 0::2] = torch.sin(position * div_term)
        if d_model % 2 == 1:
            pe[:, 1::2] = torch.cos(position * div_term[:-1])
        else:
            pe[:, 1::2] = torch.cos(position * div_term)

        pe = pe.unsqueeze(0)  # (1, max_len, d_model)
        self.register_buffer('pe', pe)

    def forward(self, x):
        # x: (batch, seq_len, d_model)
        x = x + self.pe[:, :x.size(1), :]
        return self.dropout(x)


class AttentionPooling(nn.Module):
    """
    Learned attention pooling over the sequence dimension.
    Instead of just using the last hidden state (information loss),
    this learns which timesteps are most important for the prediction.
    """

    def __init__(self, hidden_size):
        super(AttentionPooling, self).__init__()
        self.attention_weights = nn.Linear(hidden_size, 1)

    def forward(self, lstm_output):
        # lstm_output: (batch, seq_len, hidden)
        scores = self.attention_weights(lstm_output)  # (batch, seq, 1)
        weights = torch.softmax(scores, dim=1)        # (batch, seq, 1)
        context = (lstm_output * weights).sum(dim=1)   # (batch, hidden)
        return context, weights.squeeze(-1)


class TransformerLSTM(nn.Module):
    """
    🧬 Hybrid Transformer + Bidirectional LSTM with Attention Pooling.

    Why Hybrid?
    - Transformer captures cross-time dependencies (e.g., pattern at candle 5
      correlates with pattern at candle 55)
    - LSTM captures sequential memory (trend direction, momentum buildup)
    - Attention Pooling learns WHICH candles matter for the final decision

    Architecture:
        Input → Linear Projection → Positional Encoding
            → Transformer Encoder (2 layers, 4 heads)
            → Bidirectional LSTM (128 hidden, 2 layers)
            → Attention Pooling
            → FC(256→64) → ReLU → Dropout → FC(64→1) → Sigmoid
    """

    def __init__(self, input_size, d_model=128, nhead=4, num_transformer_layers=2,
                 lstm_hidden=128, lstm_layers=2, dropout=0.3):
        super(TransformerLSTM, self).__init__()

        self.input_size = input_size
        self.d_model = d_model

        # Input projection (features → d_model dimension)
        self.input_projection = nn.Linear(input_size, d_model)

        # Positional Encoding
        self.pos_encoder = PositionalEncoding(d_model, dropout=dropout)

        # Transformer Encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model, nhead=nhead,
            dim_feedforward=d_model * 4,
            dropout=dropout, batch_first=True,
            activation='gelu'
        )
        self.transformer_encoder = nn.TransformerEncoder(
            encoder_layer, num_layers=num_transformer_layers
        )

        # Bidirectional LSTM
        self.lstm = nn.LSTM(
            d_model, lstm_hidden, lstm_layers,
            batch_first=True, dropout=dropout,
            bidirectional=True
        )

        # Attention Pooling (over bidirectional output = 2 * hidden)
        self.attention_pool = AttentionPooling(lstm_hidden * 2)

        # Classification Head
        self.classifier = nn.Sequential(
            nn.Linear(lstm_hidden * 2, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, 1),
            nn.Sigmoid()
        )

        # Layer Normalization for stability
        self.layer_norm = nn.LayerNorm(d_model)

    def forward(self, x):
        # x: (batch, seq_len, input_size)

        # 1. Project input features to d_model dimensions
        x = self.input_projection(x)     # (batch, seq, d_model)
        x = self.layer_norm(x)

        # 2. Add positional encoding
        x = self.pos_encoder(x)          # (batch, seq, d_model)

        # 3. Transformer Encoder (captures cross-time relationships)
        x = self.transformer_encoder(x)  # (batch, seq, d_model)

        # 4. Bidirectional LSTM (captures sequential memory)
        x, _ = self.lstm(x)              # (batch, seq, lstm_hidden*2)

        # 5. Attention Pooling (learn which timesteps matter)
        x, attn_weights = self.attention_pool(x)  # (batch, lstm_hidden*2)

        # 6. Classification
        out = self.classifier(x)         # (batch, 1)
        return out

    def get_attention_weights(self, x):
        """Returns attention weights for interpretability / visualization."""
        self.eval()
        with torch.no_grad():
            x = self.input_projection(x)
            x = self.layer_norm(x)
            x = self.pos_encoder(x)
            x = self.transformer_encoder(x)
            x, _ = self.lstm(x)
            _, attn_weights = self.attention_pool(x)
        return attn_weights


# ====================================================================== #
#                         TRADING BRAIN V2                                #
# ====================================================================== #

class TradingBrain:
    """
    Manages the AI model lifecycle: load, build, train, save, predict.

    Model versioning:
        - v1: Legacy LSTMModel (64 hidden, unidirectional)
        - v2: TransformerLSTM (128 dim, 4 heads, bidirectional)

    Checkpoint format:
        {
            'model_state': state_dict,
            'input_size': int,
            'model_version': 'v1' or 'v2',
            'timestamp': ISO string
        }
    """

    MODEL_V3 = 'v3'
    MODEL_V2 = 'v2'
    MODEL_V1 = 'v1'

    def __init__(self, input_features=22, seq_length=60, use_v2=True):
        self.model_path = 'models/tradenet_actor.pth'
        self.input_features = input_features
        self.seq_length = seq_length
        self.use_v2 = use_v2

        # Load or Build
        self.model = self._load_or_build_model()

        # Optimizer & Loss — plain BCE (focal loss caused collapsed predictions)
        # functional form, because train_incremental passes per-sample weights
        # that change with every batch. See _class_weights.
        self.criterion = torch.nn.functional.binary_cross_entropy
        self.optimizer = optim.Adam(self.model.parameters(), lr=0.001)
        self.scheduler = optim.lr_scheduler.StepLR(self.optimizer, step_size=50, gamma=0.5)

    def _load_or_build_model(self):
        """Loads existing model or builds a new one."""
        # Archive legacy sklearn model
        if os.path.exists('models/trading_brain.pkl'):
            try:
                os.rename('models/trading_brain.pkl', 'models/trading_brain_legacy.pkl')
                print("[UPGRADE] Archived Legacy MLP Brain.")
            except:
                pass

        if os.path.exists(self.model_path):
            print("[INFO] Loading Brain...")
            try:
                checkpoint = torch.load(self.model_path, map_location=DEVICE, weights_only=False)

                if isinstance(checkpoint, dict) and 'model_state' in checkpoint:
                    input_sz = checkpoint.get('input_size', 12)
                    version = checkpoint.get('model_version', self.MODEL_V1)

                    if version == self.MODEL_V3:
                        model = SimpleBrainV3(input_size=input_sz).to(DEVICE)
                    elif version == self.MODEL_V2:
                        model = TransformerLSTM(input_size=input_sz).to(DEVICE)
                    else:
                        model = LSTMModel(input_size=input_sz).to(DEVICE)

                    model.load_state_dict(checkpoint['model_state'])
                    self.input_features = input_sz
                    self.feature_names = checkpoint.get('feature_names')
                    model.eval()
                    print(f"[INFO] Loaded {version} model ({input_sz} features)")
                    # input_sz is passed in: self.model is not assigned until
                    # this function returns, so _get_input_size() cannot be
                    # called from here.
                    self._check_feature_contract(checkpoint, input_sz)
                    return model

                elif isinstance(checkpoint, nn.Module):
                    checkpoint.to(DEVICE)
                    checkpoint.eval()
                    return checkpoint
                else:
                    print("[WARN] Unknown model format. Building New.")

            except Exception as e:
                print(f"[WARN] Failed to load Brain: {e}. Building New.")

        # Build new model — V3 (SimpleBrainV3) is now default
        print("[INIT] Building NEW SimpleBrainV3 (GRU + BatchNorm + Dropout).")
        return SimpleBrainV3(input_size=self.input_features).to(DEVICE)

    # NO_TRADE is about 96.6% of every batch, and with equal weights the
    # cheapest thing the model can do is answer 0.5 to everything: that scores
    # -log(0.5) = 0.693 on the majority and the remaining 3.4% is not worth
    # deviating for. It found exactly that -- 290 training runs sitting at a
    # median loss of 0.694, while live output collapsed to 17 BUY against 5804
    # SELL with a quarter of readings pinned at 0.00.
    #
    # Weighting the signal samples up makes ignoring them expensive. The ratio
    # is computed per batch and capped, since an uncapped 28x on a batch that
    # happens to hold two signals would swamp the gradient.
    MAX_SIGNAL_WEIGHT = 10.0

    def _class_weights(self, y_batch):
        """Per-sample weights that stop NO_TRADE from drowning the signal."""
        is_signal = (y_batch != 0.5)
        n_signal = int(is_signal.sum())

        if n_signal == 0 or n_signal == y_batch.numel():
            return None  # nothing to rebalance

        n_majority = y_batch.numel() - n_signal
        ratio = min(n_majority / n_signal, self.MAX_SIGNAL_WEIGHT)

        weights = torch.ones_like(y_batch)
        weights[is_signal] = ratio
        return weights

    def train_incremental(self, x_train, y_train, epochs=5, batch_size=256):
        """Standard or Incremental Training Loop with mini-batch support."""
        self.model.train()

        # Dynamic rebuild on feature mismatch
        current_dim = self._get_input_size()
        new_dim = x_train.shape[2]

        if current_dim != new_dim:
            print(f"[REBUILD] Feature Dimension Changed ({current_dim} → {new_dim}). Resetting Brain.")
            self.model = SimpleBrainV3(input_size=new_dim).to(DEVICE)
            self.optimizer = optim.Adam(self.model.parameters(), lr=0.001)
            self.scheduler = optim.lr_scheduler.StepLR(self.optimizer, step_size=50, gamma=0.5)
            self.input_features = new_dim

        n_samples = len(x_train)
        total_loss = 0
        n_batches = 0

        # CRITICAL: Enable training mode (activates dropout + batchnorm)
        self.model.train()

        for epoch in range(epochs):
            # Shuffle indices each epoch
            indices = np.random.permutation(n_samples)
            
            for start in range(0, n_samples, batch_size):
                end = min(start + batch_size, n_samples)
                batch_idx = indices[start:end]
                
                X_batch = torch.tensor(x_train[batch_idx], dtype=torch.float32).to(DEVICE)
                y_batch = torch.tensor(y_train[batch_idx], dtype=torch.float32).unsqueeze(1).to(DEVICE)

                self.optimizer.zero_grad()
                outputs = self.model(X_batch)
                loss = self.criterion(outputs, y_batch, weight=self._class_weights(y_batch))
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
                self.optimizer.step()
                
                total_loss = loss.item()
                n_batches += 1

                # Free GPU memory
                del X_batch, y_batch, outputs
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()

        # Switch back to eval mode after training
        self.model.eval()
        if hasattr(self, 'scheduler'):
            self.scheduler.step()
        print(f"[LEARN] Brain trained on {n_samples} samples. Loss: {total_loss:.4f}")
        self.save_model()

    def _check_feature_contract(self, checkpoint, input_size):
        """Compare the columns this model was fitted on with today's list.

        Checkpoints written before this existed carry no names -- say so once
        and move on, rather than pretending the contract has been verified.
        """
        trained_on = checkpoint.get('feature_names')

        if not trained_on:
            message = (f"[BRAIN] {self.model_path} predates feature-name "
                       f"recording -- it wants {input_size} columns "
                       f"but does not say which. Retrain to pin it down.")
            logging.warning(message)
            print(f"[WARN] {message}")
            return

        if list(trained_on) == list(FEATURES):
            print(f"[INFO] ✅ Feature contract matches ({len(FEATURES)} columns, "
                  f"{checkpoint.get('feature_version', 'unversioned')})")
            return

        # Order matters as much as membership: the model reads column 4, not
        # a column named MACD, so a reordered list is silently wrong data.
        added = [f for f in FEATURES if f not in trained_on]
        removed = [f for f in trained_on if f not in FEATURES]
        message = (f"[BRAIN] feature contract MISMATCH -- model was fitted on "
                   f"{len(trained_on)} columns, config now names {len(FEATURES)}. "
                   f"added={added} removed={removed}"
                   f"{' (same names, different order)' if not added and not removed else ''}. "
                   f"Predictions from this pairing are meaningless; retrain.")
        logging.error(message)
        print(f"[ERROR] {message}")

    def save_model(self):
        """Save Model State with version info."""
        if not os.path.exists('models'):
            os.makedirs('models')

        if isinstance(self.model, SimpleBrainV3):
            version = self.MODEL_V3
        elif isinstance(self.model, TransformerLSTM):
            version = self.MODEL_V2
        else:
            version = self.MODEL_V1

        checkpoint = {
            'input_size': self._get_input_size(),
            'model_state': self.model.state_dict(),
            'model_version': version,
            'timestamp': __import__('datetime').datetime.now().isoformat(),

            # The names, not just the count. A checkpoint carrying only
            # input_size=13 cannot be checked against anything: when the
            # trainer's list and the caller's list drifted apart, nothing on
            # disk knew enough to notice. Weights and the columns they were
            # fitted on travel together from here on.
            'feature_names': list(FEATURES),
            'feature_version': FEATURE_VERSION,
        }
        torch.save(checkpoint, self.model_path)

    # Shape mismatches repeat on every symbol on every cycle -- 32 symbols by
    # 4 timeframes -- so the message is throttled rather than dropped. Silence
    # is what let the last one hide; a wall of identical lines would too.
    _MISMATCH_LOG_INTERVAL = 300  # seconds

    def _warn_feature_mismatch(self, received, expected):
        now = time.time()
        last = getattr(self, '_last_mismatch_warning', 0)
        seen = getattr(self, '_mismatch_count', 0) + 1
        self._mismatch_count = seen

        if now - last < self._MISMATCH_LOG_INTERVAL:
            return
        self._last_mismatch_warning = now

        fate = ('extra columns dropped' if received > expected
                else 'NO PREDICTION MADE, returning neutral 0.5')
        message = (f"[BRAIN] feature count mismatch: model wants {expected}, "
                   f"got {received} -- {fate} "
                   f"({seen} times since start). The caller's feature list "
                   f"disagrees with what this model was trained on.")
        logging.error(message)
        print(f"[ERROR] {message}")

    def predict(self, last_60_candles):
        """Live Prediction — returns probability 0.0 to 1.0."""
        self.model.eval()
        with torch.no_grad():
            if isinstance(last_60_candles, np.ndarray):
                expected = self._get_input_size()
                received = last_60_candles.shape[2]

                if received != expected:
                    # Both branches used to be silent. The short branch in
                    # particular returned a neutral 0.5 that is indistinguishable
                    # from "the model has no opinion" -- so a feature-name
                    # mismatch upstream read as a flat market, and the bot sat
                    # out every trade from 22 July to 6 August without one line
                    # of log saying why. Never fail quietly here again.
                    self._warn_feature_mismatch(received, expected)

                    if received > expected:
                        last_60_candles = last_60_candles[:, :, :expected]
                    else:
                        return 0.5  # Return uncertain if features missing

                X_tensor = torch.tensor(last_60_candles, dtype=torch.float32).to(DEVICE)
                output = self.model(X_tensor)
                return output.item()

            return 0.5

    def get_attention_map(self, last_60_candles):
        """Get attention weights for interpretability (V2 only)."""
        if not isinstance(self.model, TransformerLSTM):
            return None

        if isinstance(last_60_candles, np.ndarray):
            X_tensor = torch.tensor(last_60_candles, dtype=torch.float32).to(DEVICE)
            return self.model.get_attention_weights(X_tensor).cpu().numpy()
        return None

    def _get_input_size(self):
        """Get model's expected input feature count, works for both V1 and V2."""
        if isinstance(self.model, TransformerLSTM):
            return self.model.input_size
        elif isinstance(self.model, LSTMModel):
            return self.model.lstm.input_size
        return self.input_features
