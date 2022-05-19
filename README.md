# News Archive Scraper

Scraper to download historic news articles from online newspaper archives of the German newspapers "Der Spiegel", "Die Welt", "Die Zeit", "Der Tagesspiegel".

**Disclaimer:** Notice that scraping news articles and building databases like this tool does is not in any case legal. The scraper was developed for research only. See more information about the legal situation in this [article from "Forschung & Lehre"](https://www.forschung-und-lehre.de/recht/grenzen-des-web-scrapings-2421) (in German).

## Getting Started
1) Setup Scrapy according to the [official guide](https://docs.scrapy.org/en/latest/intro/install.html).
2) Clone this repository.
3) Run the scraper locally with e.g. ```scrapy crawl welt``` resp. ```spiegel```, ```zeit``` or ```tagesspiegel```.

## How it Works

The scraping procedure depends on the newspaper. Still, the archives are usually structured as follows:
- Per year there is an overview page, where all published magazins are listed.
- Per magazin there is an overview page, where all articles are listed.

This hierarchy of pages is parsed as follows:

1) Get all magazin urls of year X.
2) Get all article urls of the magazins.
3) Extract the relevant information of the articles and store it in a database.

During step 1 & 2 magazins resp. article urls are checked whether they have not yet been scraped. This way, restarting the scraper does not result in multiple copies of the articles in the database.

In the third step, a distinction is made between articles behind a paywall and freely accessible articles. For paid articles, a previously set premium cookie is loaded to enable full-text access.
