from dataclasses import dataclass
from datetime import datetime

from openbb_terminal.reports import widget_helpers as widgets
from openbb_terminal.stocks.options import yfinance_model
from typing import Tuple
import options
import plots
from reports.base import Report
from reports.async_base import AsyncReport
import options

@dataclass
class GEXFullReport(AsyncReport):
    def process_symbol(self, symbol: str) -> Tuple[str, str]:
        htmlcode = widgets.h(1, f"Simple analysis for {symbol}:")
        full_chain = yfinance_model.get_full_option_chain(symbol)
        full_chain["strike"] = full_chain["strike"].astype(float)
        current_price = yfinance_model.get_price(symbol)

        expirations = options.filter_active_volume_expirations(full_chain, filter_less_then=1000)#,  concentration_type="openInterest")

        for expiry in expirations:
            chain = full_chain[full_chain["expiration"] == expiry]
            htmlcode += plots.options_gex_plot(
                chain, current_price
            )

            htmlcode += plots.absolute_options_concentration_plot(
                chain,
                current_price,
                concentration="openInterest",
            )
        
        htmlcode += plots.expiration_concentration_plot(
            full_chain, concentration="openInterest"
        )

        return htmlcode, symbol
