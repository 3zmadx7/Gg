#!/usr/bin/env python3
import os

os.environ["OANDA_SYMBOL"] = "USDCHF"
os.environ["OANDA_INSTRUMENT"] = "USD_CHF"

from pipeline_oanda import main


if __name__ == "__main__":
    main()
