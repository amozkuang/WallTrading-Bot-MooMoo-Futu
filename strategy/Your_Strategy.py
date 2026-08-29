"""
By: LukeLab
Created on 09/20/2023
Version: 1.0
Last Modified: 09/27/2023

Major Updated: 04/04/2024, decision and order function furnish
Still in testing

updated: 04/09/2024, output formatting

# updated: 11/17/2024, final version for open source only
# Version 2.0
# for more info, please visit: https://www.patreon.com/LookAtWallStreet

Modified: 40-Week MACD Strategy
"""

import yfinance as yf
from moomoo import *
from strategy.Strategy import Strategy
import pandas as pd
from ta.trend import MACD
# import pandas_ta as pta
from utils.dataIO import read_json_file, write_json_file, logging_info
from utils.time_tool import is_market_hours


class Your_Strategy(Strategy):
    """
    This is a 40-week MACD strategy example.
    """

    def __init__(self, trader):
        super().__init__(trader)
        self.strategy_name = "MACD_40Week_Strategy"

        """⬇️⬇️⬇️ Strategy Settings ⬇️⬇️⬇️"""

        self.stock_trading_list = ["AAPL", "CRWD", "MU", "AMD", "GOOGL", "ISRG", "JNJ"]
        self.trading_qty = {
            # please set the trading quantity for each stock
            "AAPL": 10,
            "CRWD": 10,
            "MU": 10,
            "AMD": 10,
            "GOOGL": 5,
            "ISRG": 5,
            "JNJ": 10
        }

        self.trading_confirmation = True    # True to enable trading confirmation

        # please add any other settings here based on your strategy

        """⬆️⬆️⬆️ Strategy Settings ⬆️⬆️⬆️"""

        print(f"Strategy {self.strategy_name} initialized...")

    def strategy_decision(self):
        print("Strategy Decision running...")
        """ ⬇️⬇️⬇️ 40-Week MACD Strategy starts here ⬇️⬇️⬇️"""
        # MACD strategy based on 40 weeks of weekly data
        for stock in self.stock_trading_list:
            try:
                # 1. get 40 weeks of weekly stock data from yfinance
                df = yf.Ticker(stock).history(interval="1wk", actions=False, prepost=False, raise_errors=True)
                
                # Only process if we have enough data
                if len(df) < 40:
                    print(f"{stock}: Not enough data. Have {len(df)} weeks, need 40.")
                    continue

                # Keep only the last 40 weeks
                df = df.tail(40)

                # 2. calculate MACD indicator
                macd = MACD(df['Close'], window_fast=12, window_slow=26, window_sign=9)
                df['macd'] = macd.macd()
                df['macd_signal'] = macd.macd_signal()
                df['macd_diff'] = macd.macd_diff()

                price = df['Close'].iloc[-1]
                qty = self.trading_qty[stock]

                # 3. check the signal and place order
                # Buy signal: MACD crosses above the signal line
                if (df['macd'].iloc[-1] > df['macd_signal'].iloc[-1]) and (
                        df['macd'].iloc[-2] <= df['macd_signal'].iloc[-2]):
                    print(f'BUY Signal for {stock}')
                    self.strategy_make_trade(action='BUY', stock=stock, qty=qty, price=price)

                # Sell signal: MACD crosses below the signal line
                if (df['macd'].iloc[-1] < df['macd_signal'].iloc[-1]) and (
                        df['macd'].iloc[-2] >= df['macd_signal'].iloc[-2]):
                    print(f'SELL Signal for {stock}')
                    self.strategy_make_trade(action='SELL', stock=stock, qty=qty, price=price)

                time.sleep(1)  # sleep 1 second to avoid the quote limit
            except Exception as e:
                print(f"Strategy Error for {stock}: {e}")
                logging_info(f'{self.strategy_name}: {stock} - {e}')

        """ ⏫⏫⏫ 40-Week MACD Strategy ends here ⏫⏫⏫ """

        print("Strategy checked... Waiting next decision called...")
        print('-----------------------------------------------')

    """ ⬇️⬇️⬇️ Order related functions ⬇️⬇️⬇️"""

    def strategy_make_trade(self, action, stock, qty, price):
        if self.trading_confirmation:
            # check if trading confirmation is enabled first
            if action == 'BUY':
                # check the current buying power first
                acct_ret, acct_info = self.trader.get_account_info()
                if acct_ret == RET_OK:
                    current_cash = acct_info['cash']
                else:
                    print('Trader: Get Account Info failed: ', acct_info)
                    return False

                if current_cash > qty * price:
                    # before buy action, check if it has enough cash
                    if is_market_hours():
                        # market order
                        ret, data = self.trader.market_buy(stock, qty, price)
                    else:
                        # limit order for extended hours
                        ret, data = self.trader.limit_buy(stock, qty, price)

                    if ret == RET_OK:
                        # order placed successfully:
                        print(data)
                        self.save_order_history(data)
                        print('make trade success, show latest position:')
                        print(self.get_current_position())  # show the latest position after trade
                    else:
                        print('Trader: Buy failed: ', data)
                        logging_info(f'{self.strategy_name}: Buy failed: {data}')
                else:
                    print('Trader: Buy failed: Not enough cash to buy')
                    logging_info(f'{self.strategy_name}: Buy failed: Not enough cash to buy')

            if action == 'SELL':
                position_data = self.get_current_position()
                if not position_data:
                    # check current position first
                    return False

                if qty <= position_data[stock]["qty"]:
                    # before sell action, check if it has enough position to sell
                    if is_market_hours():
                        # market order
                        ret, data = self.trader.market_sell(stock, qty, price)
                    else:
                        # limit order for extended hours
                        ret, data = self.trader.limit_sell(stock, qty, price)
                    if ret == RET_OK:
                        print(data)
                        logging_info(f'{self.strategy_name}: {data}')
                        self.save_order_history(data)
                        print('make trade success, show latest position:')
                        print(self.get_current_position())  # show the latest position after trade
                    else:
                        print('Trader: Sell failed: ', data)
                        logging_info(f'{self.strategy_name}: Sell failed: {data}')
                else:
                    print('Trader: Sell failed: Not enough position to sell')
                    logging_info(f'{self.strategy_name}: Sell failed: Not enough position to sell')

    def save_order_history(self, data):
        file_data = read_json_file("order_history.json")
        data_dict = data.to_dict()
        new_dict = {}
        for key, v in data_dict.items():
            new_dict[key] = v[0]
        logging_info(f'{self.strategy_name}: {str(new_dict)}')

        if file_data:
            file_data.append(new_dict)
        else:
            file_data = [new_dict]
        write_json_file("order_history.json", file_data)

    # add any other functions you need here
