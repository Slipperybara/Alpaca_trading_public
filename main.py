from traderlib import *
from trade_log import *
import sys
import alpaca_trade_api as tradeapi
import global_variables as gv


# check trading account
def check_account_active(api):
    try:
        account = api.get_account()
        if account.status != "ACTIVE":
            lg.error("Main - Account not active")
            sys.exit()
        else:
            lg.info("Main - Account active")
    except:
        lg.error("Main - Could not get account info")
        sys.exit()


# close current orders
def clean_open_orders(api):
    lg.info('Main - Cancelling all orders...')
    try:
        api.cancel_all_orders()
        lg.info("Main - All current open orders closed")
    except Exception as e:
        lg.error("Main - Could not close all open orders")
        lg.error(e)
        sys.exit()


# check asset tradable
def check_asset_ok(api, ticker):
    try:
        asset = api.get_asset(ticker)
        if asset.tradable:
            lg.info(f"Asset: {ticker} is tradable")
            return True
        else:
            lg.info(f"Asset: {ticker} is exists not tradable")
            return False
    except:
        lg.error("Main - Asset does not exists")
        sys.exit()


# execute trading bot
def main():
    api = tradeapi.REST(gv.API_KEY, gv.API_SECRET_KEY, gv.API_ENDPOINT, api_version="v2")
    # connect to the logger
    initialize_logger()
    # check trading account
    check_account_active(api)
    # close current orders
    clean_open_orders(api)

    # enter ticker with the keyboard
    # ticker = input('choose a stock(ticker): ')
    ticker = "AAPL"
    check_asset_ok(api, ticker)

    # run trading bot
    trader1 = Trader(api, ticker)
    trading_success = trader1.run(ticker)

    while True:
        if trading_success == "success":
            trader1.run(ticker)

        elif gv.current_time >= '15:45':
            lg.info("Market closing in 15 mins, stopping programme")
            return True

        if not trading_success:
            lg.info("Trading did not proceed")
            return True


if __name__ == '__main__':
    main()