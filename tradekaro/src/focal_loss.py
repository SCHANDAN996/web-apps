"""
🎯 Focal Loss for Trading AI
Handles class imbalance (many HOLD labels vs few BUY labels).

Standard BCE treats all samples equally.
Focal Loss reduces weight on easy/well-classified examples,
focusing the model on harder, ambiguous market scenarios.

Reference: Lin et al., "Focal Loss for Dense Object Detection" (2017)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class FocalLoss(nn.Module):
    """
    Focal Loss = -alpha * (1 - p_t)^gamma * log(p_t)
    
    When gamma=0: Equivalent to standard Binary Cross-Entropy
    When gamma>0: Down-weights easy examples, focuses on hard ones
    
    Args:
        alpha: Balancing factor for positive class (default: 0.75 for rare BUY signals)
        gamma: Focusing parameter (default: 2.0, good for most cases)
    """
    
    def __init__(self, alpha=0.95, gamma=3.0):
        super(FocalLoss, self).__init__()
        self.alpha = alpha
        self.gamma = gamma
    
    def forward(self, predictions, targets):
        """
        Args:
            predictions: Model output (batch, 1), values 0-1 after sigmoid
            targets: Ground truth (batch, 1), binary 0 or 1
        
        Returns:
            Scalar loss value
        """
        # Clamp predictions to avoid log(0)
        predictions = torch.clamp(predictions, min=1e-7, max=1 - 1e-7)
        
        # Binary Cross Entropy component
        bce = -targets * torch.log(predictions) - (1 - targets) * torch.log(1 - predictions)
        
        # Probability of correct classification
        p_t = predictions * targets + (1 - predictions) * (1 - targets)
        
        # Alpha weighting (HEAVILY favor positive/trade class for 1:11 imbalance)
        alpha_t = self.alpha * targets + (1 - self.alpha) * (1 - targets)
        
        # Focal modulation: (1 - p_t)^gamma
        focal_weight = (1 - p_t) ** self.gamma
        
        # Final loss
        loss = alpha_t * focal_weight * bce
        
        return loss.mean()


class LabelSmoothingBCE(nn.Module):
    """
    Binary Cross-Entropy with Label Smoothing.
    
    Instead of hard labels (0 or 1), uses soft labels:
      0 → smoothing (e.g., 0.05)
      1 → 1 - smoothing (e.g., 0.95)
    
    This prevents the model from becoming overconfident and
    improves generalization to unseen market conditions.
    """
    
    def __init__(self, smoothing=0.05):
        super(LabelSmoothingBCE, self).__init__()
        self.smoothing = smoothing
    
    def forward(self, predictions, targets):
        # Smooth labels
        targets_smooth = targets * (1 - self.smoothing) + 0.5 * self.smoothing
        
        return F.binary_cross_entropy(
            torch.clamp(predictions, 1e-7, 1 - 1e-7),
            targets_smooth
        )


class CombinedTradingLoss(nn.Module):
    """
    Combined loss function optimized for trading:
    
    Loss = w1 * FocalLoss + w2 * LabelSmoothingBCE
    
    Focal handles class imbalance, Label Smoothing prevents overconfidence.
    """
    
    def __init__(self, focal_weight=0.85, smooth_weight=0.15,
                 alpha=0.95, gamma=3.0, smoothing=0.05):
        super(CombinedTradingLoss, self).__init__()
        self.focal = FocalLoss(alpha=alpha, gamma=gamma)
        self.smooth_bce = LabelSmoothingBCE(smoothing=smoothing)
        self.w1 = focal_weight
        self.w2 = smooth_weight
    
    def forward(self, predictions, targets):
        return self.w1 * self.focal(predictions, targets) + \
               self.w2 * self.smooth_bce(predictions, targets)
