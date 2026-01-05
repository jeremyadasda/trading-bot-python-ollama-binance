import pandas as pd
import pandas_ta as ta
import numpy as np
from statsmodels.tsa.stattools import adfuller, coint
from statsmodels.regression.linear_model import OLS
from scipy.stats import kurtosis

class TechnicalIndicators:
    @staticmethod
    def calculate_ema(df, period):
        """Calculate Exponential Moving Average"""
        return ta.ema(df['close'], length=period)

    @staticmethod
    def calculate_sma(df, period):
        """Calculate Simple Moving Average"""
        return ta.sma(df['close'], length=period)

    @staticmethod
    def calculate_rsi(df, period=14):
        """Calculate Relative Strength Index"""
        return ta.rsi(df['close'], length=period)

    @staticmethod
    def calculate_atr(df, period=14):
        """Calculate Average True Range"""
        return ta.atr(df['high'], df['low'], df['close'], length=period)

    @staticmethod
    def calculate_macd(df):
        """Calculate MACD"""
        return ta.macd(df['close'])

    @staticmethod
    def calculate_volume_avg(df, period):
        """Calculate average volume over period"""
        return df['vol'].rolling(window=period).mean()

    @staticmethod
    def calculate_z_score(df1, df2):
        """Calculate z-score for spread between two assets"""
        spread = df1['close'] - df2['close']
        mean_spread = spread.rolling(window=20).mean()
        std_spread = spread.rolling(window=20).std()
        z_score = (spread - mean_spread) / std_spread
        return z_score

    @staticmethod
    def ols_regression(y, x):
        """Perform OLS regression and return residuals"""
        model = OLS(y, x).fit()
        residuals = model.resid
        return residuals, model.params

    @staticmethod
    def adf_test(series):
        """Augmented Dickey-Fuller test for stationarity"""
        result = adfuller(series, autolag='AIC')
        return result[0], result[1]  # statistic, p-value

    @staticmethod
    def cointegration_test(series1, series2):
        """Test for cointegration between two series"""
        score, p_value, _ = coint(series1, series2)
        return score, p_value

    @staticmethod
    def calculate_kurtosis(series, period):
        """Calculate rolling kurtosis"""
        return series.rolling(window=period).apply(lambda x: kurtosis(x, fisher=True))

    @staticmethod
    def log_difference_ma(series, period):
        """Calculate moving average of log differences"""
        log_diff = np.log(series / series.shift(1))
        return log_diff.rolling(window=period).mean()

    @staticmethod
    def correlation_coefficient(series1, series2, period):
        """Calculate rolling correlation"""
        return series1.rolling(window=period).corr(series2)

    @staticmethod
    def bollinger_bands(df, period=20, std=2):
        """Calculate Bollinger Bands"""
        return ta.bbands(df['close'], length=period, std=std)

    @staticmethod
    def stochastic_oscillator(df, k_period=14, d_period=3):
        """Calculate Stochastic Oscillator"""
        return ta.stoch(df['high'], df['low'], df['close'], k=k_period, d=d_period)

    @staticmethod
    def williams_r(df, period=14):
        """Calculate Williams %R"""
        return ta.willr(df['high'], df['low'], df['close'], length=period)

    @staticmethod
    def check_crossover(series1, series2):
        """Check if series1 crossed above series2 recently"""
        prev1 = series1.shift(1)
        prev2 = series2.shift(1)
        current1 = series1
        current2 = series2
        return (prev1 <= prev2) & (current1 > current2)

    @staticmethod
    def check_crossunder(series1, series2):
        """Check if series1 crossed below series2 recently"""
        prev1 = series1.shift(1)
        prev2 = series2.shift(1)
        current1 = series1
        current2 = series2
        return (prev1 >= prev2) & (current1 < current2)

    @staticmethod
    def volume_ratio(df, period):
        """Calculate current volume relative to average"""
        avg_vol = df['vol'].rolling(window=period).mean()
        return df['vol'] / avg_vol

    @staticmethod
    def price_change_pct(df, periods):
        """Calculate percentage change over periods"""
        return df['close'].pct_change(periods=periods)

    @staticmethod
    def volatility_atr(df, period=14):
        """Calculate volatility using ATR"""
        return TechnicalIndicators.calculate_atr(df, period)

    @staticmethod
    def mean_reversion_z_score(df, period=20):
        """Calculate z-score for mean reversion"""
        ma = df['close'].rolling(window=period).mean()
        std = df['close'].rolling(window=period).std()
        return (df['close'] - ma) / std

    @staticmethod
    def sharpe_ratio(returns, risk_free_rate=0.0):
        """Calculate Sharpe ratio"""
        excess_returns = returns - risk_free_rate
        return excess_returns.mean() / excess_returns.std() * np.sqrt(252)  # Annualized

    @staticmethod
    def sortino_ratio(returns, risk_free_rate=0.0):
        """Calculate Sortino ratio"""
        excess_returns = returns - risk_free_rate
        downside_returns = excess_returns[excess_returns < 0]
        return excess_returns.mean() / downside_returns.std() * np.sqrt(252)

    @staticmethod
    def max_drawdown(series):
        """Calculate maximum drawdown"""
        cumulative = (1 + series).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min()

    @staticmethod
    def get_all_indicators(df):
        """Compute all relevant indicators for the dataframe"""
        indicators = {}

        # Basic EMAs and SMAs
        indicators['ema_20'] = TechnicalIndicators.calculate_ema(df, 20)
        indicators['ema_50'] = TechnicalIndicators.calculate_ema(df, 50)
        indicators['ema_200'] = TechnicalIndicators.calculate_ema(df, 200)
        indicators['sma_20'] = TechnicalIndicators.calculate_sma(df, 20)
        indicators['sma_50'] = TechnicalIndicators.calculate_sma(df, 50)
        indicators['sma_200'] = TechnicalIndicators.calculate_sma(df, 200)

        # Oscillators
        indicators['rsi_14'] = TechnicalIndicators.calculate_rsi(df, 14)
        indicators['rsi_10'] = TechnicalIndicators.calculate_rsi(df, 10)

        # Volatility
        indicators['atr_14'] = TechnicalIndicators.calculate_atr(df, 14)

        # MACD
        macd_df = TechnicalIndicators.calculate_macd(df)
        # Add all MACD columns to indicators (without debug print)
        if macd_df is not None:
            for col in macd_df.columns:
                indicators[col] = macd_df[col]

        # Volume
        indicators['vol_avg_20'] = TechnicalIndicators.calculate_volume_avg(df, 20)
        indicators['vol_ratio_20'] = TechnicalIndicators.volume_ratio(df, 20)

        # Bollinger Bands
        bb_df = TechnicalIndicators.bollinger_bands(df)
        # Add all Bollinger Band columns to indicators (without debug print)
        for col in bb_df.columns:
            indicators[col] = bb_df[col]

        # Stochastic
        stoch_df = TechnicalIndicators.stochastic_oscillator(df)
        # Add all Stochastic columns to indicators (without debug print)
        if stoch_df is not None:
            for col in stoch_df.columns:
                indicators[col] = stoch_df[col]

        # Williams %R
        indicators['williams_r'] = TechnicalIndicators.williams_r(df)

        # Momentum
        indicators['roc_1'] = TechnicalIndicators.price_change_pct(df, 1)
        indicators['roc_5'] = TechnicalIndicators.price_change_pct(df, 5)
        indicators['roc_10'] = TechnicalIndicators.price_change_pct(df, 10)

        # Mean Reversion
        indicators['z_score_mr'] = TechnicalIndicators.mean_reversion_z_score(df)

        # Crossovers
        indicators['ema20_cross_above_ema50'] = TechnicalIndicators.check_crossover(indicators['ema_20'], indicators['ema_50'])
        indicators['ema20_cross_below_ema50'] = TechnicalIndicators.check_crossunder(indicators['ema_20'], indicators['ema_50'])

        return indicators