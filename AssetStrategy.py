"""Asset Arbitrage Strategy Implementation

Implements a comprehensive volatility arbitrage strategy with risk management
features including position sizing, stop-losses, and portfolio exposure limits.

Author: Lake Forest College Quantitative Trading Team
"""

from AlgorithmImports import *
class AssetArbitrageStrategy:
    """Volatility arbitrage strategy with advanced risk management.
    
    This strategy combines multiple technical indicators to identify trading
    opportunities while maintaining strict risk controls through position
    sizing and stop-loss mechanisms.
    """
    def __init__(self, algorithm, symbol):
        """Initialize strategy with risk management parameters.
        
        Args:
            algorithm: QuantConnect algorithm instance
            symbol: Trading symbol for this strategy instance
        """
        self.algorithm = algorithm
        self.symbol = symbol
        self.long_trade_size = 0.05  # 5% of the portfolio for long trades
        self.short_trade_size = 0.03  # 3% of the portfolio for short trades
        self.long_stop_loss = 0.05  # 5% stop-loss for long trades
        self.short_stop_loss = 0.03  # 3% stop-loss for short trades
        self.max_portfolio_exposure = 0.80  # Maximum 80% portfolio exposure

    def Execute(self, indicators):
        """Execute trading logic based on technical indicators.
        
        Args:
            indicators: Dictionary containing technical indicator instances
                      (contrarian_bands, rsi, trend)
        """
        contrarian_bands = indicators["contrarian_bands"]
        rsi = indicators["rsi"]
        trend = indicators["trend"]

        if not contrarian_bands.HasSignal() or not rsi.HasSignal():
            return

        price = self.algorithm.Securities[self.symbol].Price
        holdings = self.algorithm.Portfolio[self.symbol].Quantity
        average_price = self.algorithm.Portfolio[self.symbol].AveragePrice

        if price is None or price <= 0:
            self.algorithm.Debug(f"Skipping {self.symbol}: Invalid price {price}")
            return

        # Portfolio Exposure Check
        portfolio_exposure = sum([holding.HoldingsValue for holding in self.algorithm.Portfolio.Values]) / self.algorithm.Portfolio.TotalPortfolioValue
        if portfolio_exposure > self.max_portfolio_exposure:
            self.algorithm.Debug(f"Skipping trade for {self.symbol}: Portfolio exposure exceeds limit ({portfolio_exposure:.2%})")
            return

        # Long Entry
        if holdings == 0 and price < contrarian_bands.bbands.LowerBand.Current.Value and rsi.rsi.Current.Value < 30 and trend.IsUptrend():
            self.algorithm.SetHoldings(self.symbol, self.long_trade_size)

        # Short Entry
        elif holdings == 0 and price > contrarian_bands.bbands.UpperBand.Current.Value and rsi.rsi.Current.Value > 70 and trend.IsDowntrend():
            self.algorithm.SetHoldings(self.symbol, -self.short_trade_size)

        # Stop-Loss for Long Positions
        if holdings > 0 and price < average_price * (1 - self.long_stop_loss):
            self.algorithm.Debug(f"Stop-loss triggered for long {self.symbol} at price {price}")
            self.algorithm.Liquidate(self.symbol)

        # Stop-Loss for Short Positions
        if holdings < 0 and price > average_price * (1 + self.short_stop_loss):
            self.algorithm.Debug(f"Stop-loss triggered for short {self.symbol} at price {price}")
            self.algorithm.Liquidate(self.symbol)

        # Long Exit
        if holdings > 0 and price >= contrarian_bands.bbands.MiddleBand.Current.Value:
            self.algorithm.Liquidate(self.symbol)

        # Short Exit
        if holdings < 0 and price <= contrarian_bands.bbands.MiddleBand.Current.Value:
            self.algorithm.Liquidate(self.symbol)
