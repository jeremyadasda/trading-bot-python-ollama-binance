import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import pickle
import os
from technical_indicators import TechnicalIndicators

class MLPredictor:
    def __init__(self, model_path="bot_logic/trading_model.pkl"):
        self.model_path = model_path
        self.model = None
        self.feature_names = None  # Store feature names used during training
        self._load_model()

    def _load_model(self):
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, 'rb') as f:
                    loaded_data = pickle.load(f)
                    if isinstance(loaded_data, dict):
                        # New format with feature names
                        self.model = loaded_data['model']
                        self.feature_names = loaded_data['feature_names']
                    else:
                        # Old format, just the model
                        self.model = loaded_data
                    print("ML Model loaded successfully.")
            except Exception as e:
                print(f"Error loading ML model: {e}")
                self.model = None
                self.feature_names = None

    def _save_model(self):
        try:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            # Save both model and feature names
            save_data = {'model': self.model, 'feature_names': self.feature_names}
            with open(self.model_path, 'wb') as f:
                pickle.dump(save_data, f)
            print("ML Model saved successfully.")
        except Exception as e:
            print(f"Error saving ML model: {e}")

    def _calculate_features(self, df):
        """Calculate all features for the given dataframe"""
        # Calculate technical indicators
        indicators = TechnicalIndicators.get_all_indicators(df)
        
        # Add indicators to dataframe
        for key, value in indicators.items():
            if value is not None:
                df[key] = value
        
        return df

    def train_on_data(self, df):
        """Trains a model on the provided feature DataFrame."""
        if df is None or len(df) < 50:
            print("Insufficient data for training ML model.")
            return False

        # Calculate all features
        df_with_features = self._calculate_features(df)

        # Define features (avoiding targets and raw prices)
        features = [col for col in df_with_features.columns if col not in ['ts', 'open', 'high', 'low', 'close', 'vol', 'close_ts', 'qav', 'num_trades', 'taker_base', 'taker_quote', 'ignore', 'target', 'target_return']]
        
        X = df_with_features[features]
        y = df_with_features['target']

        print(f"Training ML model with {len(X)} samples and {len(features)} features...")
        self.model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
        self.model.fit(X, y)
        
        # Store the feature names used during training
        self.feature_names = features
        self._save_model()
        return True

    def predict_confidence(self, latest_df):
        """Predicts the probability of the target (Price up > 1% in 4h)."""
        if self.model is None:
            return 0.5 # Neutral
        
        try:
            # Calculate all features
            df_with_features = self._calculate_features(latest_df)
            
            # Use the exact same features that were used during training
            if self.feature_names is not None:
                # Get only the features that were used during training
                available_features = [f for f in self.feature_names if f in df_with_features.columns]
                
                if not available_features:
                    print(f"No matching features found. Expected: {self.feature_names[:10]}..., Available: {df_with_features.columns.tolist()[:10]}...")
                    return 0.5
                
                # Check for missing features
                missing_features = [f for f in self.feature_names if f not in df_with_features.columns]
                if missing_features:
                    print(f"Missing features: {missing_features[:10]}...")
                    # For missing features, add them as NaN columns
                    for feature in missing_features:
                        df_with_features[feature] = np.nan
                
                # Ensure we have all the features the model expects
                for feature in self.feature_names:
                    if feature not in df_with_features.columns:
                        df_with_features[feature] = np.nan
                
                # Use the training features in the correct order
                last_row = df_with_features[self.feature_names].tail(1)
            else:
                # Fallback: use all available features
                features = [col for col in df_with_features.columns if col not in ['ts', 'open', 'high', 'low', 'close', 'vol', 'close_ts', 'qav', 'num_trades', 'taker_base', 'taker_quote', 'ignore', 'target', 'target_return']]
                last_row = df_with_features[features].tail(1)
            
            # Probability of class 1 (Bullish)
            probs = self.model.predict_proba(last_row)[0]
            bull_prob = probs[1]
            return bull_prob
        except Exception as e:
            print(f"ML Prediction Error: {e}")
            return 0.5