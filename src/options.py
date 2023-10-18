from typing import Optional

import pandas as pd
from openbb_terminal.stocks.options import op_helpers


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
