import * as dotenv from 'dotenv'
dotenv.config()

import { Client } from '@notionhq/client';
import { writeFileSync } from 'fs';

const notion = new Client({ auth: process.env.NOTION_API_KEY });
const databaseId = process.argv[2];

(async () => {
    const response = await notion.databases.query({
        database_id: databaseId,
        sorts: [{
            property: '评价日期',
            direction: 'ascending',
        }]
    });
    let reviews = [];
    for (const page of response.results) {
        let notionUrl = page.public_url;
        let title = page.properties.名称.title[0].plain_text;
        let doubanUrl = page.properties.豆瓣.url;
        let ratingDate = page.properties.评价日期.date?.start;
        let rating = page.properties.评价.select?.name;
        console.log(`${title}, ${ratingDate}, ${rating}`);
        reviews.push({
            "notion_url": notionUrl,
            "title": title,
            "douban_url": doubanUrl,
            "rating_date": ratingDate,
            "rating": rating
        });
    }
    writeFileSync('reviews/book.json', JSON.stringify(reviews, null, 4));
})();
