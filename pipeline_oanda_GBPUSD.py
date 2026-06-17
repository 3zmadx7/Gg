#!/usr/bin/env python3
import os

os.environ["OANDA_SYMBOL"] = "GBPUSD"
os.environ["OANDA_INSTRUMENT"] = "GBP_USD"

from pipeline_oanda import main


if __name__ == "__main__":
    main()
