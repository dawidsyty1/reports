from dataclasses import dataclass
from datetime import datetime

from openbb_terminal.reports import widget_helpers as widgets
from openbb_terminal.stocks.options import yfinance_model
from typing import Tuple
import options
import plots
from reports.base import Report
from reports.async_base import AsyncReport

def should_include_friday(symbol: str):
    symbols_list = ["SPY"]

    if symbol in symbols_list and "Friday" != datetime.today().strftime("%A"):
        return True
    return False

@dataclass
class OptionReport(AsyncReport):
    narrow_price_range: float = 0.1
    wide_price_range: float = 0.3

    def process_symbol(self, symbol: str) -> Tuple[str, str]:
        htmlcode = widgets.h(1, f"Simple analysis for {symbol}:")
        full_chain = yfinance_model.get_full_option_chain(symbol)
        full_chain["strike"] = full_chain["strike"].astype(float)
        current_price = yfinance_model.get_price(symbol)

        expirations = options.filter_active_volume_expirations(
            full_chain, filter_less_then=1000
        )
        htmlcode += plots.rsi_options_plot(symbol, expirations, False)
        htmlcode += plots.rsi_options_plot(symbol, expirations)

        levels = options.options_levels(full_chain, current_price)
        htmlcode += plots.long_period_plot_with_extra_data(symbol, levels)
        htmlcode += plots.one_day_plot_with_extra_data(symbol, levels)


        price_range = self.narrow_price_range if symbol in ["SPY", "QQQ"] else self.wide_price_range

        htmlcode += plots.absolute_options_concentration_plot(
            full_chain,
            current_price,
            only_current_expiration=True,
            concentration="openInterest",
            price_range=price_range,
        )

        if should_include_friday(symbol):
            htmlcode += plots.absolute_options_concentration_plot(
                full_chain,
                current_price,
                only_next_friday_expiration=True,
                concentration="openInterest",
                price_range=price_range,
            )

        htmlcode += plots.absolute_options_concentration_plot(
            full_chain, current_price, concentration="openInterest", price_range=price_range
        )

        htmlcode += plots.options_gex_plot(full_chain, current_price, only_current_expiration=True)
        if should_include_friday(symbol):
            htmlcode += plots.options_gex_plot(
                full_chain, current_price, only_next_friday_expiration=True, price_range=2*price_range,
            )
        htmlcode += plots.expiration_concentration_plot(
            full_chain, concentration="openInterest"
        )

        return htmlcode, symbol


@dataclass
class OptionReportV2(AsyncReport):
    narrow_price_range: float = 0.1
    wide_price_range: float = 0.3
    def process_symbol(self, symbol: str) -> Tuple[str, str]:
        htmlcode = widgets.h(1, f"Analysis for {symbol}:")
        full_chain = yfinance_model.get_full_option_chain(symbol)
        full_chain["strike"] = full_chain["strike"].astype(float)
        current_price = yfinance_model.get_price(symbol)

        expirations = options.filter_active_open_interest_expirations_in_chain(full_chain, "call")
        htmlcode += plots.rsi_options_plot(symbol, expirations, False)
        
        expirations = options.filter_active_open_interest_expirations_in_chain(full_chain, "put")
        htmlcode += plots.rsi_options_plot(symbol, expirations)

        price_range = self.narrow_price_range if symbol in ["SPY", "QQQ"] else self.wide_price_range
        htmlcode += plots.detailed_option_plot(
            full_chain[full_chain["expiration"] == expirations[0]],
            current_price,
            price_range=price_range,
            description=f"Overview {symbol} {expirations[0]} {int(current_price)}",
        )
        htmlcode += plots.options_gex_plot_v2(
            full_chain[full_chain["expiration"] == expirations[0]],
            current_price,
            price_range=price_range,
            description=f"Overview GEX {symbol} {expirations[0]} {int(current_price)}",
        )

        htmlcode += plots.long_period_plot_with_extra_data(symbol)

        htmlcode += plots.expiration_concentration_plot(
            full_chain, concentration="openInterest"
        )

        if symbol == "SPY":
            htmlcode += plots.stock_bond_correlation_plot()

        return htmlcode, symbol