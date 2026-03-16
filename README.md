# Recipe Box

This is a fork of [lcordier/recipe_box](https://github.com/lcordier/recipe_box) modified to
directly upload files to my Wiki.js instance, and create recipe pages.

## Installation

```bash
uv tool install recipe-box-for-wikijs
```

## Usage

```bash
recipe_box [options] <list-of-links>
```

Available options:

```bash
-l : List all available sites
-w : Enable wild mode. This tries to scrape from unsupported sites.
-v : More verbose output.
```

## Config

The config file is read from `.config/recipe_box/recipe_box.json`. Here's an example config file.

```json
{
  "recipe_box": "~/Documents/recipe_box",
  "wiki_url": "https://wiki.example.com",
  "wiki_api_key": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "custom_css_file": "~/.config/recipe_box/custom.css",
  "tags": ["public", "cooking", "food", "recipe"],
  "image_dir_path": "/images/recipe"
}
```

## Acknowledgement

- The [`recipe-scrapers`](https://github.com/hhursev/recipe-scrapers) project, without which this project would not exist.
