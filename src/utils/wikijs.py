from requests.models import Response
import requests
import mimetypes
import truststore
from pathlib import Path

truststore.inject_into_ssl()


def upload_image_to_wiki(config: dict[str, str], image_path: Path) -> None:
    """Upload the image to WikiJS."""
    headers = {"Authorization": f"Bearer {config['wiki_api_key']}"}
    folder_id = resolve_asset_dir(config)
    with open(image_path, "rb") as f:
        files = (
            (
                "mediaUpload",
                (None, f'{{"folderId":{folder_id}}}'),
            ),
            (
                "mediaUpload",
                (
                    image_path.name,
                    f,
                    mimetypes.guess_type(image_path)[0] or "application/octet-stream",
                ),
            ),
        )
        upload: Response = requests.post(f"{config['wiki_url']}/u", headers=headers, files=files)
        upload.raise_for_status()
        print(
            f"Image uploaded at the following path: \n  {config['wiki_url']}{config['image_dir_path']}/{image_path.name}"
        )


def create_markdown_page_in_wiki(
    config: dict[str, str], markdown_path: Path, page_title: str
) -> None:
    """Upload the markdown as a page in WikiJS."""
    markdown_content = markdown_path.read_text(encoding="utf-8")

    create_mutation = """
    mutation Page ($content:String!,$path:String!,$title:String!,$css:String,$tags:[String]!) {
      pages {
        create (
          content:$content,
          description:"",
          editor:"markdown",
          isPublished:true,
          isPrivate:false,
          locale:"en",
          scriptCss:$css,
          path:$path,
          tags:$tags,
          title:$title
        ) { 
          responseResult {
            succeeded,
            errorCode,
            message
          },
          page {
            id,
            path
          }
        }
      }
    }
    """
    custom_css = ""
    try:
        custom_css_file = Path(config["custom_css_file"]).expanduser()
        with custom_css_file.open("r") as f:
            custom_css = f.read()
    except (KeyError, TypeError):
        pass
    except (FileNotFoundError, PermissionError, IsADirectoryError, OSError, UnicodeDecodeError):
        print("Could not read the custom CSS file.")
        exit(2)

    payload = {
        "query": create_mutation,
        "variables": {
            "content": markdown_content,
            "path": f"/recipes/{markdown_path.stem}",
            "title": page_title,
            "tags": config["tags"],
            "css": custom_css,
        },
    }

    res: Response = requests.post(
        f"{config['wiki_url']}/graphql",
        headers={
            "Authorization": f"Bearer {config['wiki_api_key']}",
            "Content-Type": "application/json",
        },
        json=payload,
    )
    res.raise_for_status()
    result: dict = res.json()["data"]["pages"]["create"]["responseResult"]
    if not result["succeeded"]:
        print("Error: ", result["message"])
    else:
        id: str = res.json()["data"]["pages"]["create"]["page"]["id"]
        page_path: str = res.json()["data"]["pages"]["create"]["page"]["path"]
        print(
            f"Page created with ID {id} at the following path.\n  {config['wiki_url']}/en/{page_path}"
        )


def resolve_asset_dir(config: dict[str, str]) -> int:
    asset_query = """
    query($parent: Int!) {
      assets {
        folders(parentFolderId: $parent) {
          id
          name
        }
      }
    }
    """
    parent = 0

    for part in config["image_dir_path"].strip("/").split("/"):
        payload: dict = {"query": asset_query, "variables": {"parent": parent}}
        res: Response = requests.post(
            f"{config['wiki_url']}/graphql",
            headers={
                "Authorization": f"Bearer {config['wiki_api_key']}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        res.raise_for_status()
        data: dict = res.json()
        try:
            parent: str = next(
                dir["id"] for dir in data["data"]["assets"]["folders"] if dir["name"] == part
            )
        except StopIteration:
            raise SystemExit(f"dir not found: {part}")
    return parent
