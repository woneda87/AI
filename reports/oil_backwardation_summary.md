# 2026 WTI and Brent backwardation

Reviewed 2026-11-17 UTC. The local rolling observations end on October 9 and the published Figure 3 fixed observations end on November 16. All spread values are USD per barrel.

## Rolling market observations

The best available M1−M6 observations in the local sample are WTI **+12.77 on September 24** and NYMEX Brent **+12.78 on October 1**. These are sample maxima. The calendar-year highs remain undetermined with 13 WTI and seven Brent observations. On the last common observed day, October 9, Brent was stronger at **+11.65** versus WTI **+5.44**. M1−M2 on October 9 was **+3.47** for Brent and **+0.84** for WTI. The run gives no rolling observation after October 9 from which to infer a late-October change.

## Nominal M1, M2 and M6 prices

On the last common local observation date, 2026-10-09, the underlying Yahoo Finance archive closes were:

| Product | M1 | M2 | M6 | M1−M2 | M1−M6 |
|---|---:|---:|---:|---:|---:|
| WTI CL | CLX26 91.85 | CLZ26 91.01 | CLJ27 86.41 | +0.84 | +5.44 |
| Brent BZ | BZZ26 104.72 | BZF27 101.25 | BZK27 93.07 | +3.47 | +11.65 |

Of 221 candidate sessions, the nominal prices are available independently on 13, 35 and 119 dates for WTI M1, M2 and M6, and on 7, 29 and 112 dates for Brent. A missing leg leaves the spread blank. The local run includes `data/oil_nominal_contract_prices_2026.csv` and `charts/2026_nominal_contract_prices.png`. The interactive HTML includes nominal price traces with exact contract codes.

## Fixed pairs in the published Figure 3

The source is Yahoo Finance daily closing prices for NYMEX contracts. The reference contains 127 observations per product from May 18 through November 16. It measures the fixed pairs independently of the rolling series. [Oil Curve Tracker Figure 3](https://tbysmll.github.io/oil-curve-tracker/)

| Measure | WTI CLZ26−CLK27 | Brent BZF27−BZM27 |
|---|---:|---:|
| Peak in the published six-month window | +15.40 on Sep 15 | +15.59 on Oct 23 |
| Oct 30 close | +11.16 | +15.21 |
| Nov 16 close | +6.54 | +8.76 |
| Change from Oct 30 to Nov 16 | −4.62 | −6.45 |
| 7-session regression ending Nov 16, USD/bbl/session | −0.060 | −0.027 |
| 20-session average ending Nov 16 | +8.47 | +11.43 |
| Percentage of the 127 displayed observations at least as high as Nov 16 | 37.0% | 31.5% |

Brent had the stronger fixed spread on November 16. Both spreads narrowed from October 30 and both 7-session slopes for November 6–16 were negative. The full-year rolling percentile and the November 17 fixed and rolling values remain unverified. The within-window rankings above apply only to the published fixed sample.

Both fixed spreads remained positive on November 16. The lower values versus October 30 offer less evidence of prompt-market tightness from these pairs. The fixed spreads alone cannot establish a physical supply shortage. [Oil Curve Tracker Figure 3](https://tbysmll.github.io/oil-curve-tracker/)
