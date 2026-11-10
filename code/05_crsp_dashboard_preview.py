"""Build a dashboard preview from the professor's licensed CRSP ZIP.

Run from the repository with:
    python3 code/05_crsp_dashboard_preview.py /path/to/ant728_request.zip

Stream the archive without extracting it. Write one row per proof-of-concept
bank, with the original FDIC measures and aggregate CRSP event statistics.
This is optional and does not change run_all.py or its yfinance output.
"""

import argparse
import csv
import io
import math
import re
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path, PurePosixPath
from zipfile import BadZipFile, ZipFile

from config import CALL_REPORT_DATE, ESTIMATION_WINDOW, EVENT_DAY0, EVENT_WINDOW, OUTPUTS

BASE_FIELDS = (
    "ticker", "entity_name", "entity_type", "entity_id", "call_report_date", "n_banks",
    "n_banks_missing_uninsured", "total_assets_bn", "uninsured_dep_share",
    "htm_unrealized_loss_bn", "afs_unrealized_loss_bn", "htm_loss_to_equity",
    "sec_loss_to_equity", "htm_share_of_securities",
)
RESULT_FIELDS = ("beta", "est_obs", "car_0_2", "car_0_2_mktadj", "car_note")
MIN_EST_OBS = 150  # Same threshold as the yfinance proof of concept.
EXPECTED_EVENT_DAYS = [date(2023, 3, 9), date(2023, 3, 10), date(2023, 3, 13)]


def csv_rows(stream, required, label):
    reader = csv.DictReader(stream, strict=True)
    fields = reader.fieldnames or []
    if not set(required) <= set(fields) or len(set(fields)) != len(fields):
        raise ValueError(f"{label} has missing or repeated column names.")
    for row in reader:
        if None in row or any(value is None for value in row.values()):
            raise ValueError(f"{label} has an incomplete CSV record.")
        yield row


def archive_rows(archive, filename, required):
    matches = [name for name in archive.namelist() if PurePosixPath(name).name == filename]
    if len(matches) != 1:
        raise ValueError(f"The ZIP must contain exactly one {filename}.")
    with io.TextIOWrapper(archive.open(matches[0]), encoding="utf-8-sig", newline="") as stream:
        yield from csv_rows(stream, required, filename)


def return_value(value):
    if not value.strip():
        return None
    try:
        result = float(value)
    except ValueError:
        raise ValueError("Invalid return value in the CRSP archive.") from None
    if not math.isfinite(result) or result < -1:
        raise ValueError("Invalid return value in the CRSP archive.")
    return result


def market_windows(archive, report_date):
    market = {}
    for row in archive_rows(archive, "crsp_market_vwretd.csv", ("date", "vwretd")):
        day = date.fromisoformat(row["date"])
        if day in market:
            raise ValueError("Repeated trading day in the CRSP market calendar.")
        market[day] = return_value(row["vwretd"])
    days = sorted(market)
    day0 = date.fromisoformat(EVENT_DAY0)
    if day0 not in market:
        raise ValueError("The CRSP market calendar does not include event day zero.")
    p0 = days.index(day0)
    est_start, est_end = (p0 + offset for offset in ESTIMATION_WINDOW)
    event_start, event_end = (p0 + offset for offset in EVENT_WINDOW)
    if est_start < 0 or event_start < 0 or event_end >= len(days):
        raise ValueError("The CRSP market calendar does not cover both windows.")
    estimate = days[est_start:est_end + 1]
    event = days[event_start:event_end + 1]
    if event != EXPECTED_EVENT_DAYS:
        raise ValueError("The CRSP market calendar must contain March 9, 10, and 13 as the event window.")
    if any(market[day] is None for day in event):
        raise ValueError("A required event day is missing the CRSP market return.")
    anchors = (max(day for day in days if day <= report_date), day0)
    return market, estimate, event, anchors


def name_key(value):
    return re.sub(r"[^A-Z0-9]", "", value.upper())


def candidates(archive, baseline):
    by_rssd, by_name, seen_companies = {}, defaultdict(set), set()
    for row in archive_rows(archive, "crsp_permcos.csv", ("rssd_id", "permco", "name")):
        rssd, company, issuer = row["rssd_id"], row["permco"], name_key(row["name"])
        if not rssd.isdecimal() or not company.isdecimal() or not issuer:
            raise ValueError("The CRSP request has an incomplete issuer link.")
        if rssd in by_rssd or company in seen_companies:
            raise ValueError("The CRSP request is not one-to-one between RSSD and company.")
        by_rssd[rssd] = company
        by_name[issuer].add(company)
        seen_companies.add(company)

    potential = {}
    for bank in baseline:
        # A direct bank's baseline entity_id is an FDIC certificate, not an RSSD.
        company = by_rssd.get(bank["entity_id"]) if bank["entity_type"] == "hc" else None
        if company:
            potential[bank["ticker"]] = ("RSSD", {company})
        else:
            potential[bank["ticker"]] = ("dated ticker", by_name[name_key(bank["entity_name"])])
    return potential


def stock_rows(archive, potential, required_days, anchors):
    target_companies = set().union(*(companies for _, companies in potential.values()))
    needed = {day.isoformat() for day in required_days}
    anchor_days = {day.isoformat() for day in anchors}
    hits, securities, daily = defaultdict(set), defaultdict(set), defaultdict(dict)
    fields = ("permco", "permno", "date", "ticker", "shrcd", "ret", "dlstdt", "dlstcd", "dlret")
    for row in archive_rows(archive, "crsp_daily_2022_2023.csv", fields):
        day, ticker = row["date"], row["ticker"].upper()
        company, security = row["permco"], row["permno"]
        if row["shrcd"] == "11" and day in anchor_days and ticker in potential:
            hits[ticker, day].add((company, security))
        if company not in target_companies:
            continue
        securities[company].add(security)
        if row["shrcd"] != "11" or day not in needed:
            continue
        series = daily[company, security]
        if day in series:
            raise ValueError("Repeated daily observation for a selected CRSP security.")
        series[day] = tuple(row[field] for field in ("ret", "dlstdt", "dlstcd", "dlret"))

    matches = {}
    for ticker, (method, companies) in potential.items():
        first, last = (hits[ticker, day.isoformat()] for day in anchors)
        # Both dates must identify the same single ordinary common share.
        if first == last and len(first) == 1:
            company, security = next(iter(first))
            if company in companies and securities[company] == {security}:
                matches[ticker] = (method, (company, security))
    if len({key for _, key in matches.values()}) != len(matches):
        raise ValueError("Multiple baseline tickers resolve to the same CRSP security.")
    return matches, daily


def delisting_rows(archive, matches):
    keys = {key for _, key in matches.values()}
    result, seen = {}, set()
    fields = ("permco", "permno", "dlstdt", "dlstcd", "dlret")
    for row in archive_rows(archive, "crsp_delistings.csv", fields):
        key = (row["permco"], row["permno"])
        if key not in keys:
            continue
        if key in seen:
            raise ValueError("Repeated delisting record for a selected CRSP security.")
        seen.add(key)
        if row["dlstcd"] != "100":  # Code 100 indicates a still-active listing.
            result[key] = (
                date.fromisoformat(row["dlstdt"]), row["dlstcd"], return_value(row["dlret"])
            )
    if keys != seen:
        raise ValueError("A selected security is missing its CRSP delisting record.")
    return result


def holding_return(day, daily, delisting):
    """Get a usable daily return and the reason if one cannot be computed."""
    record = daily.get(day.isoformat())
    if delisting and day > delisting[0]:
        return None, "after delisting (no usable daily return)"
    if record is None:
        return None, "no daily row"
    ret, inline_day, inline_code, inline_ret = record
    if inline_code and inline_code != "100":
        inline = (date.fromisoformat(inline_day), inline_code, return_value(inline_ret))
        if inline != delisting or inline[0] != day:
            raise ValueError("The CRSP daily and delisting files disagree.")
    stock_return = return_value(ret)
    if delisting and day == delisting[0]:
        if delisting[2] is None:
            return None, "CRSP reports a delisting but no delisting return"
        if stock_return is not None:
            stock_return = (1 + stock_return) * (1 + delisting[2]) - 1
    return (None, "no daily stock return") if stock_return is None else (stock_return, "")


def event_result(ticker, matches, daily, delistings, market, estimate, event):
    out = dict.fromkeys(RESULT_FIELDS, "")
    if ticker not in matches:
        out["car_note"] = "No verified CRSP link for the listed entity."
        return out
    _, key = matches[ticker]
    series, delisting = daily[key], delistings.get(key)
    event_returns, gaps = [], []
    for day in event:
        value, reason = holding_return(day, series, delisting)
        if value is None:
            gaps.append(f"{day}: {reason}")
        else:
            event_returns.append((market[day], value))
    if gaps:
        out["car_note"] = "Incomplete CRSP event window; " + "; ".join(gaps) + "."
        return out

    sample = []
    for day in estimate:
        value, _ = holding_return(day, series, delisting)
        if market[day] is not None and value is not None:
            sample.append((market[day], value))
    n = len(sample)
    if n < MIN_EST_OBS:
        out["car_note"] = f"Insufficient CRSP estimation observations ({n}; need {MIN_EST_OBS})."
        return out
    x_mean = math.fsum(x for x, _ in sample) / n
    y_mean = math.fsum(y for _, y in sample) / n
    x_variation = math.fsum((x - x_mean) ** 2 for x, _ in sample)
    if not x_variation:
        out["car_note"] = "No variation in the CRSP market estimation returns."
        return out
    beta = math.fsum((x - x_mean) * (y - y_mean) for x, y in sample) / x_variation
    alpha = y_mean - beta * x_mean
    out.update(
        beta=f"{beta:.4f}",
        est_obs=n,
        car_0_2=f"{math.fsum(y - (alpha + beta * x) for x, y in event_returns):.4f}",
        car_0_2_mktadj=f"{math.fsum(y - x for x, y in event_returns):.4f}",
    )
    return out


def build_preview(zip_path):
    report_date = datetime.strptime(CALL_REPORT_DATE, "%Y%m%d").date()
    with (OUTPUTS / "poc_final_rows.csv").open(encoding="utf-8-sig", newline="") as stream:
        baseline = list(csv_rows(stream, BASE_FIELDS, "Dashboard baseline"))
    if not baseline or len({bank["ticker"] for bank in baseline}) != len(baseline):
        raise ValueError("The dashboard baseline must contain unique bank tickers.")
    if any(
        bank["entity_type"] not in {"hc", "bank"}
        or not bank["entity_id"].isdecimal()
        or not bank["ticker"] or not bank["entity_name"]
        or bank["call_report_date"] != report_date.isoformat()
        for bank in baseline
    ):
        raise ValueError("The dashboard baseline has an incomplete issuer or wrong report quarter.")

    with ZipFile(zip_path) as archive:
        market, estimate, event, anchors = market_windows(archive, report_date)
        potential = candidates(archive, baseline)
        matches, daily = stock_rows(archive, potential, estimate + event, anchors)
        delistings = delisting_rows(archive, matches)
        rows = []
        for bank in baseline:
            row = {field: bank[field] for field in BASE_FIELDS}
            row.update(event_result(
                bank["ticker"], matches, daily, delistings, market, estimate, event,
            ))
            rows.append(row)

    output = OUTPUTS / "poc_crsp_rows.csv"
    with output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=BASE_FIELDS + RESULT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote outputs/{output.name}: {len(rows)} banks; "
          f"{sum(bool(row['car_0_2']) for row in rows)} with complete CRSP event CARs.")
    for method in ("RSSD", "dated ticker"):
        tickers = sorted(ticker for ticker, match in matches.items() if match[0] == method)
        print(f"{method} matches: {len(tickers)} ({', '.join(tickers) or 'none'}).")
    for row in rows:
        if row["car_note"]:
            print(f"{row['ticker']}: {row['car_note']}")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("archive", type=Path, help="Local licensed CRSP ZIP; kept outside the repo")
    args = parser.parse_args()
    try:
        build_preview(args.archive)
    except (BadZipFile, OSError, ValueError, csv.Error) as exc:
        parser.exit(1, f"CRSP preview could not be built: {exc}\n")


if __name__ == "__main__":
    main()
