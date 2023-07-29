import time
import duckdb
import requests
import os
from dotenv_vault import load_dotenv

load_dotenv()

douban_cookie = os.getenv("DOUBAN_COOKIE")
origin = "https://book.douban.com"
rate_url_tpl = "{origin}/j/subject/{}/interest"
referer_url_tpl = "{origin}/subject/{}/"


def rate(douban_id: str, rating: int, comment: str) -> bool:
    rate_url = rate_url_tpl.format(douban_id)
    referer_url = referer_url_tpl.format(douban_id)
    headers = {
        "Cookie": douban_cookie,
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": origin,
        "Referer": referer_url,
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; Redmi K30 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.210 Mobile Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
    }
    resp = requests.post(
        rate_url,
        headers=headers,
        data={
            "ck": "iGF7",
            "interest": "collect",
            "rating": f"{rating}",
            "foldcollect": "F",
            "tags": "",
            "comment": comment,
            "share-shuo": "douban",
        },
    )
    return resp.ok


duckdb.read_json("reviews/book.json")

sql = r"""
select
    regexp_extract(douban_url, 'subject/(\d+)', 1) as douban_id,
    any_value(title) as title,
    first(rating order by rating_date desc) as rating,
    string_agg(rating_date::varchar || ' ' || rating, '｜' order by rating_date desc) as comment
from "reviews/book.json"
where douban_url is not null and rating_date is not null
group by douban_url;
"""

rating_map = {
    "👏": 5,
    "👍": 4,
    "👌": 3,
    "👎": 2,
    "🖕": 1,
}

reviews = duckdb.sql(sql).fetchall()
for review in reviews:
    douban_id = review[0]
    title = review[1]
    rating = rating_map[review[2][0]]
    comment = review[3]
    print(douban_id, title, rating, comment)
    if not rate(douban_id, rating, comment):
        print("Failed")
    time.sleep(1)
