import logging as lg
import os
from datetime import datetime


# creating a folder for the logs
def initialize_logger():
    logs_path = './logs'
    try:
        os.mkdir(logs_path)
    except OSError:
        print("Log already created")
    else:
        print('Log created')

    # naming each folder depending on the time
    time_now = datetime.now().strftime("%Y%m%d - %H:%M:%S")
    log_name = f"{time_now}.log"
    file_path = logs_path + '/' + log_name
    # log parameters
    lg.basicConfig(filename=file_path, format='%(asctime)s - %(levelname)s: %(message)s', level=lg.DEBUG)

    lg.getLogger().addHandler(lg.StreamHandler())
    lg.info("- Log initialized")