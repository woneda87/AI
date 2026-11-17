"""Build 2026 oil backwardation artifacts from authorized daily observations."""
import argparse
from pathlib import Path
import fcntl

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from plotly.subplots import make_subplots
import plotly.graph_objects as go

MONTH_CODES = "FGHJKMNQUVXZ"
FIXED = {"CL": ("CLZ26", "CLK27"), "BZ": ("BZF27", "BZM27"), "B": ("BF27", "BM27")}
MARKET = {"CL": "WTI", "BZ": "Brent (NYMEX BZ)", "B": "Brent (ICE B)"}
COLORS = {"CL": "#176b9c", "BZ": "#b05030", "B": "#b05030"}
KEY = ["date", "product", "contract_code", "price_type", "source"]
COLUMNS = [*KEY, "delivery_month", "price", "source_timestamp", "source_timezone", "validation_status"]
START = pd.Timestamp("2026-01-01")
END = pd.Timestamp("2026-12-31")


def contract_code(product, delivery):
    return f"{product}{MONTH_CODES[delivery.month - 1]}{delivery.year % 100:02d}"


def combine_prices(previous, incoming):
    prices = pd.concat([previous, incoming], ignore_index=True)
    if prices.empty:
        return prices
    prices["date"] = pd.to_datetime(prices["date"], format="%Y-%m-%d").dt.normalize()
    months = pd.PeriodIndex(prices["delivery_month"], freq="M")
    expected = [contract_code(product, month) for product, month in zip(prices["product"], months)]
    prices["price"] = pd.to_numeric(prices["price"], errors="raise")
    if (prices["contract_code"] != expected).any() or not prices["product"].isin(MARKET).all():
        raise ValueError("Contract code, delivery month and product must agree")
    if not np.isfinite(prices["price"]).all() or not prices["price_type"].isin(["settlement", "close", "last"]).all():
        raise ValueError("Use finite observed prices and declare settlement, close or last")
    if prices[KEY + ["source_timezone", "validation_status"]].isna().any().any():
        raise ValueError("Observation identity and provenance are required")
    if (prices.groupby(KEY)["price"].nunique() > 1).any():
        raise ValueError("Conflicting observations. Resolve vendor revisions before ingesting")
    timestamps = prices.groupby(KEY)["source_timestamp"]
    if (timestamps.nunique() > 1).any():
        raise ValueError("Conflicting source timestamps for the same observation")
    prices["source_timestamp"] = timestamps.transform("first")
    return prices.drop_duplicates(KEY, keep="first").sort_values(KEY)[COLUMNS]


def spread_series(prices, sessions, expiries, product, price_type, source):
    product_prices = prices.loc[
        prices["product"].eq(product) & prices["price_type"].eq(price_type) & prices["source"].eq(source)
    ]
    quotes = product_prices.set_index(["date", "contract_code"])["price"]
    calendar = expiries.loc[expiries["product"].eq(product)].sort_values("delivery_month")
    months = pd.PeriodIndex(calendar["delivery_month"], freq="M")
    if calendar.empty or list(months) != list(pd.period_range(months[0], months[-1], freq="M")):
        raise ValueError(f"Expiry calendar must contain consecutive delivery months for {product}")
    if not calendar["last_trade_date"].is_monotonic_increasing or calendar["last_trade_date"].isna().any():
        raise ValueError(f"Expiry dates must be present and ordered for {product}")
    rolling, fixed = [], []
    previous_front = None
    last_trade = dict(zip(calendar["delivery_month"], calendar["last_trade_date"]))

    def observation(day, near, far):
        first = quotes.get((day, near), np.nan)
        second = quotes.get((day, far), np.nan)
        return dict(date=day, product=product, price_type=price_type, source=source,
                    near_contract=near, far_contract=far, near_price=first, far_price=second,
                    spread=round(first - second, 2))

    for day in sessions:
        active = calendar.loc[calendar["last_trade_date"].ge(day), "delivery_month"]
        if active.empty:
            raise ValueError(f"No active {product} contract metadata for {day:%Y-%m-%d}")
        month = pd.Period(active.iloc[0], freq="M")
        near = contract_code(product, month)
        rolled = previous_front is not None and previous_front != near
        for rank in (2, 3, 6):
            far = contract_code(product, month + rank - 1)
            rolling.append(dict(observation(day, near, far), series=f"M1-M{rank}", roll=rolled))
        previous_front = near
        first, second = FIXED[product]
        fixed_month = "2026-12" if product == "CL" else "2027-01"
        if fixed_month not in last_trade:
            raise ValueError(f"Missing expiry for fixed contract {first}")
        record = observation(day, first, second)
        if day > last_trade[fixed_month]:
            record.update(near_price=np.nan, spread=np.nan)
        fixed.append(dict(record, series=f"{first}-{second}"))
    return pd.DataFrame(rolling), pd.DataFrame(fixed)


def derived(series):
    slope = series.rolling(7, min_periods=7).apply(lambda values: np.dot(values, np.arange(-3, 4)) / 28, raw=True)
    return series.rolling(20, min_periods=20).mean(), slope


def change(series, offset):
    observed = series.dropna()
    if observed.empty:
        return "unavailable"
    last = observed.index[-1]
    target = last - offset
    baseline = series.loc[:target].tail(1)
    if baseline.empty or baseline.isna().any():
        return "unavailable"
    return f"{last:%b %d} vs {baseline.index[0]:%b %d}: {observed.iloc[-1] - baseline.iloc[0]:+.2f}"


def charts(rolling, fixed, output):
    specs = [
        ("2026_rolling_backwardation", "2026 rolling M1–M6", rolling.loc[rolling["series"].eq("M1-M6")], True),
        ("2026_fixed_backwardation", "Fixed contract spreads", fixed, True),
        ("2026_near_term_backwardation", "2026 rolling M1–M2", rolling.loc[rolling["series"].eq("M1-M2")], False),
    ]
    interactive = make_subplots(rows=3, cols=1, subplot_titles=[s[1] for s in specs], vertical_spacing=.11)
    for row, (filename, title, data, moving_average) in enumerate(specs, 1):
        fig, ax = plt.subplots(figsize=(11, 5), layout="constrained")
        ax.axhline(0, color="#8794a2", lw=.9)
        notes = []
        for product, group in data.groupby("product", sort=False):
            group = group.set_index("date")
            values = group["spread"]
            price_type, source = group[["price_type", "source"]].iloc[0]
            label = f"{MARKET[product]} · {group['series'].iloc[0]} · {price_type}"
            color = COLORS[product]
            ax.plot(values.index, values, color=color, label=label, marker=".", markersize=2)
            contracts = group[["near_contract", "far_contract"]].to_numpy()
            interactive.add_trace(go.Scatter(
                x=values.index, y=values.tolist(), name=label, line_color=color, connectgaps=False,
                customdata=contracts,
                hovertemplate="%{x|%Y-%m-%d}<br>%{customdata[0]} − %{customdata[1]}<br>%{y:+.2f} USD/bbl",
            ), row=row, col=1)
            ma, slope = derived(values)
            if moving_average:
                ax.plot(ma.index, ma, color=color, ls="--", lw=1.3, label=f"{MARKET[product]} 20-session MA")
                interactive.add_trace(go.Scatter(x=ma.index, y=ma.tolist(), name=f"{label} 20-session MA",
                                                line=dict(color=color, dash="dash"), connectgaps=False), row=row, col=1)
            if row == 1:
                for day in group.index[group["roll"]]:
                    ax.axvline(day, color=color, ls=":", alpha=.35, lw=.9)
                    interactive.add_vline(x=day.to_pydatetime(), line_color=color, line_dash="dot",
                                          opacity=.35, row=row, col=1)
            if row == 2:
                latest = values.last_valid_index()
                text = "unavailable"
                if latest is not None and pd.notna(slope.loc[latest]):
                    text = f"{slope.loc[latest]:+.3f} USD/bbl/session"
                detail = f"7-session slope {text}"
            elif row == 3:
                detail = f"1 week {change(values, pd.DateOffset(weeks=1))}   |   1 month {change(values, pd.DateOffset(months=1))}"
            else:
                detail = "dotted verticals mark expiry rolls"
            notes.append(f"{MARKET[product]} · {detail} · {source}")
        ax.set(xlim=(START, END), ylabel="USD per barrel", title=title, xlabel="\n".join(notes))
        ax.grid(axis="y", alpha=.22)
        ax.legend(loc="best", fontsize=8)
        fig.savefig(output / f"{filename}.png", dpi=160)
        plt.close(fig)
        interactive.add_hline(y=0, line_color="#8794a2", row=row, col=1)
        interactive.update_xaxes(range=[START, END], row=row, col=1, rangeslider_visible=False)
        interactive.update_yaxes(title_text="USD/bbl", row=row, col=1)
        interactive.layout.annotations[row-1].hovertext = "<br>".join(notes)
    dates = pd.DatetimeIndex(fixed.loc[fixed["spread"].notna(), "date"].unique()).sort_values()
    sessions = pd.DatetimeIndex(fixed["date"].unique()).sort_values()
    if len(dates):
        sessions = sessions[sessions <= dates[-1]]
        buttons = [dict(label="Full year", method="relayout", args=[{"xaxis2.range": [START, END]}])]
        for count in (7, 20):
            if len(sessions) >= count:
                window = [sessions[-count] - pd.Timedelta(hours=12), sessions[-1] + pd.Timedelta(hours=12)]
                buttons.append(dict(label=f"Latest {count} sessions", method="relayout",
                                    args=[{"xaxis2.range": window}]))
        interactive.update_layout(updatemenus=[dict(type="buttons", direction="right", x=0, y=.675,
                                                    xanchor="left", yanchor="bottom", buttons=buttons)])
    interactive.update_layout(title="2026 oil backwardation", height=1200, template="plotly_white",
                              legend=dict(orientation="h", y=-.06), margin=dict(b=130))
    interactive.write_html(output / "oil_backwardation_interactive.html", include_plotlyjs=True, div_id="oil-backwardation-2026")


def run(args):
    data = args.output / "data"
    output_charts = args.output / "charts"
    data.mkdir(parents=True, exist_ok=True)
    output_charts.mkdir(parents=True, exist_ok=True)
    store = data / "oil_contract_settlements_2026.csv"
    incoming = pd.read_csv(args.prices, dtype={"delivery_month": str})
    previous = pd.read_csv(store) if store.exists() else incoming.iloc[:0].copy()
    prices = combine_prices(previous, incoming)
    prices = prices.loc[prices["date"].between(START, END)]
    expiries = pd.read_csv(args.expiries, parse_dates=["last_trade_date"])
    if expiries.duplicated(["product", "delivery_month"]).any():
        raise ValueError("Duplicate product/delivery month in expiry calendar")
    sessions = pd.read_csv(args.sessions, parse_dates=["date"])
    if sessions.duplicated(["product", "date"]).any():
        raise ValueError("Duplicate product/date in session calendar")
    curves, fixed = [], []
    for selection in args.series:
        product, price_type, source = selection.split(":", 2)
        days = pd.DatetimeIndex(sessions.loc[sessions["product"].eq(product), "date"])
        days = days[(days >= START) & (days <= pd.Timestamp(args.through))].sort_values()
        if days.empty:
            raise ValueError(f"No sessions for {product}")
        r, f = spread_series(prices, days, expiries, product, price_type, source)
        curves.append(r)
        fixed.append(f)
    rolling, fixed = pd.concat(curves), pd.concat(fixed)
    for frame in (rolling, fixed):
        groups = frame.groupby(["product", "series"], sort=False)["spread"]
        frame["ma20"] = groups.transform(lambda s: derived(s)[0])
        if frame is fixed:
            frame["slope7"] = groups.transform(lambda s: derived(s)[1])
    for name, frame in [(store.name, prices), ("oil_backwardation_rolling_2026.csv", rolling),
                        ("oil_backwardation_fixed_2026.csv", fixed)]:
        path = data / name
        temp = path.with_suffix(".tmp")
        frame.to_csv(temp, index=False, float_format="%.6f")
        temp.replace(path)
    charts(rolling, fixed, output_charts)
    coverage = pd.concat([rolling, fixed]).groupby(["product", "series"])["spread"].agg(["count", "size"])
    print(coverage.to_string())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ["prices", "sessions", "expiries", "output"]:
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--through", required=True)
    parser.add_argument("--series", action="append", required=True, metavar="PRODUCT:PRICE_TYPE:SOURCE")
    args = parser.parse_args()
    products = [s.split(":", 1)[0] for s in args.series]
    if not set(products) <= set(MARKET) or len(products) != len(set(products)) or {"BZ", "B"} <= set(products):
        parser.error("Select one source and basis for each product and at most one Brent product")
    if not START <= pd.Timestamp(args.through) <= END:
        parser.error("--through must be a 2026 trade date")
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / ".ingest.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        run(args)


if __name__ == "__main__":
    main()
