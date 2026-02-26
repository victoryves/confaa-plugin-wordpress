import base64
import requests


def _auth_header(credentials: dict) -> dict[str, str]:
    username = credentials["wp_username"]
    app_password = credentials["wp_app_password"]
    token = base64.b64encode(f"{username}:{app_password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def _wp_url(credentials: dict, path: str) -> str:
    base = credentials["wp_url"].rstrip("/")
    return f"{base}/wp-json/wp/v2/{path}"


def get_or_create_category(name: str, credentials: dict) -> int:
    headers = _auth_header(credentials)
    resp = requests.get(_wp_url(credentials, "categories"), params={"search": name}, headers=headers, timeout=15)
    resp.raise_for_status()
    for cat in resp.json():
        if cat["name"].lower() == name.lower():
            return cat["id"]
    resp = requests.post(_wp_url(credentials, "categories"), json={"name": name}, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.json()["id"]


def upload_image(image_url: str, filename: str, credentials: dict) -> int | None:
    try:
        img_resp = requests.get(image_url, timeout=15)
        img_resp.raise_for_status()
    except Exception:
        return None

    content_type = img_resp.headers.get("Content-Type", "image/jpeg")
    headers = _auth_header(credentials)
    headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    headers["Content-Type"] = content_type

    resp = requests.post(
        _wp_url(credentials, "media"),
        data=img_resp.content,
        headers=headers,
        timeout=30,
    )
    if not resp.ok:
        return None
    return resp.json().get("id")


def create_post(
    title: str,
    content: str,
    category_name: str,
    featured_media_id: int | None,
    credentials: dict,
    status: str = "publish",
    source_url: str = "",
) -> int:
    category_id = get_or_create_category(category_name, credentials)
    headers = _auth_header(credentials)
    headers["Content-Type"] = "application/json"

    payload: dict = {
        "title": title,
        "content": content,
        "status": status,
        "categories": [category_id],
    }
    if featured_media_id:
        payload["featured_media"] = featured_media_id
    if source_url:
        payload["meta"] = {"source_url": source_url}

    resp = requests.post(_wp_url(credentials, "posts"), json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()["id"]
