import * as dotenv from 'dotenv'
dotenv.config()

import { writeFileSync } from 'fs';
import * as path from 'path';
import { Client } from '@notionhq/client';

const notion = new Client({ auth: process.env.NOTION_API_KEY });
const databaseType = process.argv[2];
const databaseId = process.argv[3];

const supportedDatabaseTypes = ['book', 'movie', 'music'];

if (!databaseType || !databaseId || !supportedDatabaseTypes.includes(databaseType)) {
    const self = path.basename(process.argv[1]);
    console.log(`Usage: node ${self} ${supportedDatabaseTypes.join('|')} <database_id>`);
    process.exit(1);
}

const nameProp = '名称';
const doubanUrlProp = '豆瓣';
const ratingDateProp = '评价日期';
const ratingProp = '评价';
const ratingScoreMap = {
    "👏": 2,
    "👍": 1,
    "👌": 0,
    "👎": -1,
    "🖕": -2,
};

(async () => {
    const response = await notion.databases.query({
        database_id: databaseId,
        sorts: [{
            property: ratingDateProp,
            direction: 'ascending',
        }]
    });
    let reviews = [];
    for (const page of response.results) {
        let name = page.properties[nameProp].title[0].plain_text;
        let doubanUrl = page.properties[doubanUrlProp].url;
        let ratingDate = page.properties[ratingDateProp].date?.start || null;
        let rating = page.properties[ratingProp].select?.name || null;
        let ratingScore = rating ? ratingScoreMap[Array.from(rating)[0]] : null;
        let publicUrl = page.public_url.replace(/\/[^\/]*-([0-9a-f]{32})$/, '/$1');

        console.log(`${name}, ${ratingDate}, ${rating}, ${ratingScore}`);
        reviews.push({
            "name": name,
            "douban_url": doubanUrl,
            "rating_date": ratingDate,
            "rating": rating,
            "rating_score": ratingScore,
            "public_url": publicUrl,
        });
    }
    writeFileSync(`reviews/${databaseType}.json`, JSON.stringify(reviews, null, 4));
})();
