import os
import time
import argparse
import duckdb
import requests
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Iterable, Optional
from dotenv import load_dotenv

load_dotenv()

DOUBAN_COOKIE = os.getenv("DOUBAN_COOKIE")
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"


def rate_on_douban(
    media_type: str, douban_id: str, rating_1_to_5: int, comment: str, share: bool
) -> bool:
    origin = f"https://{media_type}.douban.com"
    rate_url = f"{origin}/j/subject/{douban_id}/interest"
    referer_url = f"{origin}/subject/{douban_id}/"
    headers = {
        "Cookie": DOUBAN_COOKIE,
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": origin,
        "Referer": referer_url,
        "User-Agent": USER_AGENT,
        "X-Requested-With": "XMLHttpRequest",
    }
    form_data = {
        "ck": "iGF7",
        "interest": "collect",
        "rating": f"{rating_1_to_5}",
        "foldcollect": "F",
        "tags": "",
        "comment": comment,
        "share-shuo": "douban" if share else "",
    }
    resp = requests.post(
        rate_url,
        headers=headers,
        data=form_data,
    )
    return resp.ok


@dataclass
class Review:
    name: str
    douban_id: str
    latest_rating_date: date
    latest_rating: str
    latest_rating_score: int  # from -2 to +2
    rating_merged: str
    public_url: str


SQL_GET_RATED = r"""
SELECT
    any_value(name) AS name,
    regexp_extract(douban_url, 'subject/(\d+)', 1) AS douban_id,
    first(rating_date ORDER BY rating_date DESC) AS latest_rating_date,
    first(rating ORDER BY rating_date DESC) AS latest_rating,
    first(rating_score ORDER BY rating_date DESC) AS latest_rating_score,
    string_agg(
        strftime(rating_date, '%Y-%m-%d') || ' ' || rating, '／'
        ORDER BY rating_date DESC
    ) as rating_merged,
    first(public_url ORDER BY rating_date DESC) AS public_url
FROM reviews
WHERE douban_url IS NOT NULL AND rating_date IS NOT NULL
GROUP BY douban_url
ORDER BY latest_rating_date;
"""


def load_reviews(media_type: str) -> Iterable[Review]:
    json_file = f"reviews/{media_type}.json"
    duckdb.sql(f"CREATE TABLE reviews AS SELECT * FROM read_json_auto('{json_file}')")
    return map(lambda r: Review(*r), duckdb.sql(SQL_GET_RATED).fetchall())


def parse_date(user_given_date: Optional[str], default: date) -> date:
    if user_given_date:
        if user_given_date == "today":
            return date.today()
        elif user_given_date == "yesterday":
            return date.today() - timedelta(days=1)
        else:
            return date.fromisoformat(user_given_date)
    return default


def main():
    parser = argparse.ArgumentParser(
        prog=os.path.basename(__file__),
        description="Sync reviews to Douban",
    )
    parser.add_argument("media_type", choices=["book", "movie", "music"])
    parser.add_argument(
        "--start-date", help="start date, e.g. 2021-01-01, today, yesterday"
    )
    parser.add_argument(
        "--end-date", help="end date, e.g. 2021-12-31, today, yesterday"
    )
    parser.add_argument(
        "--no-share", action="store_true", help="do not share to Douban activity"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="do not send request, just print"
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=1.0,
        help="seconds to sleep between each request, default 1.0",
    )
    args = parser.parse_args()

    start_date = parse_date(args.start_date, default=date(1970, 1, 1))
    end_date = parse_date(args.end_date, default=date.today())

    for review in load_reviews(args.media_type):
        if not start_date <= review.latest_rating_date <= end_date:
            continue

        douban_rating = review.latest_rating_score + 3  # douban rating is from 1 to 5
        print(
            review.name,
            review.douban_id,
            review.rating_merged,
            douban_rating,
            sep=", ",
            end="...",
        )
        if args.dry_run:
            print("DRY RUN")
            continue

        if rate_on_douban(
            args.media_type,
            review.douban_id,
            douban_rating,
            review.rating_merged,
            not args.no_share,
        ):
            print("OK")
        else:
            print("FAILED")

        time.sleep(args.sleep)


if __name__ == "__main__":
    main()
