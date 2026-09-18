import joblib
scaler = joblib.load('models/scaler.pkl')
try:
    print(scaler.feature_names_in_)
except Exception as e:
    print(f"Error 1: {e}")
    print(scaler.n_features_in_)
