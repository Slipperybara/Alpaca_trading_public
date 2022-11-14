from datetime import datetime, timedelta

# Time
current_datetime = datetime.now() - timedelta(hours=12)
start_datetime = current_datetime - timedelta(hours=96)
current_time = current_datetime.strftime("%H:%M")
current_date = current_datetime.strftime('%Y-%m-%d')
start_date = start_datetime.strftime('%Y-%m-%d')

# API parameteres
API_KEY = 'PKA5X5K7WM72G9FFPNTY'
API_SECRET_KEY = '3SfXKDVJVdM3zbAbjw63amU2le7EMfSanBJM96sv'
API_ENDPOINT = 'https://paper-api.alpaca.markets'

# under set_stop_loss
stoploss_margin = 0.005

# under set_take_profit
take_profit_margin = 0.01

# under get_shares_amount
max_amount = 2000