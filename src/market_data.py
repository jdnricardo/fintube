import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

class MarketData:
    def __init__(self):
        """Initialize market data processor."""
        self.symbols = {
            'S&P 500': '^GSPC',
            'NASDAQ': '^IXIC',
            'VIX': '^VIX'
        }
        self.periods = {
            '1 Month': 30,
            '3 Months': 90,
            '6 Months': 180
        }

    def get_market_performance(self):
        """Get market performance data for different time periods."""
        end_date = datetime.now()
        performance_data = []

        for symbol_name, symbol in self.symbols.items():
            ticker = yf.Ticker(symbol)
            
            for period_name, days in self.periods.items():
                start_date = end_date - timedelta(days=days)
                
                # Get historical data
                hist = ticker.history(start=start_date, end=end_date)
                
                if not hist.empty:
                    # Calculate performance metrics
                    start_price = hist['Close'].iloc[0]
                    end_price = hist['Close'].iloc[-1]
                    performance = ((end_price - start_price) / start_price) * 100
                    
                    # For VIX, calculate high-low range and median
                    if symbol == '^VIX':
                        high = hist['High'].max()
                        low = hist['Low'].min()
                        median = hist['Close'].median()
                        performance_data.append({
                            'symbol': symbol_name,
                            'period': period_name,
                            'performance': None,
                            'high': high,
                            'low': low,
                            'median': median
                        })
                    else:
                        performance_data.append({
                            'symbol': symbol_name,
                            'period': period_name,
                            'performance': performance,
                            'high': None,
                            'low': None,
                            'median': None
                        })

        return pd.DataFrame(performance_data)

    def get_market_summary(self):
        """Get a formatted summary of market performance."""
        df = self.get_market_performance()
        
        # Create separate dataframes for indices and VIX
        indices_df = df[df['symbol'] != 'VIX'].copy()
        vix_df = df[df['symbol'] == 'VIX'].copy()
        
        # Pivot indices data for better display
        indices_pivot = indices_df.pivot(
            index='symbol',
            columns='period',
            values='performance'
        ).round(2)
        
        # Pivot VIX data for better display
        vix_pivot = vix_df.pivot(
            index='symbol',
            columns='period',
            values=['high', 'low', 'median']
        ).round(2)
        
        return {
            'indices': indices_pivot,
            'vix': vix_pivot
        } 