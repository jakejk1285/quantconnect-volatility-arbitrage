"""QuantConnect Volatility Arbitrage Algorithm

A sophisticated trading strategy that combines technical indicators to identify
arbitrage opportunities across equity and cryptocurrency markets using volatility
signals and contrarian approaches.

Author: Lake Forest College Quantitative Trading Team
League: https://www.quantconnect.com/league/19302/2025-q3/lake-forest-college/p1
"""

from AlgorithmImports import *
from Indicators import CustomBollingerBands, RSIIndicator, HistoricalVolatility, TrendFilter
from AssetStrategy import AssetArbitrageStrategy


class VolatilityArbitrage(QCAlgorithm):
    """Main algorithm class implementing volatility arbitrage strategy.
    
    This algorithm trades on volatility signals using Bollinger Bands, RSI,
    and trend filters across a diversified portfolio of equities and cryptocurrencies.
    """
    def Initialize(self):
        """Initialize the algorithm with universe selection and indicators."""
        self.SetStartDate(2023, 10, 1)
        self.SetEndDate(2023, 12, 31)
        self.SetCash(100000)

        # Add cryptocurrencies
        self.crypto_symbols = ["BTCUSD", "ETHUSD", "SOLUSD"]
        for crypto in self.crypto_symbols:
            self.AddCrypto(crypto, Resolution.Daily)

        # Universe selection for 100 stocks
        self.AddUniverse(self.CoarseSelectionFunction)

        # Extended warm-up period for better historical volatility data
        self.SetWarmUp(timedelta(days=60))

        self.symbol_data = {}

    def CoarseSelectionFunction(self, coarse):
        """Select top 100 liquid stocks by dollar volume.
        
        Args:
            coarse: List of coarse fundamental data
            
        Returns:
            List of selected symbols including crypto assets
        """
        # Select liquid equities with price > $20 and sort by dollar volume in descending order
        filtered = [x for x in coarse if x.Price > 20 and x.DollarVolume > 1e7]
        sorted_by_volume = sorted(filtered, key=lambda x: x.DollarVolume, reverse=True)
        selected = [x.Symbol for x in sorted_by_volume[:100]]  # Top 100 stocks
        return selected + self.crypto_symbols  # Add cryptos to the universe

    def OnSecuritiesChanged(self, changes):
        """Handle universe changes by initializing indicators and strategies.
        
        Args:
            changes: SecurityChanges object containing added/removed securities
        """
        for added in changes.AddedSecurities:
            symbol = added.Symbol
            if symbol not in self.symbol_data:
                self.symbol_data[symbol] = {
                    "indicators": {
                        "contrarian_bands": CustomBollingerBands(self, symbol),
                        "rsi": RSIIndicator(self, symbol),
                        "hist_vol": HistoricalVolatility(self, symbol),
                        "trend": TrendFilter(self, symbol)
                    },
                    "strategy": AssetArbitrageStrategy(self, symbol)
                }

        for removed in changes.RemovedSecurities:
            symbol = removed.Symbol
            if symbol in self.symbol_data:
                del self.symbol_data[symbol]

    def OnData(self, data):
        """Process incoming market data and execute trading logic.
        
        Args:
            data: Dictionary containing price data for all securities
        """
        if self.IsWarmingUp:
            return

        for symbol, data_set in self.symbol_data.items():
            if symbol in data:
                indicators = data_set["indicators"]
                indicators["contrarian_bands"].Update(data)
                indicators["rsi"].Update(data)
                indicators["hist_vol"].Update(data)
                indicators["trend"].Update(data)
                data_set["strategy"].Execute(indicators)
