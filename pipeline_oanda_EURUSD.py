#!/usr/bin/env python3
import os

os.environ["OANDA_SYMBOL"] = "EURUSD"
os.environ["OANDA_INSTRUMENT"] = "EUR_USD"

from pipeline_oanda import main


if __name__ == "__main__":
    main()
