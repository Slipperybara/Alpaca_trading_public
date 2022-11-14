import logging as lg
import sys
import time
import global_variables as gv
import tulipy as ti
from datetime import datetime, timedelta
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import *
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import *
from alpaca_trade_api.rest import REST, TimeFrame, TimeFrameUnit


class Trader:
    def __init__(self, api, ticker):
        lg.info("TRADER - trader initiated with ticker %s" % ticker)
        self.ticker = ticker
        self.trend = 'long'
        self.api = api
        self.now = datetime.now()
        self.current_price = 0
        self.shares_amount = 0
        self.trading_client = TradingClient(gv.API_KEY, gv.API_SECRET_KEY)

    def set_stop_loss(self, entryprice, direction):
        # set stop loss: take entry price as input and calculate stop-loss price
        # input price
        # output stoploss_point in system
        stoploss_margin = gv.stoploss_margin  # percentage margin
        try:
            if direction == 'long':
                stoploss_point = float(entryprice) - (float(entryprice) * float(stoploss_margin))
                return float(stoploss_point)
            elif direction == 'short':
                stoploss_point = entryprice + (float(entryprice) * float(stoploss_margin))
                return float(stoploss_point)
            else:
                lg.error("Directions can only be long or short")

        except Exception:
            lg.error("EXIT STRATEGY - error occured while setting stoploss")
            sys.exit()

    def set_take_profit(self, entryprice, direction):
        # set take profit
        # input price
        # output price to sell in system
        take_profit_margin = gv.take_profit_margin  # percentage margin
        try:
            if direction == 'long':
                take_profit_point = float(entryprice) + (float(entryprice) * float(take_profit_margin))
                return float(take_profit_point)
            elif direction == 'short':
                take_profit_point = float(entryprice) + (float(entryprice) * float(take_profit_margin))
                return float(take_profit_point)
            else:
                lg.error("Directions can only be long or short")

        except Exception:
            lg.error("EXIT STRATEGY - error occured while setting take profit")
            sys.exit()

    def load_historical_data(self, interval, ticker):
        # load historical data:
        # input ticker, interval, period
        # output array with stock data
        try:
            current_datetime = datetime.now() - timedelta(hours=12)
            start_datetime = current_datetime - timedelta(hours=96)
            current_date = current_datetime.strftime('%Y-%m-%d')
            start_date = start_datetime.strftime('%Y-%m-%d')
            # # new version API not working
            # client = StockHistoricalDataClient(gv.API_KEY, gv.API_SECRET_KEY)
            # request_params = StockBarsRequest(
            #     symbol_or_symbols=ticker,
            #     timeframe=TimeFrame(interval, TimeFrameUnit.Minute),
            #     start=start_datetime,
            #     end=current_datetime,
            # )
            # bars = client.get_stock_bars(request_params)
            # return bars.df
            # old version API
            import pdb; pdb.set_trace()
            api = REST(gv.API_KEY, gv.API_SECRET_KEY, gv.API_ENDPOINT, api_version="v2")
            data = api.get_bars(ticker, TimeFrame(interval, TimeFrameUnit.Minute), '2022-11-04', '2022-11-07',
                                adjustment='raw').df
            return data
        except:
            lg.error("Something went wrong while retrieving historical data")

    def submit_order(self, current_price, direction, ticker, quantity):
        # submit order: gets order through API
        # input order data, limit order/market order
        # output boolean
        attempts = 0
        max_attempt = 3
        while attempts < max_attempt:
            try:
                if direction == 'buy':
                    market_order_data = MarketOrderRequest(symbol=ticker,
                                                           qty=quantity,
                                                           limit_price=current_price,
                                                           side=OrderSide.BUY,
                                                           type=OrderType.MARKET,
                                                           time_in_force=TimeInForce.DAY,
                                                           )
                    self.trading_client.submit_order(order_data=market_order_data)
                    lg.info("ENTERING POSITION - Order submitted: \n"
                            f"{ticker}\n"
                            f"{current_price}\n"
                            f"{quantity}"
                            f"{direction}")
                    return True

                if direction == 'sell':
                    market_order_data = MarketOrderRequest(symbol=ticker,
                                                           qty=quantity,
                                                           limit_price=current_price,
                                                           side=OrderSide.SELL,
                                                           type=OrderType.MARKET,
                                                           time_in_force=TimeInForce.DAY,
                                                         )
                    self.trading_client.submit_order(order_data=market_order_data)
                    lg.info("ENTERING POSITION - Order submitted: \n"
                            f"{ticker}\n"
                            f"{current_price}\n"
                            f"{quantity}"
                            f"{direction}")
                    return True
            except Exception:
                lg.info("ENTERING POSITION - Something went wrong with submitting order, trying again")
                attempts += 1
        lg.error('Could not submit order, exiting programme')
        self.cancel_pending_order()
        sys.exit()

    def cancel_pending_order(self):
        # cancel order
        # input order id
        # output boolean
        cancel_statuses = self.trading_client.cancel_orders()
        lg.info("Cancelling all orders... "
                f"\n Response: {cancel_statuses}")

    def check_position(self, ticker):
        # check position: check if position is still open
        # input: ticker
        # output: boolean
        maxattempts = 2
        attempt = 0
        while attempt <= maxattempts:
            try:
                position = self.api.get_position(ticker)
                entryprice = position.avg_entry_price
                quantity = position.qty
                asset_id = position.asset_id
                lg.info(f"TRADER - Position confirmed. Entry price: ${entryprice} "
                        f"\n quantity: {quantity} "
                        f"\n asset_id: {asset_id}")
                return True
            except:
                # retry after 10 seconds
                lg.info("Checking position")
                time.sleep(1)
                attempt += 1
        lg.info(f"TRADER - There are no existing position for {ticker}")
        return False

    def get_shares_amount(self, asset_price):

        lg.info("Getting shares amount")

        try:
            # def max to spend
            invest_amount = int(gv.max_amount)
            # total equity available
            account = self.trading_client.get_account()
            equity = float(account.equity)
            lg.info(f"ENTERING POSITION - You have a total of {equity} in your account")
            # calculate the number of shares
            if invest_amount < equity:
                quantity = int(invest_amount//asset_price)
                lg.info(f"ENTERING POSITION - Buying a total of [{quantity}]  shares")
                return quantity
            else:
                lg.info("ENTERING POSITION - You have insufficient amount of equity in your account")

        except:
            lg.info("An error occured while calculating shares amount")
            sys.exit()

    def get_general_trend_market(self, market):
        # Perform general trend analysis (Up, Down, Sideways)
        # Input: asset
        # Output Up/ Down/ Sideways
        attempt = 0
        maxattempt = 48
        lg.info("TRADER - General market trend analysis entered")
        try:
            while True:
                historical_data = self.load_historical_data(ticker=market,
                                                            interval=30)

                ema9 = ti.ema(historical_data.close.to_numpy(), 9)[-1]
                ema26 = ti.ema(historical_data.close.to_numpy(), 26)[-1]
                ema50 = ti.ema(historical_data.close.to_numpy(), 50)[-1]
                lg.info(f"{market}'s general ema value(30min candles)=\n ema9:{ema9}, \nema26:{ema26}, \nema50:{ema50}")

                if ema50 > ema26 > ema9:
                    lg.info(f"down trend for {market}")
                    return "short"
                elif ema50 < ema26 < ema9:
                    lg.info(f"up trend for {market}")
                    return "long"
                elif attempt <= maxattempt:
                    attempt += 1
                    lg.info("Trend unclear")
                    time.sleep(300)
                else:
                    lg.info(f"no trend for {market}")
                    return False

        except Exception as e:
            lg.error("TRADER - Something went wrong at getting general trend market")
            lg.error(e)
            sys.exit()

    def get_general_trend_stock(self, ticker, trend):
        # Perform general trend analysis (Up, Down, Sideways)
        # Input: asset
        # Output Up/ Down/ Sideways
        attempt = 0
        maxattempt = 10
        lg.info("General trend analysis entered")
        try:
            while True:
                historical_data = self.load_historical_data(ticker=ticker,
                                                            interval=30)

                ema9 = ti.ema(historical_data.close.to_numpy(), 9)[-1]
                ema26 = ti.ema(historical_data.close.to_numpy(), 26)[-1]
                ema50 = ti.ema(historical_data.close.to_numpy(), 50)[-1]
                lg.info(f"{ticker}'s general ema value(30min candles)=\n ema9:{ema9}, \nema26:{ema26}, \nema50:{ema50}")

                if ema50 > ema26 > ema9 and trend == 'short':
                    lg.info(f"down trend for {ticker}")
                    return "short"
                elif ema50 < ema26 < ema9 and trend == 'long':
                    lg.info(f"up trend for {ticker}")
                    return "long"
                elif attempt <= maxattempt:
                    attempt += 1
                    lg.info("Trend unclear")
                    time.sleep(120)
                else:
                    lg.info(f"no trend for {ticker}")
                    return False

        except Exception as e:
            lg.error("Something went wrong at getting general trend stock")
            lg.error(e)
            sys.exit()

    def get_instant_trend(self, ticker, trend):
        # perform instant trend analysis
        # input Output of the general trend function, input 5 mins candles(closing price)
        # Output True(Trend same direction)/False(Trend different direction)
        attempt = 0
        maxattempt = 5
        lg.info("Instant trend analysis entered")
        try:
            while True:
                data = self.load_historical_data(ticker=ticker,
                                                 interval=5,
                                                 )
                ema9 = ti.ema(data.close.to_numpy(), 9)[-1]
                ema26 = ti.ema(data.close.to_numpy(), 26)[-1]
                ema50 = ti.ema(data.close.to_numpy(), 50)[-1]

                lg.info(f"{ticker}'s instant ema value= \nema9: {ema9}\nema26: {ema26}\nema50: {ema50}")

                if ema50 < ema26 < ema9 and trend == 'long':
                    lg.info(f"confirmed up trend for {ticker}")
                    return True

                elif ema50 > ema26 > ema9 and trend == "short":
                    lg.info(f" confirmed down trend for {ticker}")
                    return True

                elif attempt <= maxattempt:
                    attempt += 1
                    lg.info("Instant trend unclear")
                    time.sleep(60)

                else:
                    lg.info(f"trend not confirmed for {ticker}")
                    return False

        except Exception as e:
            lg.error("Something went wrong at getting instant trend")
            lg.error(e)
            sys.exit()

    def get_rsi(self, ticker, trend):
        # Perform RSI
        # input Output of the general trend function, input 5 mins candles(closing price)
        # Output True(Trend same direction)/False(Trend different direction)
        lg.info("RSI analysis entered")
        attempt = 0
        maxattempt = 5
        try:
            while True:
                data = self.load_historical_data(ticker=ticker,
                                                 interval=5,
                                                )
                rsi = ti.rsi(data.close.to_numpy(), 14)[-1]
                lg.info(f"{ticker} RSI value equals to {rsi}")

                if 50 < rsi < 80 and trend == 'long':
                    lg.info(f"confirmed up trend for {ticker}")
                    return True
                elif 20 < rsi < 50 and trend == "short":
                    lg.info(f" confirmed down trend for {ticker}")
                    return True
                elif attempt <= maxattempt:
                    attempt += 1
                    lg.info("RSI trend unclear")
                    time.sleep(60)
                else:
                    lg.info(f"trend not confirmed for {ticker}")
                    return False
        except Exception as e:
            lg.error("Something went wrong at getting RSI")
            lg.error(e)
            sys.exit()

    def get_stoch(self, ticker, trend):
        # Perform stochastic analysis
        # input asset, Output of the general trend function, input 5 mins candles(open, high, low, close)
        # Output True(Trend same direction)/False(Trend different direction)
        lg.info("Stochastic analysis entered")

        attempt = 0
        maxattempt = 5
        try:
            while True:
                data = self.load_historical_data(ticker=ticker,
                                                 interval=5,
                                                 )
                stoch_k, stoch_d = ti.stoch(data.high.to_numpy(),
                                            data.low.to_numpy(),
                                            data.close.to_numpy(),
                                            9, 6, 9)
                stoch_k = stoch_k[-1]
                stoch_d = stoch_d[-1]
                lg.info(f"{ticker} stochastic value equals to {stoch_k} and {stoch_d}")

                if (stoch_k > stoch_d) and (stoch_k < 70) and (trend == 'long'):
                    lg.info(f"confirmed up trend for {ticker}")
                    return True
                elif (stoch_k < stoch_d) and (stoch_k > 30) and (trend == "short"):
                    lg.info(f" confirmed down trend for {ticker}")
                    return True
                elif attempt <= maxattempt:
                    attempt += 1
                    lg.info("Instant trend unclear")
                    time.sleep(60)
                else:
                    lg.info (f"trend not confirmed for {ticker}")
                    return False

        except Exception as e:
            lg.error("Something went wrong at getting RSI")
            lg.error(e)
            sys.exit()

    # def check_stoch_crossing(self, ticker, trend):
    #     #input: asset, trend
    #     #output; True/False
    #     try:
    #
    #         data = self.load_historical_data(ticker=ticker,
    #                                          interval=5,
    #                                          )
    #         stoch_k, stoch_d = ti.stoch(data.high.to_numpy(),
    #                                         data.low.to_numpy(),
    #                                         data.close.to_numpy(),
    #                                         21, 7, 7)
    #         if (trend == 'long') and (stoch_k <= stoch_d):
    #             lg.info("stochastic curves crossed: long")
    #             return True
    #         if (trend == "short") and (stoch_k >= stoch_d):
    #             lg.info("stochastic curves crossed: short")
    #             return True
    #         else:
    #             lg.info("Stochastic curves not crossed")
    #             return False
    #         pass
    #     except:
    #         lg.error("Error occured at check stoch crossing")
    #         return Tru
    def exit_strategy(self, ticker, direction):
        # exit strategy(loop ~8h):
        position = self.api.get_position(ticker)
        entry_price = float(position.avg_entry_price)
        current_price = float(position.current_price)
        quantity = int(position.qty)

        take_profit_price_long = self.set_take_profit(entry_price, 'long')
        stoploss_price_long = self.set_stop_loss(entry_price, 'long')

        take_profit_price_short = self.set_take_profit(entry_price, 'short')
        stoploss_price_short = self.set_stop_loss(entry_price, 'short')

        # stoch_crossed = self.check_stoch_crossing(ticker, 'long')
        attempt = 0
        maxattempt = 2000

        while True:
            # closing long position(sell)
            if direction == 'long':
                if float(current_price) >= take_profit_price_long:
                    lg.info(f"EXIT STRATEGY - Take profit met at {current_price}\n "
                            f"Total profit: {(current_price - entry_price)*quantity}")
                    return True

                elif float(current_price) <= stoploss_price_long:
                    lg.info(f"EXIT STRATEGY - Stop loss met at {current_price}\n "
                            f"Total loss: {(current_price - entry_price)*quantity}")
                    return True
            # closing short position(buy)
            if direction == 'short':
                if float(current_price) <= take_profit_price_short:
                    lg.info(f"EXIT STRATEGY - Take profit met at {current_price}\n "
                            f"Total profit: {(current_price - entry_price) * quantity}")
                    return True

                elif float(current_price) >= stoploss_price_short:
                    lg.info(f"EXIT STRATEGY - Stop loss met at {current_price}\n "
                            f"Total loss: {(current_price - entry_price) * quantity}")
                    return True
            # elif stoch_crossed:
            #     lg.info(f"Stochastic curves crossed, closing position at {current_price}\n"
            #             f"Total profit: {(current_price - entry_price)*quantity}")
            #     return True

            elif gv.current_time >= '15:45':
                lg.info(f"EXIT STRATEGY - Market closing in 15 mins, closing position at {current_price}\n"
                        f"Total profit: {(current_price - entry_price)*quantity}")
                return True

            elif attempt <= maxattempt:
                attempt += 1
                lg.info("EXIT STRATEGY - waiting inside position")
                lg.info(f"current price: {current_price}")
                time.sleep(10)

            else:
                lg.info(f"EXIT STRATEGY - Time reached, selling position, current price: {current_price}")
                return True

    # combined code
    def run(self, ticker):
        while True:
            # Check Position: Check with API if available to trade, and is there already an open position
            if self.check_position(ticker):
                lg.info("TRADER - Position for this ticker already exist, ending buying operation")
                break

            # CONFIRMING TREND DIRECTION
            while True:
                # Perform general trend analysis(SPY)
                self.trend = self.get_general_trend_market(market='SPY')
                if not self.trend:
                    lg.info(f"FINDING TREND - Market is trendless today, not tradable")
                    return False
                # Perform general trend analysis(ticker)
                if not self.get_general_trend_stock(ticker=ticker,
                                                    trend=self.trend):
                    lg.info(f"FINDING TREND - {ticker} general trend not following the market")
                    continue
                # Perform instant trend analysis
                if not self.get_instant_trend(ticker=ticker,
                                              trend=self.trend):
                    lg.info(f"FINDING TREND - {ticker}: instant trend not confirmed, going back to general trend")
                    continue
                # Perform RSI
                if not self.get_rsi(ticker=ticker,
                                    trend=self.trend):
                    lg.info(f"FINDING TREND - {ticker}: RSI not confirmed, going back to general trend")
                    continue
                # Perform stochastic analysis
                # if not self.get_stoch(ticker, self.trend):
                #     lg.info(f"{ticker}: Stochastic trend not confirmed, going back to general trend")
                #     continue
                # All indicators passed
                lg.info("FINDING TREND - All indicators passed! carrying on")
                break

            # ENTERING POSITION
            # Get current price
            data = self.load_historical_data(ticker=ticker,
                                             interval=1,
                                             )
            self.current_price = data.close.to_numpy()[-1]
            # Get_shares_amount: Decide the total amount to invest
            self.shares_amount = self.get_shares_amount(self.current_price)
            # Submit order
            if self.trend == 'long':
                self.submit_order(current_price=self.current_price,
                                  direction='buy',
                                  ticker=ticker,
                                  quantity=self.shares_amount)
            if self.trend == 'short':
                self.submit_order(current_price=self.current_price,
                                  direction='sell',
                                  ticker=ticker,
                                  quantity=self.shares_amount)
            time.sleep(30)
            # Check position
            if not self.check_position(ticker):
                lg.info("Position not logged, exiting")
                try:
                    self.cancel_pending_order()
                    lg.info("Back to Finding Trend Stage")
                    continue # go through the process again
                except:
                    lg.error("Something went wrong with submitting order, cannot cancel!!")
                    sys.exit()


        # EXIT
        # EXIT STRATEGY(Loop ~8H)
        lg.info("Moving onto exit strategy")
        success_operation = self.exit_strategy(ticker=ticker,
                                               direction=self.trend)
        time.sleep(5)
        while True:
            if success_operation:
                position = self.api.get_position(ticker)
                current_price = float(position.current_price)
                quantity = abs(int(position.qty))

                if self.trend == 'long':
                    self.submit_order(
                                      current_price=current_price,
                                      direction='sell',
                                      ticker=ticker,
                                      quantity=quantity)
                    time.sleep(60)
                    # Check position
                    if self.check_position(ticker) == False:
                        lg.info("[-------------------------------POSITION CLOSED-------------------------------]")
                        return "success"

                if self.trend == "short":
                    self.submit_order(
                        current_price=current_price,
                        direction='buy',
                        ticker=ticker,
                        quantity=quantity)
                    time.sleep(60)
                    # Check position
                    if self.check_position(ticker) == False:
                        lg.info("[-------------------------------POSITION CLOSED-------------------------------]")
                        return "success"