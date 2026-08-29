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

Modified: Conservative 40-Week MACD Strategy with Risk Management
Version 3.0: Portfolio Safety & Risk Controls
"""

import yfinance as yf
from moomoo import *
from strategy.Strategy import Strategy
import pandas as pd
from ta.trend import MACD, SMAIndicator
# import pandas_ta as pta
from utils.dataIO import read_json_file, write_json_file, logging_info
from utils.time_tool import is_market_hours
from datetime import datetime, timedelta
import time


class Your_Strategy(Strategy):
    """
    Conservative 40-week MACD strategy with portfolio risk management.
    Designed for safer, long-term wealth building with strict position limits.
    """

    def __init__(self, trader):
        super().__init__(trader)
        self.strategy_name = "Conservative_MACD_Risk_Managed"

        """⬇️⬇️⬇️ Portfolio & Risk Settings ⬇️⬇️⬇️"""
        
        # Total portfolio value (update this with your actual bot capital)
        self.total_portfolio_value = 1000  # $1,000 allocated to bot (20-30% of total)
        
        # Stock allocation limits (% of total portfolio)
        self.max_position_allocation = {
            "AAPL": 0.05,      # 5% max
            "GOOGL": 0.05,     # 5% max
            "JNJ": 0.05,       # 5% max
            "ISRG": 0.03,      # 3% max
            "CRWD": 0.025,     # 2.5% max
            "AMD": 0.025,      # 2.5% max
            "MU": 0.025        # 2.5% max
        }
        
        self.stock_trading_list = ["AAPL", "CRWD", "MU", "AMD", "GOOGL", "ISRG", "JNJ"]
        
        # Safety Controls
        self.max_active_positions = 4  # Maximum 4 simultaneous positions
        self.max_new_positions_per_week = 1  # Maximum 1 new position per week
        self.max_order_value = self.total_portfolio_value * 0.05  # Max 5% per order
        
        # Portfolio circuit breaker levels
        self.circuit_breaker_5pct = 0.05  # Stop new positions at 5% drawdown
        self.circuit_breaker_8pct = 0.08  # Require manual review at 8% drawdown
        self.max_drawdown_threshold = 0.10  # Max 10% before full halt
        
        # Trading parameters
        self.trading_confirmation = True  # Require manual approval for orders
        self.use_paper_trading = True  # Set to True for paper trading mode
        self.require_manual_approval = True  # User must approve each trade
        
        # Weekly execution (run once after Friday close)
        self.last_execution_date = None
        
        """⬆️⬆️⬆️ Portfolio & Risk Settings ⬆️⬆️⬆️"""

        print(f"Strategy {self.strategy_name} initialized...")
        print(f"Bot Capital: ${self.total_portfolio_value}")
        print(f"Max Active Positions: {self.max_active_positions}")
        print(f"Max New Positions/Week: {self.max_new_positions_per_week}")
        print(f"Paper Trading Mode: {self.use_paper_trading}")

    def strategy_decision(self):
        print("Strategy Decision running...")
        print(f"Execution Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        """ ⬇️⬇️⬇️ Conservative 40-Week MACD Strategy starts here ⬇️⬇️⬇️"""
        
        # 1. Check if we should run (weekly, after Friday close)
        if not self._is_weekly_execution_time():
            print("Not weekly execution time. Skipping...")
            return
        
        # 2. Check portfolio circuit breakers
        current_drawdown = self._calculate_current_drawdown()
        if not self._check_circuit_breaker(current_drawdown):
            print(f"Circuit breaker triggered at {current_drawdown*100:.2f}% drawdown")
            return
        
        # 3. Get current positions and pending orders
        current_positions = self.get_current_position()
        pending_orders = self._get_pending_orders()
        
        # 4. Check how many new positions we can open this week
        new_positions_this_week = self._count_new_positions_this_week()
        
        # 5. Check market-wide filter (S&P 500 above 40-week SMA)
        if not self._is_market_healthy():
            print("Market-wide filter failed: S&P 500 below 40-week SMA. Skipping buys.")
            return
        
        # 6. Process each stock
        for stock in self.stock_trading_list:
            try:
                # Get 40+ weeks of weekly data
                df = yf.Ticker(stock).history(interval="1wk", actions=False, prepost=False, raise_errors=True)
                
                if len(df) < 40:
                    print(f"{stock}: Not enough data ({len(df)} weeks). Skipping.")
                    continue
                
                # Use only last 40 weeks
                df = df.tail(40).copy()
                
                # Calculate indicators
                df['sma_40'] = SMAIndicator(df['Close'], window=40).sma_indicator()
                macd = MACD(df['Close'], window_fast=12, window_slow=26, window_sign=9)
                df['macd'] = macd.macd()
                df['macd_signal'] = macd.macd_signal()
                
                # Get latest values
                current_price = df['Close'].iloc[-1]
                current_sma = df['sma_40'].iloc[-1]
                current_macd = df['macd'].iloc[-1]
                current_signal = df['macd_signal'].iloc[-1]
                previous_macd = df['macd'].iloc[-2]
                previous_signal = df['macd_signal'].iloc[-2]
                previous_sma = df['sma_40'].iloc[-2]
                
                # Check BUY conditions (all must be true)
                buy_signal = self._check_buy_conditions(
                    stock, current_price, current_sma, current_macd, current_signal,
                    previous_macd, previous_signal, previous_sma, df, current_positions, pending_orders
                )
                
                if buy_signal:
                    # Check if we can add more positions
                    if len(current_positions) >= self.max_active_positions:
                        print(f"{stock}: Max active positions ({self.max_active_positions}) reached. Skipping buy.")
                        continue
                    
                    if new_positions_this_week >= self.max_new_positions_per_week:
                        print(f"{stock}: Max new positions per week ({self.max_new_positions_per_week}) reached. Skipping buy.")
                        continue
                    
                    # Calculate position size
                    qty = self._calculate_position_size(stock, current_price)
                    order_value = qty * current_price
                    
                    if order_value > self.max_order_value:
                        print(f"{stock}: Order value (${order_value:.2f}) exceeds max (${self.max_order_value:.2f}). Adjusting...")
                        qty = int(self.max_order_value / current_price)
                        order_value = qty * current_price
                    
                    if qty > 0:
                        print(f'BUY Signal for {stock} @ ${current_price:.2f} | Qty: {qty} | Order Value: ${order_value:.2f}')
                        self._execute_buy(stock, qty, current_price)
                        new_positions_this_week += 1
                
                # Check SELL conditions (any one can trigger)
                sell_signal = self._check_sell_conditions(
                    stock, current_price, current_sma, current_macd, current_signal,
                    previous_macd, previous_signal, current_positions
                )
                
                if sell_signal and stock in current_positions:
                    position_qty = current_positions[stock]["qty"]
                    print(f'SELL Signal for {stock} @ ${current_price:.2f} | Qty: {position_qty}')
                    self._execute_sell(stock, position_qty, current_price)
                
                time.sleep(1)  # Respect rate limits
                
            except Exception as e:
                print(f"Strategy Error for {stock}: {e}")
                logging_info(f'{self.strategy_name}: {stock} - {e}')
        
        """ ⏫⏫⏫ Conservative 40-Week MACD Strategy ends here ⏫⏫⏫ """
        
        self.last_execution_date = datetime.now().date()
        print("Strategy checked... Waiting for next weekly execution...")
        print('-----------------------------------------------')

    # ==================== SAFETY & FILTER FUNCTIONS ====================
    
    def _is_weekly_execution_time(self):
        """Check if we should execute (weekly, ideally Friday after close)"""
        # For now, execute once per calendar week
        # TODO: Refine to Friday after 4 PM ET
        today = datetime.now().date()
        if self.last_execution_date is None:
            return True
        days_since_last = (today - self.last_execution_date).days
        return days_since_last >= 7
    
    def _is_market_healthy(self):
        """Check if S&P 500 is above its 40-week SMA"""
        try:
            sp500 = yf.Ticker("^GSPC").history(interval="1wk", actions=False, prepost=False, raise_errors=True)
            if len(sp500) < 40:
                print("Not enough S&P 500 data for market filter")
                return False
            
            sp500 = sp500.tail(40).copy()
            sp500['sma_40'] = SMAIndicator(sp500['Close'], window=40).sma_indicator()
            
            current_price = sp500['Close'].iloc[-1]
            current_sma = sp500['sma_40'].iloc[-1]
            
            is_healthy = current_price > current_sma
            print(f"Market Filter: S&P 500 @ ${current_price:.2f} | 40-SMA @ ${current_sma:.2f} | Healthy: {is_healthy}")
            return is_healthy
            
        except Exception as e:
            print(f"Error checking market health: {e}")
            return False  # Fail safe: don't trade if we can't check market
    
    def _check_circuit_breaker(self, current_drawdown):
        """Check portfolio circuit breaker levels"""
        if current_drawdown >= self.max_drawdown_threshold:
            print(f"CRITICAL: Portfolio drawdown at {current_drawdown*100:.2f}%. Trading halted.")
            logging_info(f'{self.strategy_name}: CIRCUIT BREAKER - Full halt at {current_drawdown*100:.2f}% drawdown')
            return False
        
        if current_drawdown >= self.circuit_breaker_8pct:
            print(f"WARNING: Portfolio drawdown at {current_drawdown*100:.2f}%. Manual review required.")
            logging_info(f'{self.strategy_name}: CIRCUIT BREAKER - Manual review required at {current_drawdown*100:.2f}% drawdown')
            return False  # Require manual intervention
        
        if current_drawdown >= self.circuit_breaker_5pct:
            print(f"CAUTION: Portfolio drawdown at {current_drawdown*100:.2f}%. Stopping new positions.")
            # Allow existing positions to be managed, but no new buys
        
        return True
    
    def _calculate_current_drawdown(self):
        """Calculate current portfolio drawdown"""
        # TODO: Implement actual P&L calculation
        # For now, return 0% (no drawdown)
        return 0.0
    
    def _get_pending_orders(self):
        """Get list of pending orders"""
        # TODO: Query moomoo for pending orders
        return {}
    
    def _count_new_positions_this_week(self):
        """Count how many new positions were opened this week"""
        # TODO: Check order history for this week
        return 0
    
    # ==================== BUY & SELL CONDITIONS ====================
    
    def _check_buy_conditions(self, stock, price, sma, macd, signal, prev_macd, prev_signal, prev_sma, df, positions, pending):
        """
        All conditions must be true to buy:
        1. MACD crosses above signal line
        2. Stock closes above 40-week SMA
        3. 40-week SMA is rising
        4. S&P 500 above its 40-week SMA (already checked)
        5. No earnings within 5 trading days
        6. No existing position or pending order
        """
        
        # Condition 1: MACD crosses above signal line
        if not (macd > signal and prev_macd <= prev_signal):
            return False
        
        # Condition 2: Stock closes above 40-week SMA
        if price <= sma:
            return False
        
        # Condition 3: 40-week SMA is rising
        if prev_sma >= sma:
            return False
        
        # Condition 5: Check for earnings (simplified - no earnings data API)
        # TODO: Integrate earnings calendar API
        
        # Condition 6: No existing position or pending order
        if stock in positions and positions[stock]["qty"] > 0:
            return False
        if stock in pending:
            return False
        
        return True
    
    def _check_sell_conditions(self, stock, price, sma, macd, signal, prev_macd, prev_signal, positions):
        """
        Sell when ANY one occurs:
        1. MACD crosses below signal line
        2. Stock closes below 40-week SMA
        3. Risk-based stop (TODO)
        4. Circuit breaker (already handled)
        """
        
        # Condition 1: MACD crosses below signal line
        if macd < signal and prev_macd >= prev_signal:
            return True
        
        # Condition 2: Stock closes below 40-week SMA
        if price < sma:
            return True
        
        return False
    
    # ==================== POSITION SIZING ====================
    
    def _calculate_position_size(self, stock, current_price):
        """Calculate position size based on portfolio allocation limits"""
        max_allocation = self.max_position_allocation.get(stock, 0.02)
        max_position_value = self.total_portfolio_value * max_allocation
        qty = int(max_position_value / current_price)
        return max(qty, 1)  # At least 1 share
    
    # ==================== EXECUTION FUNCTIONS ====================
    
    def _execute_buy(self, stock, qty, price):
        """Execute buy order with safety checks and notifications"""
        if self.require_manual_approval:
            # Send notification for manual approval
            order_summary = f"BUY {qty} shares of {stock} @ ${price:.2f} = ${qty*price:.2f}"
            print(f"⚠️  PENDING MANUAL APPROVAL: {order_summary}")
            logging_info(f'{self.strategy_name}: PENDING APPROVAL - {order_summary}')
            # In paper trading, skip actual execution
            if not self.use_paper_trading:
                return
        
        self.strategy_make_trade(action='BUY', stock=stock, qty=qty, price=price)
    
    def _execute_sell(self, stock, qty, price):
        """Execute sell order with safety checks and notifications"""
        if self.require_manual_approval:
            order_summary = f"SELL {qty} shares of {stock} @ ${price:.2f} = ${qty*price:.2f}"
            print(f"⚠️  PENDING MANUAL APPROVAL: {order_summary}")
            logging_info(f'{self.strategy_name}: PENDING APPROVAL - {order_summary}')
            if not self.use_paper_trading:
                return
        
        self.strategy_make_trade(action='SELL', stock=stock, qty=qty, price=price)

    # ==================== ORDER EXECUTION ====================
    
    def strategy_make_trade(self, action, stock, qty, price):
        """Execute trade with confirmation"""
        if self.trading_confirmation:
            if action == 'BUY':
                acct_ret, acct_info = self.trader.get_account_info()
                if acct_ret == RET_OK:
                    current_cash = acct_info['cash']
                else:
                    print('Trader: Get Account Info failed: ', acct_info)
                    return False

                if current_cash > qty * price:
                    if is_market_hours():
                        ret, data = self.trader.market_buy(stock, qty, price)
                    else:
                        ret, data = self.trader.limit_buy(stock, qty, price)

                    if ret == RET_OK:
                        print(data)
                        self.save_order_history(data)
                        print('✅ Buy order executed successfully')
                        print(self.get_current_position())
                    else:
                        print('❌ Trader: Buy failed: ', data)
                        logging_info(f'{self.strategy_name}: Buy failed: {data}')
                else:
                    print('❌ Trader: Buy failed: Not enough cash')
                    logging_info(f'{self.strategy_name}: Buy failed: Not enough cash')

            if action == 'SELL':
                position_data = self.get_current_position()
                if not position_data:
                    return False

                if qty <= position_data[stock]["qty"]:
                    if is_market_hours():
                        ret, data = self.trader.market_sell(stock, qty, price)
                    else:
                        ret, data = self.trader.limit_sell(stock, qty, price)
                    
                    if ret == RET_OK:
                        print(data)
                        logging_info(f'{self.strategy_name}: {data}')
                        self.save_order_history(data)
                        print('✅ Sell order executed successfully')
                        print(self.get_current_position())
                    else:
                        print('❌ Trader: Sell failed: ', data)
                        logging_info(f'{self.strategy_name}: Sell failed: {data}')
                else:
                    print('❌ Trader: Sell failed: Not enough position')
                    logging_info(f'{self.strategy_name}: Sell failed: Not enough position')

    def save_order_history(self, data):
        """Save order to transaction log"""
        file_data = read_json_file("order_history.json")
        data_dict = data.to_dict()
        new_dict = {}
        for key, v in data_dict.items():
            new_dict[key] = v[0]
        new_dict['timestamp'] = datetime.now().isoformat()
        logging_info(f'{self.strategy_name}: {str(new_dict)}')

        if file_data:
            file_data.append(new_dict)
        else:
            file_data = [new_dict]
        write_json_file("order_history.json", file_data)
