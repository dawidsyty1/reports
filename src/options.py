import base64
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd
import talib
import yfinance as yf
from dateutil.relativedelta import relativedelta
from openbb_terminal import OpenBBFigure
from openbb_terminal.core.plots.plotly_ta.ta_class import PlotlyTA
from openbb_terminal.reports import widget_helpers as widgets
from openbb_terminal.stocks import stocks_helper
from openbb_terminal.stocks.options import op_helpers, yfinance_model

from reports import Report


def full_image_path(file_name):
    Path("/tmp/images/").mkdir(parents=True, exist_ok=True)
    return "/tmp/images/" + file_name + ".png"


# Volatile Concentration
def volatile_concentration(chain, filter_less_then: int = 0):
    print("volatile concentration...")
    expiration_concentraion = {}

    for expiry, local_chain in chain.groupby(["expiration"]):
        call = local_chain[local_chain["optionType"] == "call"]["volume"].sum()
        puts = local_chain[local_chain["optionType"] == "put"]["volume"].sum()
        expiration_concentraion[expiry] = call + puts

    return_expiration_concentraion = {}
    # Filter less then 1k Volume:
    for key in expiration_concentraion:
        if expiration_concentraion[key] > filter_less_then:
            return_expiration_concentraion[key] = expiration_concentraion[key]

    if not len(return_expiration_concentraion) and filter_less_then:
        return volatile_concentration(chain, filter_less_then - 1000)

    return return_expiration_concentraion


# Expiration Concentration
def expiration_concentration_plot(chain, concentration="volume"):
    print(f"Expiration concentration for {concentration}...")
    expiration_concentraion = {"expiry": [], "call": [], "put": []}
    # openInterest

    for index, (expiry, local_chain) in enumerate(chain.groupby(["expiration"])):
        expiration_concentraion["expiry"].append(f"{expiry}.")
        expiration_concentraion["call"].append(
            local_chain[local_chain["optionType"] == "call"][concentration].sum()
        )
        expiration_concentraion["put"].append(
            -local_chain[local_chain["optionType"] == "put"][concentration].sum()
        )

    expiration_concentraion = pd.DataFrame.from_dict(expiration_concentraion)

    option_absolute_plot = OpenBBFigure()
    option_absolute_plot.add_bar(
        x=expiration_concentraion["expiry"],
        y=expiration_concentraion["call"],
        name=f"Calls: {concentration}",
        marker_color="green",
        width=0.8,
    )
    option_absolute_plot.add_bar(
        x=expiration_concentraion["expiry"],
        y=expiration_concentraion["put"],
        name=f"Puts: {concentration}",
        marker_color="red",
        width=0.8,
    )

    full_path = full_image_path("expiration_concentration")
    option_absolute_plot.write_image(
        full_path, format=None, scale=None, width=1600, height=1024, validate=True
    )

    htmlcode = widgets.h(5, f"expiration concentration for {concentration}")
    htmlcode += '<img src="data:image/png;base64,{0}">'.format(
        base64.b64encode(open(full_path, "rb").read()).decode("utf-8")
    )
    return htmlcode


def absolute_options_concentration_plot(
    chain,
    current_price,
    only_current_expiration=False,
    only_next_friday_expiration=False,
    concentration="volume",
):
    current_expiration = chain.expiration.iloc[0]
    if only_current_expiration:
        chain = chain[chain["expiration"] == current_expiration]

    elif only_next_friday_expiration:
        today = datetime.today()
        friday_expiration = today + timedelta((4 - today.weekday()) % 7)
        current_expiration = friday_expiration.strftime("%Y-%m-%d")
        chain = chain[chain["expiration"] == current_expiration]

    if concentration == "volume":
        call_field_name = "volume_call"
        put_field_name = "volume_put"
    else:
        call_field_name = "openInterest_call"
        put_field_name = "openInterest_put"

    # option chain calculation require for absolute volume
    print(
        f"Absolute {concentration} for\
        only_current_expiration={only_current_expiration}: {current_expiration},\
        only_next_friday_expiration={only_next_friday_expiration}"
    )
    min_strike = 0.95 * current_price
    max_strike = 1.05 * current_price

    chain = chain[chain["strike"] >= min_strike]
    chain = chain[chain["strike"] <= max_strike]

    calls = chain[chain["optionType"] == "call"]
    puts = chain[chain["optionType"] == "put"]

    option_chain = pd.merge(
        calls[["volume", "strike", "openInterest"]],
        puts[["volume", "strike", "openInterest"]],
        on="strike",
    )

    option_chain = option_chain.rename(
        columns={
            "volume_x": "volume_call",
            "volume_y": "volume_put",
            "openInterest_x": "openInterest_call",
            "openInterest_y": "openInterest_put",
        }
    )

    option_chain[["openInterest_put", "volume_put"]] = (
        option_chain[["openInterest_put", "volume_put"]] * -1
    )
    option_chain[["openInterest_call", "volume_call"]] = option_chain[
        ["openInterest_call", "volume_call"]
    ]
    # calculate put/call wall above/bellow price

    try:
        put_wall_id = option_chain[option_chain["strike"] <= current_price][
            put_field_name
        ].idxmin()
        call_wall_id = option_chain[option_chain["strike"] >= current_price][
            call_field_name
        ].idxmax()
        put_wall = option_chain.iloc[put_wall_id].strike
        call_wall = option_chain.iloc[call_wall_id].strike
    except Exception:
        put_wall = None
        call_wall = None
    option_absolute_plot = OpenBBFigure()

    option_absolute_plot.add_bar(
        x=option_chain.strike,
        y=option_chain[call_field_name],
        name=call_field_name,
        marker_color="green",
        width=0.8,
    )

    option_absolute_plot.add_bar(
        x=option_chain.strike,
        y=option_chain[put_field_name],
        name=put_field_name,
        marker_color="red",
        width=0.8,
    )
    option_absolute_plot.add_vline_legend(
        x=current_price,
        name=f"Current stock price: {current_price}",
        line=dict(width=0.8, color="white"),
    )
    if put_wall:
        option_absolute_plot.add_vline_legend(
            x=put_wall,
            name=f"Put wall = {put_wall}",
            line=dict(width=0.8, color="red"),
        )
    if call_wall:
        option_absolute_plot.add_vline_legend(
            x=call_wall,
            name=f"Call wall = {call_wall}",
            line=dict(width=0.8, color="blue"),
        )

    option_absolute_plot.update_layout()
    full_path = full_image_path("absolute_volume")
    option_absolute_plot.write_image(
        full_path, format=None, scale=None, width=1600, height=1024, validate=True
    )

    htmlcode = widgets.h(
        5,
        f"Abosulte {concentration}: only_current_expiration={only_current_expiration}: {current_expiration}, \
        only_next_friday_expiration={only_next_friday_expiration}",
    )

    htmlcode += '<img src="data:image/png;base64,{0}">'.format(
        base64.b64encode(open(full_path, "rb").read()).decode("utf-8")
    )
    return htmlcode


def call_put_walls(chain, current_price):
    print("Call Put walls...")
    min_strike = 0.95 * current_price
    max_strike = 1.05 * current_price

    chain = chain[chain["strike"] >= min_strike]
    chain = chain[chain["strike"] <= max_strike]

    calls = chain[chain["optionType"] == "call"]
    puts = chain[chain["optionType"] == "put"]

    option_chain = pd.merge(
        calls[["volume", "strike", "openInterest"]],
        puts[["volume", "strike", "openInterest"]],
        on="strike",
    )

    option_chain = option_chain.rename(
        columns={
            "volume_x": "volume_call",
            "volume_y": "volume_put",
            "openInterest_x": "openInterest_call",
            "openInterest_y": "openInterest_put",
        }
    )

    option_chain[["openInterest_put", "volume_put"]] = (
        option_chain[["openInterest_put", "volume_put"]] * -1
    )
    option_chain[["openInterest_call", "volume_call"]] = option_chain[
        ["openInterest_call", "volume_call"]
    ]
    # calculate put/call wall above/bellow price
    put_wall_id = option_chain[option_chain["strike"] <= current_price][
        "volume_put"
    ].idxmin()
    call_wall_id = option_chain[option_chain["strike"] >= current_price][
        "volume_call"
    ].idxmax()
    put_wall = option_chain.iloc[put_wall_id]
    call_wall = option_chain.iloc[call_wall_id]

    return put_wall.strike, call_wall.strike


def options_levels(full_chain, current_price):
    # calculate largest gamma
    print("Calculating options levels...")
    put_wall, call_wall = call_put_walls(full_chain, current_price)
    levels = {
        "Curent price": current_price,
        "Put wall": put_wall,
        "Call wall": call_wall,
    }
    div_cont: float = 0
    rf: Optional[float] = None
    show_all: bool = False

    min_strike = 0.95 * current_price
    max_strike = 1.05 * current_price
    largest_values = []

    for expiry, chain in full_chain.groupby(["expiration"]):
        chain = chain[chain["strike"] >= min_strike]
        chain = chain[chain["strike"] <= max_strike]
        results = op_helpers.get_greeks(
            current_price=current_price,
            expire=expiry,
            calls=chain[chain["optionType"] == "call"],
            puts=chain[chain["optionType"] == "put"],
            div_cont=div_cont,
            rf=rf,
            opt_type=1,
            show_extra_greeks=show_all,
        )
        values = results.sort_values(by=["Gamma"], ascending=False)
        if not pd.isna(values["Gamma"].iloc[0]):
            largest_values.append(
                {
                    "Strike": values["Strike"].iloc[0],
                    "Gamma": float(values["Gamma"].iloc[0]),
                }
            )

    for expiry, chain in full_chain.groupby(["expiration"]):
        chain = chain[chain["strike"] >= min_strike]
        chain = chain[chain["strike"] <= max_strike]
        results = op_helpers.get_greeks(
            current_price=current_price,
            expire=expiry,
            calls=chain[chain["optionType"] == "call"],
            puts=chain[chain["optionType"] == "put"],
            div_cont=div_cont,
            rf=rf,
            opt_type=-1,
            show_extra_greeks=show_all,
        )
        values = results.sort_values(by=["Gamma"], ascending=False)
        if not pd.isna(values["Gamma"].iloc[0]):
            largest_values.append(
                {
                    "Strike": values["Strike"].iloc[0],
                    "Gamma": float(values["Gamma"].iloc[0]),
                }
            )

    largest_values = sorted(largest_values, key=lambda d: d["Gamma"], reverse=True)[:5]
    for index, value in enumerate(largest_values):
        levels[f"Large Gamma {index}"] = value["Strike"]

    return levels


def largest_gamma(full_chain, current_price):
    # calculate largest gamma
    print("Calculating largest gamma...")
    div_cont: float = 0
    rf: Optional[float] = None
    opt_type: int = 1
    show_all: bool = False

    greeks = {}
    min_strike = 0.95 * current_price
    max_strike = 1.05 * current_price

    for expiry, chain in full_chain.groupby(["expiration"]):
        chain = chain[chain["strike"] >= min_strike]
        chain = chain[chain["strike"] <= max_strike]
        results = op_helpers.get_greeks(
            current_price=current_price,
            expire=expiry,
            calls=chain[chain["optionType"] == "call"],
            puts=chain[chain["optionType"] == "put"],
            div_cont=div_cont,
            rf=rf,
            opt_type=opt_type,
            show_extra_greeks=show_all,
        )
        greeks[expiry] = results.sort_values(by=["Gamma"], ascending=False)

    largest_gamma_dict = {"expiry": 0, "strike": 0, "gamma": 0}

    for expiry, greek in greeks.items():
        strike = greek["Strike"].iloc[0]
        gamma = greek["Gamma"].iloc[0]
        if largest_gamma_dict["gamma"] < gamma:
            largest_gamma_dict = {"expiry": expiry, "strike": strike, "gamma": gamma}
    return largest_gamma_dict["strike"]


def color_per_level(level):
    color_per_type = {
        "Put wall": "red",
        "Curent price": "yellow",
        "Call wall": "green",
        "Large Gamma 0": "blue",
    }
    color = "white"
    if level in color_per_type:
        color = color_per_type[level]

    return color


def stock_plot_with_extra_data(stock, levels):
    ta = PlotlyTA()
    stock_plot = ta.plot(stock)
    for level in levels:
        strike = levels[level]
        stock_plot.add_hline_legend(
            y=strike,
            name=f"{level} : {strike}",
            line=dict(dash="dash", width=0.5, color=color_per_level(level)),
        )
    stock_plot.update_layout(showlegend=True, xaxis=dict(type="category"))
    full_path = full_image_path("stock_plot_with_extra_data")
    stock_plot.write_image(
        full_path, format=None, scale=None, width=1600, height=1024, validate=True
    )
    htmlcode = '<img src="data:image/png;base64,{0}">'.format(
        base64.b64encode(open(full_path, "rb").read()).decode("utf-8")
    )
    return htmlcode


def long_period_plot_with_extra_data(symbol, levels):
    start_date = datetime.strftime(
        datetime.now() + relativedelta(months=-3), "%Y-%m-%d"
    )
    interval = 60
    stock = stocks_helper.load(symbol, interval=interval, start_date=start_date)

    htmlcode = widgets.h(5, "Longterm chart with extra data:")
    htmlcode += stock_plot_with_extra_data(stock, levels)
    return htmlcode


def one_day_plot_with_extra_data(symbol, levels):
    print(f"Stock with extra data {symbol}...")

    days_left = 3
    if datetime.now().today().weekday() == 0 or datetime.now().today().weekday() == 1:
        days_left = 5

    start_date = datetime.strftime(
        datetime.now() + relativedelta(days=-days_left), "%Y-%m-%d"
    )
    interval = 15
    stock = stocks_helper.load(symbol, interval=interval, start_date=start_date)
    htmlcode = widgets.h(5, "One day trading chart with extra data:")
    htmlcode += stock_plot_with_extra_data(stock, levels)
    return htmlcode


def rsi_options_plot(symbol, volume_concentration, show_put=True):
    tk = yf.Ticker(symbol)
    current_price = yfinance_model.get_price(symbol)
    dte = {
        (datetime.strptime(exp, "%Y-%m-%d") - datetime.now()).days: exp
        for exp in volume_concentration
    }
    expirations = []

    # get expirations for options 50, 100 and 150 dte
    for close_to_in_days in [150, 100, 50]:  # , 100, 150]:
        dte_close_to = min(dte.keys(), key=lambda x: abs(x - close_to_in_days))
        expirations.append(dte[dte_close_to])
        del dte[dte_close_to]

    option_plot = None
    color_per_expiration = {
        0: "white",
        1: "red",
        2: "blue",
    }

    for index, exp in enumerate(expirations):
        opt = tk.option_chain(exp)
        opt.calls["optionType"] = "call"
        opt.puts["optionType"] = "put"

        if show_put:
            option_strike = 0.90 * current_price
            close_to = opt.puts.iloc[
                (opt.puts["strike"] - option_strike).abs().argsort()[:10]
            ]
            close_to = close_to.sort_values(by=["volume"], ascending=False)
            option_symbol = close_to["contractSymbol"].iloc[0]
            option_strike = close_to["strike"].iloc[0]
        else:
            option_strike = 1.10 * current_price
            close_to = opt.calls.iloc[
                (opt.calls["strike"] - option_strike).abs().argsort()[:10]
            ]
            close_to = close_to.sort_values(by=["volume"], ascending=False)
            option_symbol = close_to["contractSymbol"].iloc[0]
            option_strike = close_to["strike"].iloc[0]

        print(option_symbol)
        option_data = yf.download(option_symbol)

        option_data["rsi"] = (
            talib.RSI(option_data["Close"]) if len(option_data["Close"]) else 0
        )
        option_data = option_data[14:]

        if not option_plot:
            if not len(option_data["Close"]):
                continue

            option_plot = OpenBBFigure.create_subplots()
            option_plot.add_shape(
                type="line",
                name="RSI Trend",
                x0=option_data.index[0],
                y0=50,
                x1=option_data.index[-1],
                y1=50,
                line=dict(color="white", width=0.8),
                row=1,
                col=1,
                secondary_y=False,
            )
        color = color_per_expiration[index]
        option_plot.add_scatter(
            x=option_data.index,
            y=option_data["rsi"],
            name=f"{exp}: {option_strike}",
            orientation="h",
            showlegend=True,
            secondary_y=False,
            line=dict(color=color, width=0.8),
        )
    options_type = "PUT:" if show_put else "CALL:"

    print(symbol, options_type, option_strike)

    if option_plot:
        full_path = full_image_path(f"{symbol}")
        option_plot.write_image(
            full_path, format=None, scale=None, width=1600, height=1024, validate=True
        )

        htmlcode = widgets.h(
            5, f"The RSI momentum plot for following options expirations {expirations}."
        )
        options_type = "PUT:" if show_put else "CALL:"
        htmlcode += widgets.h(5, f"{options_type}: STRIKE: {int(option_strike)}")
        htmlcode += '<img src="data:image/png;base64,{0}">'.format(
            base64.b64encode(open(full_path, "rb").read()).decode("utf-8")
        )
    else:
        htmlcode = widgets.h(
            5,
            f"No data for {symbol} type {options_type} with {expirations} expiration.",
        )
    return htmlcode


def should_include_friday(symbol):
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

        volume_concentration = volatile_concentration(full_chain, filter_less_then=1000)
        htmlcode += rsi_options_plot(symbol, volume_concentration, False)
        htmlcode += rsi_options_plot(symbol, volume_concentration)

        levels = options_levels(full_chain, current_price)
        htmlcode += long_period_plot_with_extra_data(symbol, levels)
        htmlcode += one_day_plot_with_extra_data(symbol, levels)

        htmlcode += absolute_options_concentration_plot(
            full_chain,
            current_price,
            only_current_expiration=True,
            concentration="openInterest",
        )

        if should_include_friday(symbol):
            htmlcode += absolute_options_concentration_plot(
                full_chain,
                current_price,
                only_next_friday_expiration=True,
                concentration="openInterest",
            )

        htmlcode += absolute_options_concentration_plot(
            full_chain, current_price, concentration="openInterest"
        )

        htmlcode += absolute_options_concentration_plot(full_chain, current_price)
        htmlcode += absolute_options_concentration_plot(
            full_chain, current_price, only_current_expiration=True
        )
        htmlcode += expiration_concentration_plot(full_chain)
        htmlcode += expiration_concentration_plot(
            full_chain, concentration="openInterest"
        )

        self.body += widgets.add_tab(symbol, htmlcode)
