import base64
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

import pandas as pd
import talib
import yfinance as yf
from dateutil.relativedelta import relativedelta
from openbb_terminal import OpenBBFigure
from openbb_terminal.core.plots.plotly_ta.ta_class import PlotlyTA
from openbb_terminal.reports import widget_helpers as widgets
from openbb_terminal.stocks import stocks_helper
from openbb_terminal.stocks.options import yfinance_model


def temporary_image_path(file_name):
    Path("/tmp/images/").mkdir(parents=True, exist_ok=True)
    return "/tmp/images/" + file_name + ".png"


def htmlcode_image(image_path: str) -> str:
    bytes = base64.b64encode(open(image_path, "rb").read()).decode("utf-8")
    htmlcode = f'<img src="data:image/png;base64,{bytes}">'
    return htmlcode


# Expiration Concentration
def expiration_concentration_plot(chain, concentration="volume"):
    logging.info(f"Expiration concentration for {concentration}...")
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

    full_path = temporary_image_path("expiration_concentration")
    option_absolute_plot.write_image(
        full_path, format=None, scale=None, width=1600, height=1024, validate=True
    )

    htmlcode = widgets.h(5, f"expiration concentration for {concentration}")
    htmlcode += htmlcode_image(full_path)
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
    logging.info(
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
    full_path = temporary_image_path("absolute_volume")
    option_absolute_plot.write_image(
        full_path, format=None, scale=None, width=1600, height=1024, validate=True
    )

    htmlcode = widgets.h(
        5,
        f"Abosulte {concentration}: only_current_expiration={only_current_expiration}: {current_expiration}, \
        only_next_friday_expiration={only_next_friday_expiration}",
    )

    htmlcode += htmlcode_image(full_path)
    return htmlcode


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
    full_path = temporary_image_path("stock_plot_with_extra_data")
    stock_plot.write_image(
        full_path, format=None, scale=None, width=1600, height=1024, validate=True
    )
    htmlcode = htmlcode_image(full_path)
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
    logging.info(f"Stock with extra data {symbol}...")

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


def rsi_options_plot(symbol, expirations: List[str], show_put=True):
    """Following plot shows RSI momentum for options with different expirations days."""

    tk = yf.Ticker(symbol)
    current_price = yfinance_model.get_price(symbol)

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

        logging.info(option_symbol)
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

    logging.info(f"{symbol} {options_type}, {option_strike}")

    if option_plot:
        full_path = temporary_image_path(f"{symbol}")
        option_plot.write_image(
            full_path, format=None, scale=None, width=1600, height=1024, validate=True
        )

        htmlcode = widgets.h(
            5, f"The RSI momentum plot for following options expirations {expirations}."
        )
        options_type = "PUT:" if show_put else "CALL:"
        htmlcode += widgets.h(5, f"{options_type}: STRIKE: {int(option_strike)}")
        htmlcode += htmlcode_image(full_path)
    else:
        htmlcode = widgets.h(
            5,
            f"No data for {symbol} type {options_type} with {expirations} expiration.",
        )
    return htmlcode
