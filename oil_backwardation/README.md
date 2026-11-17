# Reproduce the 2026 oil backwardation charts

Use Python 3.10 or later on Linux. Supply a daily contract-price export you are authorized to process and session and expiry calendars for each selected exchange product.

```sh
python -m pip install -r oil_backwardation/requirements.txt
python -m unittest oil_backwardation.test_pipeline -v
python -m oil_backwardation.pipeline \
  --prices /path/to/prices.csv --sessions /path/to/sessions.csv \
  --expiries /path/to/expiries.csv --output /path/to/output \
  --through 2026-11-17 \
  --series 'CL:settlement:Licensed CME feed' \
  --series 'B:settlement:Licensed ICE feed'
```

Price CSV columns. `date,product,contract_code,price_type,source,delivery_month,price,source_timestamp,source_timezone,validation_status`. Use ISO trade dates, delivery months as YYYY-MM, raw unadjusted USD/bbl prices, and contract codes such as CLZ26. Supply the source timestamp in ISO 8601 when known, the source time zone separately, and a validation status such as `exchange_final`. Leave an unavailable timestamp blank. Omit missing observations, and use the exact source label in the series selector. `close`, `last`, and `settlement` are distinct bases. NYMEX Brent Last Day Financial is `BZ`. ICE Brent is `B`.

Session CSV columns. `product,date`. Include all exchange trade dates through the cutoff, including any date whose prices are missing.

Expiry CSV columns. `product,delivery_month,last_trade_date`. Include consecutive delivery months from the first eligible contract through at least the latest front month. Include the near month of the fixed pair. Use the exchange's product-specific last trading day rather than a generic weekday calendar.

Re-run with a new observation CSV and expanded calendars to update the same output directory. Identical price keys deduplicate and earlier values remain. Conflicting revisions fail before any output is written. Use another output directory for a separate revision study. Keep generated market data and charts in storage allowed by the source agreement.

The program writes four CSVs under `data/`, four PNGs and a self-contained HTML under `charts/`, and prints observed and scheduled session counts. The market tracks use the front contract through its last trading date and then roll on the next session. The fixed comparison uses the same pair throughout and ends eligibility on the earlier expiry.

The nominal price export and chart show each scheduled M1, M2 and M6 leg in USD/bbl using the same contract ranks as the rolling spreads. Each leg remains visible when its own price is observed, even if the corresponding spread is blank.

With CL selected, the pipeline also writes `data/oil_wti_monthly_contract_pairs_2026.csv` and `charts/2026_wti_monthly_contract_pairs.png`. In each trade month it selects the next two delivery months, for example CLG26−CLH26 for January and CLX26−CLZ26 for October. It preserves the scheduled pair and leaves all post-expiry dates blank through month-end. This chart uses the selected CL price basis and source.
