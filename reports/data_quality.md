# 2026 oil backwardation data quality

Review date 2026-11-17 UTC. The reproducible research run uses NYMEX CL and NYMEX Brent Last Day Financial BZ daily vendor closes. The local output sits under `/workspace/scratch/oil_backwardation_2026/`. Public repository coverage of underlying redistributed data is zero.

| Source | What was available | Result |
|---|---|---|
| [CME WTI settlement page](https://www.cmegroup.com/markets/energy/crude-oil/light-sweet-crude.settlements.html) | A trade-date-specific probe returned the 2026-11-16 final report with separate Last and Settle columns. | No authorized bulk series was obtained. The [CME data terms](https://www.cmegroup.com/trading/market-data-explanation-disclaimer.html) require authorization for collection, processing and redistribution. |
| [ICE Report Center](https://www.ice.com/report-center) | Exchange reports and a historical end-of-day subscription/purchase route. | No ICE Brent series was obtained for use. Public report terms restrict onward disclosure and no authorized historical feed was supplied. |
| [Yahoo Finance direct chart endpoint](https://query1.finance.yahoo.com/v8/finance/chart/CLG26.NYM?range=1y&interval=1d) | The tested 2026 WTI contract returned HTTP 429. | No direct rows for that probe. Only dated, identifiable contracts in an existing public research archive were used for the local run. |
| [Data4ThePeople archive methodology](https://github.com/Data4ThePeople/spr-exchange/blob/f46fa7d299c9ec0074b43a9c851eaa23b70e227e/DATASETS.md) | 10,862 dated contract closes, 6,982 CL and 3,880 BZ. Dated symbols normalize by removing `.NYM`. The archive notes material Yahoo revisions on a later re-pull. | Local research basis is `close`. The source's stated publication practice is derived figures and selected values. Repository commits exclude the bulk observations and generated dataset and charts. |
| [VIX TermLab WTI](https://vixtermlab.com/wti), [Brent](https://vixtermlab.com/brent), [license](https://vixtermlab.com/license) | 179 reported sessions from 2026-01-02 to 2026-09-18. Brent is BZ and the provider describes its inputs as daily closing bars. | Used contract last-trading-date metadata as a calendar reference. VIX TermLab closes were excluded from this run. The terms do not grant a bulk copy or redistribution license. |

All 10,862 tidy rows matched the pinned raw Yahoo bars by contract, exchange-local date and close to a cent. The underlying CSV records the raw bar timestamp in UTC and the vendor time zone (America/New_York). The bar timestamp identifies the daily date bucket. The time of the closing trade or settlement is unknown.

## Coverage

The local denominator is 221 candidate NYMEX dates per market, through 2026-11-17. It uses the 194 published archive dates on CLZ26 through October 9 and 27 subsequent weekdays. This proxy is not a certified exchange settlement calendar. January 1 has no observed settlement in the archive. The PNG and HTML axes extend through December 31. Dates after the run cutoff carry no observations.

| Product | Daily series | Coverage | Missing candidate dates |
|---|---|---|---|
| WTI CL | Each of M1−M2, M1−M3, M1−M6 | 13 / 221 (5.9%), Sep 23–Oct 9 | 208 |
| Brent BZ | Each of M1−M2, M1−M3, M1−M6 | 7 / 221 (3.2%), Oct 1–9 | 214 |
| WTI CL | CLZ26−CLK27 | 194 / 221 (87.8%), Jan 2–Oct 9 | 27 |
| Brent BZ | BZF27−BZM27 | 194 / 221 (87.8%), Jan 2–Oct 9 | 27 |

Most rolling gaps arise from absent expired front contracts. Both fixed series have a continuous archive run through October 9 and blank candidate sessions thereafter. A blank inside a 7- or 20-session calculation invalidates that window. Timestamp gaps, contract gaps and the later dates were not imputed. M1–M6 has insufficient contiguous observations for its 20-session mean in this run. The near-term one-calendar-month changes are also unavailable.

## Contract and arithmetic checks

The front remains eligible on its published last trading day. The next candidate session selects the next delivery month. Far legs use delivery-month offsets of one, two and five. Missing observations preserve the scheduled contract ranks. For example, WTI changes from CLV26 after September 22 to CLX26 on September 23 and Brent changes from BZX26 after September 30 to BZZ26 on October 1. The fixed pairs preserve their contract IDs across rolls.

The run found zero duplicate observation keys and zero duplicate spread keys. A many-to-one join on date, product, normalized contract code, source and price type reconciled all 448 nonblank spreads to their two prices and the signed subtraction to USD 0.01 per barrel. All emitted missing spreads reconciled to the missing-leg inputs. Unit tests exercise contract identity, duplicate conflicts, roll boundaries, missing legs, same-source/same-type pairing, backwardation and contango signs, and moving windows across gaps.

## Figure 3 comparison

Inspected [revision 3be26ab](https://github.com/tbysmll/oil-curve-tracker/tree/3be26abec6633c015459a1ce6030b6b82858672d), which has no repository license file. Figure 3 ranks the latest curve, holds its first and sixth contracts fixed, subtracts matching same-date observations, and shows six months. The plotted history comes from Yahoo daily Close, classified by the project as settlement after its 22:00 London cutoff. That cutoff alone provides no official settlement attestation. The curve used to select the fixed contracts can forward-fill individual back-month prices for three sessions on fallback, whereas the historical Figure 3 subtraction drops missing legs. The checked-in snapshots lack per-observation price-type and fill flags.

Read the underlying values from the public Plotly figure rather than estimating from SVG pixels. Matched NYMEX CLZ26 and CLK27 and NYMEX BZF27 and BZM27 from 2026-05-18 through 2026-10-09. In both markets **101 of 101 overlapping daily spreads match exactly** to a cent. Contract identities, trade dates and Yahoo Close input basis agree. Figure 3 is an external consistency check against another presentation of the same vendor data. Independent official settlement validation and validation of rolling expiry transitions against Figure 3 remain unavailable.

## WTI contract pairs by calendar month

The separate calendar-month run schedules CLG26−CLH26 in January, CLH26−CLJ26 in February, CLX26−CLZ26 in October, and CLZ26−CLF27 in November. The pair changes at the start of the trade month. The earlier leg must still be trading. For example, January dates after CLG26's last trading day (January 20) remain blank until the February pair begins, even if an expired-contract row is still displayed.

From the 221 candidate dates through November 17, 152 are eligible for the scheduled pair. The Yahoo archive has seven usable CLX26−CLZ26 dates, October 1–9. A local reference chart displays 14 additional source-specific markers, including one January VIX TermLab/IBKR daily close, two published settlement observations, and 11 Oil Curve Tracker snapshots with unverified fill status. November 13 has two sourced readings with distinct bases. The reference points do not enter the main archive export. [VIX TermLab](https://vixtermlab.com/wti) · [CME bulletin values as quoted by Baratelli](https://baratelliinstitute.com/oil-futures-curve) · [Kresmion futures curves](https://kresmion.com/tools/futures-curve) · [Oil Curve Tracker](https://tbysmll.github.io/oil-curve-tracker/)

The CME page displays settlement rows by delivery month. CME documents bulk historical access through DataMine, which serves entitled files. The anonymous Historical Futures Data November CL sample was checked and contains one 10-second OHLC series without a contract identifier or settlement field. It cannot supply the two dated settlement legs. [CME settlement FAQ](https://www.cmegroup.com/articles/faqs/access-to-cme-group-settlement-data-faq.html) · [CME DataMine API](https://www.cmegroup.com/datamine/datamine-api.html) · [CL sample](https://historicalfuturesdata.com/en/browse/CL)
