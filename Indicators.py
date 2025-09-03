"""Custom Technical Indicators for QuantConnect Trading Strategies

This module provides custom implementations of technical indicators including
Bollinger Bands, RSI, Historical Volatility, and Trend Filters optimized
for volatility arbitrage strategies.

Author: Lake Forest College Quantitative Trading Team
"""

from AlgorithmImports import *
import numpy as np
class CustomBollingerBands:
    """Custom Bollinger Bands implementation for contrarian signals.
    
    Uses standard Bollinger Bands to identify potential reversal points
    when price touches the upper or lower bands.
    """
    def __init__(self, algorithm, symbol, period=20, deviations=2):
        """Initialize Bollinger Bands indicator.
        
        Args:
            algorithm: QuantConnect algorithm instance
            symbol: Trading symbol
            period: Lookback period for moving average (default: 20)
            deviations: Number of standard deviations for bands (default: 2)
        """
        self.algorithm = algorithm
        self.symbol = symbol
        self.bbands = algorithm.BB(symbol, period, deviations, MovingAverageType.Simple, Resolution.Daily)

    def Update(self, data):
        if self.symbol in data and data[self.symbol] is not None:
            self.bbands.Update(data[self.symbol].EndTime, data[self.symbol].Close)

    def HasSignal(self):
        return self.bbands.IsReady


class RSIIndicator:
    """Relative Strength Index indicator for momentum analysis.
    
    Identifies overbought (>70) and oversold (<30) conditions
    to complement Bollinger Band signals.
    """
    def __init__(self, algorithm, symbol, period=14):
        self.algorithm = algorithm
        self.symbol = symbol
        self.rsi = algorithm.RSI(symbol, period, MovingAverageType.Simple, Resolution.Daily)

    def Update(self, data):
        if self.symbol in data and data[self.symbol] is not None:
            self.rsi.Update(data[self.symbol].EndTime, data[self.symbol].Close)

    def HasSignal(self):
        return self.rsi.IsReady


class HistoricalVolatility:
    """Historical volatility calculator using rolling window of returns.
    
    Calculates volatility based on logarithmic returns over a specified
    period to measure price movement intensity.
    """
    def __init__(self, algorithm, symbol, period=20):
        self.algorithm = algorithm
        self.symbol = symbol
        self.returns = RollingWindow[float](period)

    def Update(self, data):
        if self.symbol in data and data[self.symbol] is not None:
            price = data[self.symbol].Close
            if self.returns.Count > 0:
                previous_price = self.returns[0] if self.returns[0] != 0 else price
                log_return = np.log(price / previous_price) if previous_price > 0 else 0
                self.returns.Add(log_return)
            else:
                self.returns.Add(0)

    def GetVolatility(self):
        if self.returns.IsReady:
            return np.std(list(self.returns))
        return None


class TrendFilter:
    """Trend direction filter using Simple Moving Average.
    
    Determines market trend direction by comparing current price
    to a longer-term moving average.
    """
    def __init__(self, algorithm, symbol, sma_period=50):
        self.algorithm = algorithm
        self.symbol = symbol
        self.sma = algorithm.SMA(symbol, sma_period, Resolution.Daily)

    def Update(self, data):
        if self.symbol in data and data[self.symbol] is not None:
            self.sma.Update(data[self.symbol].EndTime, data[self.symbol].Close)

    def IsUptrend(self):
        if self.sma.IsReady:
            price = self.algorithm.Securities[self.symbol].Price
            return price > self.sma.Current.Value
        return False

    def IsDowntrend(self):
        if self.sma.IsReady:
            price = self.algorithm.Securities[self.symbol].Price
            return price < self.sma.Current.Value
        return False
