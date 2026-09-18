import pandas as pd
from src.indicators import TechnicalIndicators

# Dummy DF
df = pd.read_csv('colab/export_data/market_data_1m.csv', nrows=1000)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df.set_index('timestamp', inplace=True)

df_features = TechnicalIndicators.apply_multi_timeframe_features(df)
features = [
    'close', 'SMA_20', 'EMA_50', 'RSI_14', 'MACD', 'plus_di', 'minus_di', 'ADX',
    'KC_Upper', 'KC_Lower', 'KC_Middle', 'volume_shock',
    '15m_EMA_50', '15m_SMA_20', '15m_RSI_14', '15m_MACD', '15m_ADX',
    '1H_EMA_50', '1H_RSI_14', '1H_ADX'
]
selected_features = []
for col in df_features.columns:
    if col in features or any(x in col for x in ['close', 'SMA', 'EMA', 'RSI', 'MACD', 'plus_di', 'minus_di', 'ADX', 'KC', 'volume_shock', 'ATR']):
        selected_features.append(col)

with open('features_out.txt', 'w') as f:
    f.write(str(len(selected_features)) + "\n")
    f.write(str(selected_features) + "\n")

