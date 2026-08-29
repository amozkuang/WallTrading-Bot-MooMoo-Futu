# Dev
# 03/29/2024
# LukeLab for LookAtWallStreet
# Version 1.0
# Programming Trading based on MooMoo API/OpenD

"""
# updated: 11/17/2024, final version for open source only
# Version 2.0
# for more info, please visit: https://www.patreon.com/LookAtWallStreet

# UPDATED: 08/29/2026
# Version 3.1 - Twice-weekly execution (Mon 8pm, Fri 8am SG time)
"""

# MooMoo API Documentation, English:
# https://openapi.moomoo.com/moomoo-api-doc/en/intro/intro.html
# 官方文档，中文:
# https://openapi.moomoo.com/moomoo-api-doc/intro/intro.html

from moomoo import *
import schedule
from pytz import timezone

from env._secrete import MooMoo_PWD
from strategy.Your_Strategy import Your_Strategy
from utils.dataIO import get_current_time, print_current_time, logging_info
from utils.time_tool import is_market_and_extended_hours, is_trading_day

""" ⬇️ project setup ⬇️ """
'''
Step 1: Set up the environment information
'''
# Environment Variables
MOOMOOOPEND_ADDRESS = "127.0.0.1"  # should be same as the OpenD host IP, just keep as default
MOOMOOOPEND_PORT = 11112  # should be same as the OpenD port number, make sure keep both the same
TRADING_ENVIRONMENT = TrdEnv.REAL  # set up trading environment, real, or simulate/paper trading
# REAL = "REAL"
# SIMULATE = "SIMULATE"

'''
Step 2: Set up the account information
'''
TRADING_PWD = MooMoo_PWD  # set up the trading password in the env/_secrete.py file
SECURITY_FIRM = SecurityFirm.FUTUINC  # set up the security firm based on your broker account registration
# for U.S. account, use FUTUINC, (default)
# for HongKong account, use FUTUSECURITIES
# for Singapore account, use FUTUSG
# for Australia account, use FUTUAU

'''
Step 3: Set up the trading information
'''
FILL_OUTSIDE_MARKET_HOURS = True  # enable if order fills on extended hours
TRADING_MARKET = TrdMarket.US  # set up the trading market, US market, HK for HongKong, etc.
# NONE = "N/A"
# HK = "HK"
# US = "US"
# CN = "CN"
# HKCC = "HKCC"
# FUTURES = "FUTURES"

""" ⏫ project setup ⏫ """

# Timezone for SG time (UTC+8)
SG_TZ = timezone('Asia/Singapore')

# Trader class:
class Trader:
    def __init__(self, name='Your Trader Name'):
        self.name = name
        self.trade_context = None

    def init_context(self):
        self.trade_context = OpenSecTradeContext(filter_trdmarket=TRADING_MARKET, host=MOOMOOOPEND_ADDRESS,
                                                 port=MOOMOOOPEND_PORT, security_firm=SECURITY_FIRM)

    def close_context(self):
        self.trade_context.close()

    def unlock_trade(self):
        if TRADING_ENVIRONMENT == TrdEnv.REAL:
            ret, data = self.trade_context.unlock_trade(TRADING_PWD)
            if ret != RET_OK:
                print('Unlock trade failed: ', data)
                return False
            print('Unlock Trade success!')
        return True

    def market_sell(self, stock, quantity, price):
        self.init_context()
        if self.unlock_trade():
            code = f'US.{stock}'
            ret, data = self.trade_context.place_order(price=price, qty=quantity, code=code, trd_side=TrdSide.SELL,
                                                       order_type=OrderType.MARKET, trd_env=TRADING_ENVIRONMENT)
            if ret != RET_OK:
                print('Trader: Market Sell failed: ', data)
                self.close_context()
                return ret, data
            print('Trader: Market Sell success!')
            self.close_context()
            return ret, data
        else:
            data = 'Trader: Market Sell failed: unlock trade failed'
            print(data)
            self.close_context()
            return -1, data

    def market_buy(self, stock, quantity, price):
        self.init_context()
        if self.unlock_trade():
            code = f'US.{stock}'
            ret, data = self.trade_context.place_order(price=price, qty=quantity, code=code, trd_side=TrdSide.BUY,
                                                       order_type=OrderType.MARKET, trd_env=TRADING_ENVIRONMENT)
            if ret != RET_OK:
                print('Trader: Market Buy failed: ', data)
                self.close_context()
                return ret, data
            print('Trader: Market Buy success!')
            self.close_context()
            return ret, data
        else:
            data = 'Trader: Market Buy failed: unlock trade failed'
            print(data)
            self.close_context()
            return -1, data

    def limit_sell(self, stock, quantity, price):
        self.init_context()
        if self.unlock_trade():
            code = f'US.{stock}'
            ret, data = self.trade_context.place_order(price=price, qty=quantity, code=code, trd_side=TrdSide.SELL,
                                                       order_type=OrderType.NORMAL, trd_env=TRADING_ENVIRONMENT,
                                                       fill_outside_rth=FILL_OUTSIDE_MARKET_HOURS)
            if ret != RET_OK:
                print('Trader: Limit Sell failed: ', data)
                self.close_context()
                return ret, data
            print('Trader: Limit Sell success!')
            self.close_context()
            return ret, data
        else:
            data = 'Trader: Limit Sell failed: unlock trade failed'
            print(data)
            self.close_context()
            return -1, data

    def limit_buy(self, stock, quantity, price):
        self.init_context()
        if self.unlock_trade():
            code = f'US.{stock}'
            ret, data = self.trade_context.place_order(price=price, qty=quantity, code=code, trd_side=TrdSide.BUY,
                                                       order_type=OrderType.NORMAL, trd_env=TRADING_ENVIRONMENT,
                                                       fill_outside_rth=FILL_OUTSIDE_MARKET_HOURS)
            if ret != RET_OK:
                print('Trader: Limit Buy failed: ', data)
                self.close_context()
                return ret, data
            print('Trader: Limit Buy success!')
            self.close_context()
            return ret, data
        else:
            data = 'Trader: Limit Buy failed: unlock trade failed'
            print(data)
            self.close_context()
            return -1, data

    def get_account_info(self):
        self.init_context()
        if self.unlock_trade():
            ret, data = self.trade_context.accinfo_query()
            if ret != RET_OK:
                print('Trader: Get Account Info failed: ', data)
                self.close_context()
                return ret, data

            acct_info = {
                # https://openapi.moomoo.com/moomoo-api-doc/en/trade/get-funds.html
                # Obsolete. Please use 'us_cash' or other fields to get the cash of each currency.
                # updated 01-07-2025
                'cash': round(data["us_cash"][0], 2),
                'total_assets': round(data["total_assets"][0], 2),
                'market_value': round(data["market_val"][0], 2),
            }
            self.close_context()
            logging_info('Trader: Get Account Info success!')
            return ret, acct_info
        else:
            data = 'Trader: Get Account Info failed: unlock trade failed'
            print(data)
            self.close_context()
            return -1, data

    def get_positions(self):
        self.init_context()
        if self.unlock_trade():
            ret, data = self.trade_context.position_list_query()
            if ret != RET_OK:
                print('Trader: Get Positions failed: ', data)
                self.close_context()
                return ret, data
            # refactor the data
            data['code'] = data['code'].str[3:]
            data_dict = data.set_index('code').to_dict(orient='index')
            self.close_context()
            logging_info('Trader: Get Positions success!')
            return ret, data_dict
        else:
            data = 'Trader: Get Positions failed: unlock trade failed'
            print(data)
            self.close_context()
            return -1, data


if __name__ == '__main__':

    print(get_current_time(), 'TradingBOT is running...')
    print("Execution Schedule: Monday 8:00 PM SG time + Friday 8:00 AM SG time")
    print("=" * 60)
    
    # Create a trader and strategy object
    trader = Trader()
    strategy = Your_Strategy(trader)
    print("trader and strategy objects created...")

    # schedule the task - Twice weekly execution
    bot_task = schedule.Scheduler()
    
    # Monday 8:00 PM SG time (UTC+8)
    bot_task.every().monday.at("20:00", tz=SG_TZ).do(strategy.strategy_decision)
    
    # Friday 8:00 AM SG time (UTC+8)
    bot_task.every().friday.at("08:00", tz=SG_TZ).do(strategy.strategy_decision)

    # print the time every hour showing bot running...
    bkg_task = schedule.Scheduler()
    bkg_task.every().hour.at(":00").do(print_current_time)

    print("schedule the task...")
    print("Next scheduled executions:")
    print("  - Every Monday at 8:00 PM SG time")
    print("  - Every Friday at 8:00 AM SG time")
    print("=" * 60)

    # loop and keep the schedule running
    while True:
        bkg_task.run_pending()
        if is_market_and_extended_hours() and is_trading_day():
            bot_task.run_pending()  # please handle all error in your strategy

        time.sleep(1)
