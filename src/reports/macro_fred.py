import os
from fredapi import Fred


fred = Fred(
    os.environ.get("FRED_API_KEY", ""),
)
MACRO_CHARTS = {
    "CORE_CPI": "CORESTICKM159SFRBATL",
    "UNEPLOMENT_RATION": "UNRATE",
    "INTEREST_RATIO": "FEDFUNDS",
    "DOW_JOHN_100Y": "M1109BUSM293NNBR",
}

fred.get_series('FEDFUNDS')
