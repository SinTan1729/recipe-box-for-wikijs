import os
import httpx
from pathlib import Path
import re
from prompt_toolkit import prompt

from utils.fileio import (
    valid_filename,
    ensure_directory_exists,
)
from utils.wikijs import (
    upload_image_to_wiki,
    create_markdown_page_in_wiki,
)


def process_recipe(config, scraper, url, verbose=False) -> None:
    """Process the recipe at a given URL."""
    recipe_box = ensure_directory_exists(config["recipe_box"])
    media = ensure_directory_exists(os.path.join(config["recipe_box"], "images"))

    print("Make any changes to the detected title if you want and press enter.")
    cleaned_title = re.sub(
        r"[\s\-:|]*recipe(?:\s+(?:ideas?|video|videos|tutorial|tutorials))?\b\s*$",
        "",
        scraper.title(),
        flags=re.I,
    )
    title = prompt("Title: ", default=cleaned_title)

    prefix = title.strip().replace(" ", "-").lower()
    path = os.path.join(recipe_box, prefix + ".md")
    path = valid_filename(path)
    recipe = open(path, "w+")

    image_path = None
    url_getter = httpx.Client(http2=True)
    try:
        image_url = scraper.image()
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
        image = open(filepath, "wb+")
        image.write(response.content)
        image.close()
        if verbose:
            print("Saving {url} -> {path}".format(url=image_url, path=filepath))

    # Make sure to upload the image file inside /images/recipe with the proper name or edit the following
    # lines to suit your needs.
    if filename:
        recipe.write("![{filename}](/images/recipe/{filename})\n".format(filename=filename))
    recipe.write("\n")
    recipe.write("## Information\n")
    recipe.write("Yields: {yields}\n".format(yields=scraper.yields()))
    recipe.write("Total Time: {total_time} minutes\n".format(total_time=scraper.total_time()))
    recipe.write("\n")
    recipe.write("## Ingredients\n")
    for ingredient in scraper.ingredients():
        recipe.write("1. {ingredient}\n".format(ingredient=ingredient))

    recipe.write("\n")
    recipe.write("## Instructions\n")
    for instruction in scraper.instructions().split("\n"):
        instruction = instruction.strip()
        if instruction:
            if instruction[0].isdigit():
                recipe.write("{instruction}\n".format(instruction=instruction))
            else:
                recipe.write("1. {instruction}\n".format(instruction=instruction))

    recipe.write("\n#### URL\n")
    recipe.write("[{url}]({url})\n".format(url=url))

    recipe.close()
    # if verbose:
    print("Saving {url} -> {path}".format(url=url, path=path))
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
