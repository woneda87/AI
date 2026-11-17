import unittest

import pandas as pd

from oil_backwardation.pipeline import COLUMNS, combine_prices, contract_code, derived, nominal_prices, spread_series


class SpreadTests(unittest.TestCase):
    def fixture(self, *observations):
        return pd.DataFrame(observations, columns=COLUMNS)

    def quote(self, date, code, month, price, price_type="settlement", source="exchange"):
        return date, "CL", code, price_type, source, month, price, None, "America/Chicago", "verified"

    def test_contract_identity_and_duplicate_conflicts(self):
        row = self.quote("2026-11-20", "CLZ26", "2026-12", 84)
        prices = self.fixture(row)
        self.assertEqual(len(combine_prices(prices, prices)), 1)
        timestamped = prices.assign(source_timestamp="2026-11-20T05:00:00Z")
        self.assertEqual(combine_prices(prices, timestamped)["source_timestamp"].iloc[0],
                         "2026-11-20T05:00:00Z")
        with self.assertRaisesRegex(ValueError, "Conflicting"):
            combine_prices(prices, self.fixture(self.quote("2026-11-20", "CLZ26", "2026-12", 86)))
        with self.assertRaisesRegex(ValueError, "delivery month"):
            combine_prices(prices, self.fixture(self.quote("2026-11-20", "CLZ26", "2027-01", 84)))
        self.assertEqual(contract_code("BZ", pd.Period("2027-06", freq="M")), "BZM27")

    def test_expiry_roll_missing_quotes_and_price_type(self):
        prices = combine_prices(self.fixture(), self.fixture(
            self.quote("2026-11-20", "CLZ26", "2026-12", 84),
            self.quote("2026-11-20", "CLF27", "2027-01", 82),
            self.quote("2026-11-20", "CLK27", "2027-05", 83),
            self.quote("2026-11-20", "CLG27", "2027-02", 74, "last"),
            self.quote("2026-11-20", "CLG27", "2027-02", 77, source="other"),
            self.quote("2026-11-23", "CLF27", "2027-01", 81),
            self.quote("2026-11-23", "CLG27", "2027-02", 82),
        ))
        dates = pd.to_datetime(["2026-11-20", "2026-11-23"])
        expiries = pd.DataFrame({
            "product": "CL",
            "delivery_month": ["2026-12", "2027-01"],
            "last_trade_date": pd.to_datetime(["2026-11-20", "2026-12-21"]),
        })
        rolling, fixed = spread_series(prices, dates, expiries, "CL", "settlement", "exchange")
        self.assertEqual(rolling["roll"].tolist(), [False] * 3 + [True] * 3)
        self.assertEqual(rolling.loc[0, "spread"], 2)
        self.assertTrue(pd.isna(rolling.loc[1, "spread"]))
        self.assertEqual(rolling.loc[2, "far_contract"], "CLK27")
        self.assertEqual(rolling.loc[3, "spread"], -1)
        self.assertEqual(fixed.loc[0, "spread"], 1)
        self.assertTrue(pd.isna(fixed.loc[1, "spread"]))
        nominal = nominal_prices(rolling).pivot(index="date", columns="rank", values="price")
        self.assertEqual(nominal.loc[dates[0], "M6"], 83)
        self.assertEqual(nominal.loc[dates[1], "M1"], 81)
        self.assertEqual(nominal.loc[dates[1], "M2"], 82)
        self.assertTrue(pd.isna(nominal.loc[dates[1], "M6"]))

    def test_derived_spreads_preserve_missing_sessions(self):
        values = pd.Series(range(22), dtype=float)
        values.iloc[20] = float("nan")
        mean, slope = derived(values)
        self.assertAlmostEqual(mean.iloc[19], 9.5)
        self.assertAlmostEqual(slope.iloc[19], 1)
        self.assertTrue(pd.isna(mean.iloc[21]))
        self.assertTrue(pd.isna(slope.iloc[21]))
