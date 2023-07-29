# Notion-Douban Sync

用来把 Notion 数据库的书籍、电影评价同步到豆瓣。

## 用法

### 准备环境

```sh
git clone https://github.com/stdrc/notion-douban-sync.git
cd notion-douban-sync

# 安装 Node 依赖
npm install

# 安装 Python 依赖
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

### 准备 Notion API 和豆瓣 Cookie

先摆了，可以网上搜索如何获得。获得后，拷贝 `.env.example` 为 `.env`，填入到对应项。

### 从 Notion 数据库获取评价数据

```sh
node get_notion_reviews.js movie <database_id>
```

这里 `movie` 可以改成 `book`。脚本假设数据库 schema 和 [我的](https://stdrc.notion.site/d0f220b2c9a741849b6991de22151ae3) 一致，如果不一致，可以自行修改脚本或者用其它方式导出为兼容的 JSON 文件。

JSON 文件的形如：

```json
[
    {
        "name": "死亡诗社",
        "douban_url": "https://movie.douban.com/subject/1291548/",
        "rating_date": "2023-07-23",
        "rating": "👍 值得一看",
        "rating_score": 1,
        "public_url": "https://stdrc.notion.site/1d7942b7347546fe928ed38131b6b6c7"
    }
]
```

其中 `rating` 可以是任何字符串，后面的脚本是依据 `rating_score` 在豆瓣评分；`rating_score` 采用 -2 到 +2 的评价方式，-2 表示极差，-1 表示较差，0 表示无感，1 表示较好，2 表示极好；`public_url` 是可以公开访问的影评/书评链接，目前没用到，可以留空。

### 同步评价到豆瓣

```sh
python sync_to_douban.py --dry-run movie
```

注意这里加了 `--dry-run` 表示只打印到控制台，不真的请求豆瓣 API，去掉会真的往豆瓣同步。可以通过 `python sync_to_douban.py --help` 查看更多用法，比如限制只同步一定时间范围内的数据：

```sh
python sync_to_douban.py \
    --dry-run \
    --start-date 2022-01-01 \
    --end-date 2022-12-31 \
    movie
```

如果只需要同步今天刚评价的内容：

```sh
python sync_to_douban.py \
    --dry-run \
    --start-date today \
    movie
```
