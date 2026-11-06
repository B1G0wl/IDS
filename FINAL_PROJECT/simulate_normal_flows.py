import fs from "fs";
import https from "https";

const SAVE_DIR = "./images_2024_04";
if (!fs.existsSync(SAVE_DIR)) fs.mkdirSync(SAVE_DIR, { recursive: true });

async function getImageUrls() {
  const sitemapUrl = "https://programmingfever.com/wp-sitemap-media-1.xml";
  const xml = await fetch(sitemapUrl).then(r => r.text());

  const regex = /https:\/\/programmingfever\.com\/wp-content\/uploads\/2024\/04\/[^<]+?\.(?:jpg|jpeg|png|webp)/g;
  const urls = xml.match(regex) || [];
  console.log("Found", urls.length, "images");
  return urls;
}

function download(url) {
  return new Promise((resolve, reject) => {
    const filename = `${SAVE_DIR}/${url.split("/").pop()}`;
    const file = fs.createWriteStream(filename);
    https.get(url, res => {
      if (res.statusCode !== 200) return reject(`Failed: ${url}`);
      res.pipe(file);
      file.on("finish", () => file.close(() => resolve(filename)));
    }).on("error", reject);
  });
}

(async () => {
  const urls = await getImageUrls();
  for (const url of urls) {
    console.log("Downloading", url);
    try { await download(url); } 
    catch (e) { console.error(e); }
  }
  console.log("✅ Done");
})();
