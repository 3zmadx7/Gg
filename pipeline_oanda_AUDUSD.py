#!/usr/bin/env python3
import os

os.environ["OANDA_SYMBOL"] = "AUDUSD"
os.environ["OANDA_INSTRUMENT"] = "AUD_USD"

from pipeline_oanda import main


if __name__ == "__main__":
    main()
