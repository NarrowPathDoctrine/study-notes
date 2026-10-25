#!/usr/bin/env python3
"""Publish due teaching drafts and build the public PDF-backed catalog.
Uses the GitHub Actions GITHUB_TOKEN; no credentials are stored on the website.
"""
from __future__ import annotations
import datetime as dt
import json
import os
import re
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

UK = ZoneInfo("Europe/London")
REPO = os.environ.get("GITHUB_REPOSITORY", "NarrowPathDoctrine/study-notes")
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN", "")
OUTPUT = Path(__file__).resolve().parents[1] / "site" / "data" / "studies.json"
FIELD = re.compile(r"^\s*(youtube|publish\s*\(\s*uk\s*\)|topic|scripture|description)\s*:\s*(.*?)\s*$", re.I)
VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")

def api(method: str, endpoint: str, payload: dict | None = None):
    if not TOKEN:
        raise RuntimeError("GitHub Actions token is required")
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = Request(
        "https://api.github.com/repos/" + REPO + "/" + endpoint,
        data=body,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer " + TOKEN,
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "Narrow-Path-Study-Library",
            **({"Content-Type": "application/json"} if body else {}),
        },
    )
    with urlopen(req, timeout=25) as response:
        return json.load(response)

def get_releases():
    result = []
    for page in range(1, 102):
        batch = api("GET", "releases?per_page=100&page=" + str(page))
        result.extend(batch)
        if len(batch) < 100:
            return result
    raise RuntimeError("Release count exceeds supported limit")

def fields(body: str):
    output = {}
    for line in (body or "").splitlines():
        match = FIELD.match(line)
        if match:
            output[re.sub(r"\s+", " ", match.group(1).strip().lower())] = match.group(2).strip()
    return output

def video_id(url: str):
    try:
        parsed = urlparse(url)
        if parsed.scheme != "https":
            return None
        host = (parsed.hostname or "").lower()
        if host in ("youtu.be", "www.youtu.be"):
            candidate = parsed.path.strip("/").split("/")[0]
        elif host in ("youtube.com", "www.youtube.com", "m.youtube.com"):
            parts = [p for p in parsed.path.split("/") if p]
            if parsed.path.rstrip("/") == "/watch":
                candidate = parse_qs(parsed.query).get("v", [""])[0]
            elif len(parts) >= 2 and parts[0] in ("shorts", "live", "embed"):
                candidate = parts[1]
            else:
                return None
        else:
            return None
        return candidate if VIDEO_ID.fullmatch(candidate) else None
    except (TypeError, ValueError):
        return None

def scheduled_for(data: dict):
    try:
        return dt.datetime.strptime(data.get("publish (uk)", ""), "%Y-%m-%d %H:%M").replace(tzinfo=UK)
    except ValueError:
        return None

def attached_pdf(release: dict):
    for asset in release.get("assets", []):
        if (asset.get("name", "").lower().endswith(".pdf")
                and asset.get("state", "uploaded") == "uploaded"
                and asset.get("browser_download_url", "").startswith("https://")):
            return asset
    return None

def youtube_title(vid: str):
    endpoint = "https://www.youtube.com/oembed?" + urlencode({
        "url": "https://www.youtube.com/watch?v=" + vid,
        "format": "json",
    })
    req = Request(endpoint, headers={"User-Agent": "Mozilla/5.0 (compatible; StudyNotesPublisher/1.0)"})
    try:
        with urlopen(req, timeout=16) as response:
            info = json.load(response)
        title = info.get("title")
        return title.strip()[:300] if isinstance(title, str) and title.strip() else None
    except (HTTPError, URLError, TimeoutError, ValueError, OSError) as exc:
        print("YouTube metadata unavailable: " + str(exc))
        return None

def publish_due(releases: list[dict], now: dt.datetime):
    for release in releases:
        if not release.get("draft"):
            continue
        data = fields(release.get("body", ""))
        when = scheduled_for(data)
        vid = video_id(data.get("youtube", ""))
        asset = attached_pdf(release)
        tag = release.get("tag_name", "(untagged)")
        if not when or not vid or not asset:
            print("Incomplete draft, left unpublished: " + tag)
            continue
        if now < when:
            print("Future draft: " + tag)
            continue
        title = youtube_title(vid)
        if not title:
            print("Video still unavailable: " + tag)
            continue
        print("Publishing draft: " + tag)
        changed = api("PATCH", "releases/" + str(release["id"]), {
            "draft": False, "name": title, "prerelease": False
        })
        release.update(changed)
        time.sleep(0.2)
    return releases

def public_catalog(releases: list[dict]):
    studies = []
    for release in releases:
        if release.get("draft") or release.get("prerelease"):
            continue
        data = fields(release.get("body", ""))
        vid = video_id(data.get("youtube", ""))
        pdf = attached_pdf(release)
        published = release.get("published_at")
        if not vid or not pdf or not published:
            continue
        try:
            date = dt.datetime.fromisoformat(published.replace("Z", "+00:00"))
        except (TypeError, ValueError):
            continue
        studies.append({
            "id": str(release.get("tag_name", "")),
            "title": str(release.get("name") or release.get("tag_name") or "Teaching"),
            "video_id": vid,
            "pdf_url": pdf["browser_download_url"],
            "published_at": published,
            "year": date.astimezone(UK).year,
            "topic": data.get("topic", "Biblical teaching")[:90],
            "scripture": data.get("scripture", "")[:140],
            "description": data.get("description", "")[:500],
        })
    studies.sort(key=lambda item: item["published_at"], reverse=True)
    return {
        "generated_at": studies[0]["published_at"] if studies else None,
        "studies": studies,
    }

def main():
    now = dt.datetime.now(UK)
    print("Checking releases at " + now.isoformat())
    releases = get_releases()
    updated = publish_due(releases, now)
    result = public_catalog(updated)
    new_text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != new_text:
        OUTPUT.write_text(new_text, encoding="utf-8")
        print("Published teaching count: " + str(len(result["studies"])))
    else:
        print("No change to public catalog")

if __name__ == "__main__":
    main()
