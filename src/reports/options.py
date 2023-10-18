from datetime import datetime
from openbb_terminal.reports import widget_helpers as widgets
from openbb_terminal.stocks.options import yfinance_model

from reports.base import Report
import options
import plots

def should_include_friday(symbol: str):
    symbols_list = ["SPY"]

    if symbol in symbols_list and "Friday" != datetime.today().strftime("%A"):
        return True
    return False


class OptionReport(Report):
    def process_symbol(self, symbol: str):
        htmlcode = widgets.h(1, f"Simple analysis for {symbol}:")
        full_chain = yfinance_model.get_full_option_chain(symbol)
        full_chain["strike"] = full_chain["strike"].astype(float)
        current_price = yfinance_model.get_price(symbol)

        volume_concentration = options.volatile_concentration(full_chain, filter_less_then=1000)
        htmlcode += plots.rsi_options_plot(symbol, volume_concentration, False)
        htmlcode += plots.rsi_options_plot(symbol, volume_concentration)

        levels = options.options_levels(full_chain, current_price)
        htmlcode += plots.long_period_plot_with_extra_data(symbol, levels)
        htmlcode += plots.one_day_plot_with_extra_data(symbol, levels)

        htmlcode += plots.absolute_options_concentration_plot(
            full_chain,
            current_price,
            only_current_expiration=True,
            concentration="openInterest",
        )

        if should_include_friday(symbol):
            htmlcode += plots.absolute_options_concentration_plot(
                full_chain,
                current_price,
                only_next_friday_expiration=True,
                concentration="openInterest",
            )

        htmlcode += plots.absolute_options_concentration_plot(
            full_chain, current_price, concentration="openInterest"
        )

        htmlcode += plots.absolute_options_concentration_plot(full_chain, current_price)
        htmlcode += plots.absolute_options_concentration_plot(
            full_chain, current_price, only_current_expiration=True
        )
        htmlcode += plots.expiration_concentration_plot(full_chain)
        htmlcode += plots.expiration_concentration_plot(
            full_chain, concentration="openInterest"
        )

        self.body += widgets.add_tab(symbol, htmlcode)
