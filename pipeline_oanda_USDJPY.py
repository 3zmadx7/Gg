#!/usr/bin/env python3
import os

os.environ["OANDA_SYMBOL"] = "USDJPY"
os.environ["OANDA_INSTRUMENT"] = "USD_JPY"

from pipeline_oanda import main


if __name__ == "__main__":
    main()
