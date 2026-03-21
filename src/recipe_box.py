#!/usr/bin/env python3

# Scrape a recipe, convert it to Markdown and store it in Wiki.js

import argparse
import json
import os
import sys
from recipe_scrapers import scrape_html, WebsiteNotImplementedError, SCRAPERS

from utils.fileio import ensure_directory_exists
from utils.scraper import process_recipe


ROOT = "~/.config/recipe_box/"


def main() -> None:
    """Console script entry point."""
    parser = argparse.ArgumentParser()
    parser.add_argument("url", metavar="URL", type=str, nargs="*", default="", help="recipe url")
    parser.add_argument(
        "-l", dest="list", action="store_true", default=False, help="list all available sites"
    )
    parser.add_argument(
        "-w",
        dest="wild_mode",
        action="store_true",
        default=False,
        help="try scraping 'unknown' site using wild-mode (some editing of the recipe might be required)",
    )
    parser.add_argument(
        "-v", dest="verbose", action="store_true", default=False, help="verbose output"
    )
    args = parser.parse_args()

    if args.list:
        for host in sorted(SCRAPERS):
            print(host)
        sys.exit()

    wild_mode = args.wild_mode
    verbose = args.verbose

    config_path = ensure_directory_exists(os.path.join(ROOT, "recipe_box.json"), file=True)
    if not os.path.exists(config_path):
        config = {"recipe_box": "~/recipe_box/"}
        with open(config_path, "w") as f:
            json.dump(config, f, indent=4)
    else:
        with open(config_path, "r") as f:
            config = json.load(f)

    for url in args.url:
        if url:
            try:
                scraper = scrape_html(html=None, org_url=url, wild_mode=wild_mode, online=True)
            except WebsiteNotImplementedError:
                print("No scraper defined for {url}".format(url=url))
                print("Try using the -w [wild-mode] option, your mileage may vary.")
                print("")
                print(
                    "It is recommended you add it to recipe-scrapers site, that way everybody gains from the effort."
                )
                print(
                    "https://github.com/hhursev/recipe-scrapers#if-you-want-a-scraper-for-a-new-site-added"
                )
            else:
                process_recipe(config, scraper, url, verbose)


if __name__ == "__main__":
    main()
