#  NIFTY 50 0920 Short straddle, % based SL

from kiteconnect import KiteConnect
import pandas as pd
import datetime as dt
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class NiftyTradingBot:
    def __init__(self):
        # Configuration
        self.lots = 1  # quantity
        self.lot_size = 75  # NIFTY lot size (changed from 50 to 75 from March 2025)
        self.ce_stoploss_per = 25
        self.pe_stoploss_per = 25

        # NSE Holidays - Updated for 2025
        self.nse_holidays = [
            dt.date(2025, 1, 26), dt.date(2025, 3, 14), dt.date(2025, 3, 31),
            dt.date(2025, 4, 11), dt.date(2025, 4, 14), dt.date(2025, 4, 18),
            dt.date(2025, 5, 1), dt.date(2025, 8, 15), dt.date(2025, 10, 2),
            dt.date(2025, 10, 31), dt.date(2025, 11, 15), dt.date(2025, 12, 25)
        ]

        # API Configuration - Use your existing credentials
        self.api_key = "1t306nxawlfv28w4"  # From your working script
        self.api_secret = ""

        # Trading Times
        self.open_time = dt.time(hour=9, minute=15)
        self.trade_entry_time = dt.time(hour=9, minute=20)
        self.re_entry_time = dt.time(hour=12, minute=30)
        self.sqf_time = dt.time(hour=15, minute=6)

        # Initialize KiteConnect
        self.access_token = self.load_access_token()
        self.kite = KiteConnect(api_key=self.api_key)
        self.kite.set_access_token(self.access_token)

        # Trading variables
        self.bn_ltp = None
        self.atm_strike = None
        self.ce_symbol = None
        self.pe_symbol = None
        self.ce_order_id = None
        self.pe_order_id = None
        self.ce_sell_price = None
        self.pe_sell_price = None
        self.ce_sl_orderid = None
        self.pe_sl_orderid = None
        self.bn_exp_df = None

    def load_access_token(self):
        """Load access token from file"""
        try:
            with open('/home/ubuntu/utilities/kite_connect_data/tickjournal/key_files/access_token.txt', 'r') as f:
                return f.read().strip()
        except FileNotFoundError:
            logger.error("Access token file not found")
            raise

    def get_expiry_date(self):
        """Calculate the next weekly expiry date (Thursday)"""
        current_date = dt.date.today()
        wd = current_date.weekday()  # 0 Monday, 6 Sunday

        # Calculate days to next Thursday (weekly expiry)
        if wd <= 3:
            x = (3 - wd)
        else:
            x = 6

        exp_date = current_date + dt.timedelta(days=x)

        # Handle holidays
        while exp_date in self.nse_holidays:
            exp_date = exp_date - dt.timedelta(days=1)

        return exp_date

    def find_nearest_expiry(self, nifty_df, target_expiry):
        """Find the nearest available expiry date from the instrument dump"""
        available_expiries = sorted(nifty_df['expiry'].unique())
        logger.info(f"Available expiry dates: {available_expiries}")

        if target_expiry in available_expiries:
            logger.info(f"Target expiry {target_expiry} found in available expiries")
            return target_expiry

        # Find the nearest expiry date
        nearest_expiry = min(available_expiries, key=lambda x: abs((x - target_expiry).days))
        logger.info(f"Target expiry {target_expiry} not found. Using nearest expiry: {nearest_expiry}")
        return nearest_expiry

    def get_nifty_atm_strike(self, ltp):
        """Calculate ATM strike for NIFTY 50 (50 point intervals)"""
        r = ltp % 50
        if r < 25:
            atm = ltp - r
        else:
            atm = ltp - r + 50
        return int(atm)

    def debug_instrument_data(self, df, target_strike, expiry_date):
        """Debug function to analyze the instrument data"""
        logger.info(f"=== DEBUG INSTRUMENT DATA ===")
        logger.info(f"Expiry date: {expiry_date}")
        logger.info(f"Target strike: {target_strike}")
        logger.info(f"Total instruments in filtered dataframe: {len(df)}")

        if len(df) == 0:
            logger.error("No instruments found for this expiry date!")
            return

        # Show unique strikes available
        unique_strikes = sorted(df['strike'].unique())
        logger.info(f"Total unique strikes available: {len(unique_strikes)}")
        logger.info(f"Strike range: {min(unique_strikes)} to {max(unique_strikes)}")

        # Show strikes around target
        nearby_strikes = [s for s in unique_strikes if abs(s - target_strike) <= 200]
        logger.info(f"Strikes within 200 points of {target_strike}: {nearby_strikes}")

        # Show instrument types available for target strike
        target_data = df[df.strike == target_strike]
        if len(target_data) > 0:
            logger.info(f"Available instrument types for strike {target_strike}: {target_data['instrument_type'].unique()}")
            for _, row in target_data.iterrows():
                logger.info(f"  {row['instrument_type']}: {row['tradingsymbol']}")
        else:
            logger.info(f"No instruments found for exact strike {target_strike}")
            if unique_strikes:
                closest_strike = min(unique_strikes, key=lambda x: abs(x - target_strike))
                logger.info(f"Closest available strike: {closest_strike}")

    def get_trading_symbol(self, df, strike, option_type):
        """Get trading symbol for given strike and option type - improved version"""
        try:
            # Filter for exact strike
            df_filtered = df[df.strike == strike]

            if len(df_filtered) == 0:
                # If exact strike not found, find the closest available strike
                unique_strikes = sorted(df['strike'].unique())
                if not unique_strikes:
                    raise ValueError("No strikes available in the instrument data")

                closest_strike = min(unique_strikes, key=lambda x: abs(x - strike))
                logger.info(f"Exact strike {strike} not found. Using closest available strike: {closest_strike}")
                df_filtered = df[df.strike == closest_strike]
                strike = closest_strike

            # Check if we have the required option type for this strike
            available_types = df_filtered['instrument_type'].unique()
            if option_type not in available_types:
                raise ValueError(f"Option type {option_type} not available for strike {strike}. Available types: {available_types}")

            # Get the trading symbol for the specified option type
            symbol_data = df_filtered[df_filtered.instrument_type == option_type]
            if len(symbol_data) == 0:
                raise ValueError(f"No {option_type} option found for strike {strike}")

            symbol = symbol_data.tradingsymbol.values[0]
            logger.info(f"Found {option_type} symbol for strike {strike}: {symbol}")

            return symbol

        except Exception as e:
            logger.error(f"Error getting trading symbol for strike {strike}, type {option_type}: {str(e)}")
            raise

    def get_nifty_ltp(self, max_retries=10):
        """Get NIFTY 50 Last Traded Price with improved error handling"""
        for attempt in range(max_retries):
            try:
                nifty_data = self.kite.ltp('NSE:NIFTY 50')
                ltp = nifty_data['NSE:NIFTY 50']['last_price']
                logger.info(f"NIFTY 50 LTP: {ltp}")
                return ltp
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1}: Can't extract LTP data - {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                else:
                    logger.error("Failed to get NIFTY LTP after maximum retries")
                    raise Exception("Unable to fetch NIFTY LTP after maximum retries")

    def place_market_order_sell(self, symbol, quantity):
        """Place market sell order"""
        try:
            order_id = self.kite.place_order(
                tradingsymbol=symbol,
                exchange=self.kite.EXCHANGE_NFO,
                transaction_type=self.kite.TRANSACTION_TYPE_SELL,
                quantity=quantity,
                order_type=self.kite.ORDER_TYPE_MARKET,
                product=self.kite.PRODUCT_MIS,
                variety=self.kite.VARIETY_REGULAR
            )
            logger.info(f"Sell order placed for {symbol}: {order_id}")
            return order_id
        except Exception as e:
            logger.error(f"Error placing sell order for {symbol}: {str(e)}")
            raise

    def place_market_order_buy(self, symbol, quantity):
        """Place market buy order"""
        try:
            order_id = self.kite.place_order(
                tradingsymbol=symbol,
                exchange=self.kite.EXCHANGE_NFO,
                transaction_type=self.kite.TRANSACTION_TYPE_BUY,
                quantity=quantity,
                order_type=self.kite.ORDER_TYPE_MARKET,
                product=self.kite.PRODUCT_MIS,
                variety=self.kite.VARIETY_REGULAR
            )
            logger.info(f"Buy order placed for {symbol}: {order_id}")
            return order_id
        except Exception as e:
            logger.error(f"Error placing buy order for {symbol}: {str(e)}")
            raise

    def place_stoploss_order_buy(self, symbol, quantity, trigger_price):
        """Place stop loss buy order"""
        try:
            order_id = self.kite.place_order(
                tradingsymbol=symbol,
                exchange=self.kite.EXCHANGE_NFO,
                transaction_type=self.kite.TRANSACTION_TYPE_BUY,
                quantity=quantity,
                order_type=self.kite.ORDER_TYPE_SLM,
                product=self.kite.PRODUCT_MIS,
                variety=self.kite.VARIETY_REGULAR,
                trigger_price=trigger_price
            )
            logger.info(f"Stop loss buy order placed for {symbol} at {trigger_price}: {order_id}")
            return order_id
        except Exception as e:
            logger.error(f"Error placing stop loss order for {symbol}: {str(e)}")
            raise

    def get_trade_price(self, order_id, max_retries=10):
        """Get average price of executed trade"""
        for attempt in range(max_retries):
            try:
                trades = self.kite.trades()
                tb_df = pd.DataFrame(trades)
                trade_price = tb_df[tb_df.order_id == order_id].average_price.values[0]
                logger.info(f"Trade price for order {order_id}: {trade_price}")
                return trade_price
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1}: Can't extract trade data - {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                else:
                    logger.error(f"Failed to get trade price for order {order_id}")
                    raise Exception(f"Unable to fetch trade price for order {order_id}")

    def get_order_status(self, order_id, max_retries=10):
        """Check if order is executed or pending"""
        for attempt in range(max_retries):
            try:
                trades = self.kite.trades()
                tb_df = pd.DataFrame(trades)
                df_filtered = tb_df[tb_df.order_id == order_id]

                if len(df_filtered) > 0:
                    status = 'executed'
                else:
                    status = 'pending'

                logger.info(f"Order {order_id} status: {status}")
                return status
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1}: Can't extract order status - {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                else:
                    logger.error(f"Failed to get order status for {order_id}")
                    return 'unknown'

    def cancel_order(self, order_id):
        """Cancel pending order"""
        try:
            self.kite.cancel_order(order_id=order_id, variety=self.kite.VARIETY_REGULAR)
            logger.info(f"Order {order_id} cancelled")
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {str(e)}")

    def round_to_tick_size(self, price):
        """Round price to 0.05 tick size"""
        r = round(price % 0.05, 2)
        rounded_price = round(price - r, 2)
        return float(rounded_price)

    def download_instrument_data(self):
        """Download instrument data from Kite with retry logic"""
        max_retries = 16
        for attempt in range(max_retries):
            try:
                instrument_dump = self.kite.instruments("NFO")
                logger.info(f"Successfully downloaded {len(instrument_dump)} instruments from NFO")
                return pd.DataFrame(instrument_dump)
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1}: Instrument dump download error - {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                else:
                    logger.error("Failed to download instrument data after maximum retries")
                    raise Exception("Unable to download instrument data")

    def calculate_atm_and_place_order(self):
        """Calculate ATM strike and place straddle orders"""
        try:
            # Get current NIFTY price
            self.bn_ltp = self.get_nifty_ltp()
            logger.info(f'NIFTY LTP: {self.bn_ltp}')

            # Calculate ATM strike
            self.atm_strike = self.get_nifty_atm_strike(self.bn_ltp)
            logger.info(f'ATM Strike: {self.atm_strike}')

            # Debug instrument data before trying to get symbols
            self.debug_instrument_data(self.bn_exp_df, self.atm_strike, self.expiry_date)

            # Get trading symbols
            self.ce_symbol = self.get_trading_symbol(self.bn_exp_df, self.atm_strike, 'CE')
            self.pe_symbol = self.get_trading_symbol(self.bn_exp_df, self.atm_strike, 'PE')

            logger.info(f"CE Symbol: {self.ce_symbol}")
            logger.info(f"PE Symbol: {self.pe_symbol}")

            # Place sell orders for straddle
            quantity = self.lots * self.lot_size
            logger.info(f"Placing sell orders for quantity: {quantity} (lots: {self.lots} x lot_size: {self.lot_size})")

            self.ce_order_id = self.place_market_order_sell(self.ce_symbol, quantity)
            self.pe_order_id = self.place_market_order_sell(self.pe_symbol, quantity)

            # Wait for orders to process
            time.sleep(2)

            # Get trade prices
            self.ce_sell_price = self.get_trade_price(self.ce_order_id)
            self.pe_sell_price = self.get_trade_price(self.pe_order_id)

            logger.info(f'CE sell price: {self.ce_sell_price}')
            logger.info(f'PE sell price: {self.pe_sell_price}')

            # Calculate stop loss values
            ce_stoploss_value = self.round_to_tick_size(self.ce_sell_price * self.ce_stoploss_per / 100)
            pe_stoploss_value = self.round_to_tick_size(self.pe_sell_price * self.pe_stoploss_per / 100)

            # Place stop loss orders
            ce_trigger_price = self.round_to_tick_size(self.ce_sell_price + ce_stoploss_value)
            pe_trigger_price = self.round_to_tick_size(self.pe_sell_price + pe_stoploss_value)

            self.ce_sl_orderid = self.place_stoploss_order_buy(self.ce_symbol, quantity, ce_trigger_price)
            self.pe_sl_orderid = self.place_stoploss_order_buy(self.pe_symbol, quantity, pe_trigger_price)

            logger.info(f"Straddle setup completed - CE: {self.ce_sell_price}, PE: {self.pe_sell_price}")

        except Exception as e:
            logger.error(f"Error in calculate_atm_and_place_order: {str(e)}")
            raise

    def wait_until_time(self, target_time):
        """Wait until specified time"""
        logger.info(f"Waiting until {target_time}")
        while dt.datetime.now().time() < target_time:
            time.sleep(1)

    def execute_square_off_logic(self):
        """Execute square off logic at market close"""
        logger.info("Executing square off logic")

        ce_sl_status = self.get_order_status(self.ce_sl_orderid)
        pe_sl_status = self.get_order_status(self.pe_sl_orderid)

        quantity = self.lots * self.lot_size

        if ce_sl_status == 'pending':
            self.cancel_order(self.ce_sl_orderid)
            self.place_market_order_buy(self.ce_symbol, quantity)

        if pe_sl_status == 'pending':
            self.cancel_order(self.pe_sl_orderid)
            self.place_market_order_buy(self.pe_symbol, quantity)

        logger.info("Square off completed")

    def run_trading_strategy(self):
        """Main trading strategy execution"""
        try:
            logger.info("Starting NIFTY 50 Short Straddle Strategy")

            # Download instrument data
            instrument_df = self.download_instrument_data()

            # Filter NIFTY options - use 'NIFTY' not 'NIFTY50'
            nifty_options = instrument_df[instrument_df.name == 'NIFTY']
            logger.info(f"Found {len(nifty_options)} NIFTY instruments")

            # Calculate and find expiry date
            target_expiry_date = self.get_expiry_date()
            logger.info(f"Target expiry date: {target_expiry_date}")

            # Find the nearest available expiry date
            self.expiry_date = self.find_nearest_expiry(nifty_options, target_expiry_date)
            logger.info(f"Using expiry date: {self.expiry_date}")

            # Filter for current expiry
            self.bn_exp_df = nifty_options[nifty_options.expiry == self.expiry_date]
            logger.info(f"Found {len(self.bn_exp_df)} NIFTY instruments for expiry {self.expiry_date}")

            if len(self.bn_exp_df) == 0:
                logger.error("No NIFTY instruments found for the expiry date!")
                available_expiries = sorted(nifty_options['expiry'].unique())
                logger.error(f"Available expiry dates: {available_expiries}")
                raise Exception("No instruments available for trading")

            # Wait until trade entry time
            self.wait_until_time(self.trade_entry_time)

            # Place initial straddle
            logger.info("Placing initial straddle orders")
            self.calculate_atm_and_place_order()

            # Wait until re-entry time to check for adjustments
            self.wait_until_time(self.re_entry_time)

            # Check if both stop losses hit and re-enter if needed
            ce_sl_status = self.get_order_status(self.ce_sl_orderid)
            pe_sl_status = self.get_order_status(self.pe_sl_orderid)

            if ce_sl_status == 'executed' and pe_sl_status == 'executed':
                logger.info("Both stop losses hit - Re-entering straddle")
                self.calculate_atm_and_place_order()

            # Wait until square off time
            self.wait_until_time(self.sqf_time)

            # Execute square off
            self.execute_square_off_logic()

            logger.info("Trading strategy completed successfully")

        except Exception as e:
            logger.error(f"Error in trading strategy: {str(e)}")
            raise


# Main execution
if __name__ == "__main__":
    try:
        bot = NiftyTradingBot()
        bot.run_trading_strategy()
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        print(f"Trading bot failed with error: {str(e)}")