from rjapi import rjapi
from time import sleep
from datetime import datetime
import sys

def main():
    config_file = None
    if len(sys.argv) > 1:
        if sys.argv[1] == "-h" or len(sys.argv) != 3:
            print("Usage: {} [-c config_file]".format(sys.argv[0]))
            return
        elif sys.argv[1] == "-c" and len(sys.argv) == 3:
            config_file = sys.argv[2]
    
    # Initialize rjapi and start infinite loop
    api = rjapi(config_file)
    start(api)


def start(api):
    print(datetime.now(), "Regiojet Checker started.")
    while True:
        # Tickets available
        if api.search_ticket():
            api.send_alert()
            print(datetime.now(), "Tickets available, sleeping for 5 minutes.")
            sleep(500)
        # Tickets not available
        else:
            sleep(20)


if __name__ == "__main__":
    main()