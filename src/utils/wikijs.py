import requests
import mimetypes
import truststore
from pathlib import Path

truststore.inject_into_ssl()


def upload_image_to_wiki(config, image_path):
    """Upload the image to WikiJS."""
    headers = {"Authorization": f"Bearer {config['wiki_api_key']}"}
    with open(image_path, "rb") as f:
        files = (
            (
                "mediaUpload",
                (None, f'{{"folderId":{config["folder_id"]}}}'),
            ),
            (
                "mediaUpload",
                (
                    image_path.name,
                    f,
                    mimetypes.guess_file_type(image_path)[0] or "application/octet-stream",
                ),
            ),
        )
        upload = requests.post(f"{config['wiki_url']}/u", headers=headers, files=files)
        upload.raise_for_status()
        print("Image uploaded.")


def create_markdown_page_in_wiki(config, markdown_path, page_title):
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
    with open(Path(config["custom_css_file"]).expanduser(), "r") as c:
        payload = {
            "query": create_mutation,
            "variables": {
                "content": markdown_content,
                "path": f"/recipes/{markdown_path.stem}",
                "title": page_title,
                "tags": config["tags"],
                "css": c.read(),
            },
        }

    res = requests.post(
        f"{config['wiki_url']}/graphql",
        headers={
            "Authorization": f"Bearer {config['wiki_api_key']}",
            "Content-Type": "application/json",
        },
        json=payload,
    )
    res.raise_for_status()
    result = res.json()["data"]["pages"]["create"]["responseResult"]
    if not result["succeeded"]:
        print("Error: ", result["message"])
    else:
        id = res.json()["data"]["pages"]["create"]["page"]["id"]
        page_path = res.json()["data"]["pages"]["create"]["page"]["path"]
        print(
            f"Page created with ID {id} at the following path.\n  {config['wiki_url']}/en/{page_path}"
        )
