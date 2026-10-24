import os
import re
from pathlib import Path

import httpx
from prompt_toolkit import prompt
from recipe_scrapers import AbstractScraper

from utils.fileio import (
    ensure_directory_exists,
    valid_filename,
)
from utils.wikijs import (
    create_markdown_page_in_wiki,
    upload_image_to_wiki,
)


def process_recipe(
    config: dict[str, str], scraper: AbstractScraper, url: str, verbose: bool = False
) -> None:
    """Process the recipe at a given URL."""
    recipe_box = ensure_directory_exists(config["recipe_box"])
    media = ensure_directory_exists(os.path.join(config["recipe_box"], "images"))

    print("Make any changes to the detected title if you want and press enter.")
    cleaned_title = re.sub(
        r"[\s\-:|]*recipe(?:\s+(?:ideas?|video|videos|tutorial|tutorials))?\b\s*$",
        "",
        scraper.title(),
        flags=re.IGNORECASE,
    )
    title = prompt("Title: ", default=cleaned_title)

    recipe_name = title.strip().replace(" ", "-").lower()
    while "--" in recipe_name:
        recipe_name = recipe_name.replace("--", "-")
    path = os.path.join(recipe_box, recipe_name + ".md")
    path = valid_filename(path)
    with open(path, "w+") as recipe:
        url_getter = httpx.Client(http2=True)
        try:
            image_url: str = scraper.image()
            response = url_getter.get(image_url)
        except httpx.RequestError:
            filename = None
        else:
            # Not sure about image urls without filename extensions, might need python-magic.
            # Also, os.path.splitext(url), probably not a good idea. ;)
            filename = (
                os.path.splitext(os.path.basename(path))[0] + os.path.splitext(scraper.image())[1]
            )
            filepath = os.path.join(media, filename)
            image_path = Path(filepath)
            with open(filepath, "wb+") as image:
                image.write(response.content)
            if verbose:
                print(f"Saving {image_url} -> {filepath}")

        # Make sure to upload the image file inside /images/recipe with the proper name or edit the following
        # lines to suit your needs.
        if filename:
            recipe.write(f"![{filename}](/images/recipe/{filename})\n")
        recipe.write("\n")
        recipe.write("## Information\n")
        recipe.write(f"Yields: {scraper.yields()}\n")
        recipe.write(f"Total Time: {scraper.total_time()} minutes\n")
        recipe.write("\n")
        recipe.write("## Ingredients\n")
        recipe.writelines(f"1. {ingredient}\n" for ingredient in scraper.ingredients())

        recipe.write("\n")
        recipe.write("## Instructions\n")
        for instruction in scraper.instructions().split("\n"):
            instruction = instruction.strip()
            if instruction:
                if instruction[0].isdigit():
                    recipe.write(f"{instruction}\n")
                else:
                    recipe.write(f"1. {instruction}\n")

        recipe.write("\n#### URL\n")
        recipe.write(f"[{url}]({url})\n")

    # if verbose:
    print(f"Saving {url} -> {path}")
    answer = (
        input(
            "Please take a look at the files generated. Do you want to upload these to WikiJS? [y/N]: "
        )
        .strip()
        .lower()
    )
    if answer == "y":
        upload_image_to_wiki(config, image_path)
        create_markdown_page_in_wiki(config, Path(path), title.removesuffix(" recipe"))
    else:
        print("Not uploading.")
