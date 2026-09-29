#!/usr/bin/env python3

import os
import re
import sys
from pathlib import Path
from typing import Any

import requests
from requests import Response, Session
from requests.exceptions import RequestException
from urllib3.exceptions import InsecureRequestWarning


APP_NAME = "Immich Print Picker"
DEFAULT_DOWNLOAD_DIR = "./downloads"
DEFAULT_TIMEOUT = 60
DOWNLOAD_TIMEOUT = 60 * 60


class ImmichClient:
    def __init__(self, url: str, api_key: str, verify_ssl: bool = True) -> None:
        base_url = url.rstrip("/")
        self.api_base = base_url if base_url.endswith("/api") else f"{base_url}/api"

        self.session = Session()
        self.session.headers.update(
            {
                "x-api-key": api_key,
                "Accept": "application/json",
                "User-Agent": "immich-print-picker/1.0",
            }
        )
        self.verify_ssl = verify_ssl

        if not verify_ssl:
            requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

    def _request(self, method: str, path: str, **kwargs: Any) -> Response:
        response = self.session.request(
            method,
            f"{self.api_base}{path}",
            timeout=kwargs.pop("timeout", DEFAULT_TIMEOUT),
            verify=self.verify_ssl,
            **kwargs,
        )

        if not response.ok:
            detail = response.text.strip()
            if len(detail) > 800:
                detail = detail[:800] + "..."
            raise RuntimeError(
                f"Immich API returned HTTP {response.status_code} for {method} {path}"
                + (f"\n{detail}" if detail else "")
            )

        return response

    def get_albums(self) -> list[dict[str, Any]]:
        response = self._request("GET", "/albums")
        data = response.json()
        if not isinstance(data, list):
            raise RuntimeError("Unexpected response from Immich while listing albums.")
        return data

    def get_like_activities(self, album_id: str) -> list[dict[str, Any]]:
        response = self._request(
            "GET",
            "/activities",
            params={
                "albumId": album_id,
                "type": "like",
                "level": "asset",
            },
        )
        activities = response.json()
        if not isinstance(activities, list):
            raise RuntimeError("Unexpected response from Immich while reading likes.")

        # Album-level likes have assetId == null. Print Picker only works with
        # likes attached to individual photos/videos.
        return [
            activity
            for activity in activities
            if isinstance(activity, dict)
            and activity.get("id")
            and activity.get("assetId")
        ]

    def get_download_info(self, asset_ids: list[str]) -> dict[str, Any]:
        response = self._request(
            "POST",
            "/download/info",
            json={"assetIds": asset_ids},
        )
        data = response.json()
        if not isinstance(data, dict):
            raise RuntimeError("Unexpected response from Immich while preparing the download.")
        return data

    def download_archive(
        self,
        asset_ids: list[str],
        archive_name: str,
        destination: Path,
        part: int,
        total_parts: int,
    ) -> None:
        response = self._request(
            "POST",
            "/download/archive",
            json={
                "assetIds": asset_ids,
                "archiveName": archive_name,
            },
            stream=True,
            timeout=DOWNLOAD_TIMEOUT,
        )

        expected = int(response.headers.get("content-length", "0") or 0)
        downloaded = 0

        with destination.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if not chunk:
                    continue
                handle.write(chunk)
                downloaded += len(chunk)

                if expected > 0:
                    percent = downloaded * 100 / expected
                    print(
                        f"\r   Part {part}/{total_parts}: {percent:5.1f}% "
                        f"({format_bytes(downloaded)} / {format_bytes(expected)})",
                        end="",
                        flush=True,
                    )

        if expected > 0:
            print()
        else:
            print(f"   Part {part}/{total_parts}: downloaded {format_bytes(downloaded)}")

    def delete_activity(self, activity_id: str) -> None:
        self._request("DELETE", f"/activities/{activity_id}")


def env_bool(name: str, default: bool = True) -> bool:
    value = os.getenv(name)
    if value is None:
        return default

    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False

    raise ValueError(f"{name} must be true or false.")


def format_bytes(value: int | float) -> str:
    size = float(value)
    units = ["B", "KB", "MB", "GB", "TB"]

    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024

    return f"{size:.1f} TB"


def safe_filename(name: str) -> str:
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip().strip(".")
    return value or "immich-print-picker"


def choose_album(albums: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not albums:
        print("No albums are available to this API key.")
        return None

    albums = sorted(albums, key=lambda album: str(album.get("albumName", "")).casefold())

    print("\n📚 Available albums\n")
    for index, album in enumerate(albums, start=1):
        name = album.get("albumName") or "Untitled album"
        asset_count = album.get("assetCount", "?")
        shared = " • shared" if album.get("shared") else ""
        print(f"  {index:>3}. {name} ({asset_count} assets{shared})")

    while True:
        choice = input("\nChoose an album number (or q to quit): ").strip()

        if choice.lower() in {"q", "quit", "exit"}:
            return None

        try:
            index = int(choice)
        except ValueError:
            print("Please enter a valid album number.")
            continue

        if 1 <= index <= len(albums):
            return albums[index - 1]

        print("Please enter a number from the list.")


def choose_action() -> str | None:
    print("\nWhat would you like to do?\n")
    print("  1. 📦 Download print picks")
    print("  2. 🧹 Reset all likes")
    print("  3. 📦🧹 Download print picks, then reset all likes")
    print("  q. Quit")

    while True:
        choice = input("\nChoose an action: ").strip().lower()

        if choice in {"q", "quit", "exit"}:
            return None
        if choice == "1":
            return "download"
        if choice == "2":
            return "reset"
        if choice == "3":
            return "download_reset"

        print("Please choose 1, 2, 3, or q.")


def confirm_reset(album_name: str, total_likes: int, unique_assets: int) -> bool:
    print()
    print("⚠️  WARNING: this is a destructive action.")
    print(
        f'   It will remove {total_likes} like(s) from {unique_assets} asset(s) '
        f'in “{album_name}”.'
    )
    print("   This can include likes created by other users.")
    print("   The operation cannot be undone by Immich Print Picker.")
    confirmation = input("\nType RESET to continue: ").strip()
    return confirmation == "RESET"


def download_print_picks(
    client: ImmichClient,
    asset_ids: list[str],
    album_name: str,
    download_dir: Path,
) -> None:
    print("\n📦 Asking Immich to prepare the original files...")

    info = client.get_download_info(asset_ids)
    archives = info.get("archives") or []
    total_size = int(info.get("totalSize") or 0)

    if not archives:
        raise RuntimeError("Immich returned no downloadable archives.")

    download_dir.mkdir(parents=True, exist_ok=True)

    base_name = f"{safe_filename(album_name)} - print picks"
    print(
        f"⬇️  Downloading {format_bytes(total_size)} "
        f"in {len(archives)} archive(s) to {download_dir.resolve()}"
    )

    for index, archive in enumerate(archives, start=1):
        part_asset_ids = archive.get("assetIds") or []
        if not part_asset_ids:
            continue

        suffix = "" if len(archives) == 1 else f" - part {index}"
        destination = download_dir / f"{base_name}{suffix}.zip"

        client.download_archive(
            part_asset_ids,
            base_name,
            destination,
            index,
            len(archives),
        )
        print(f"   ✅ Saved: {destination}")

    print("\n✨ Download complete. Your print picks are ready.")


def reset_likes(client: ImmichClient, activities: list[dict[str, Any]]) -> None:
    total = len(activities)
    removed = 0

    print(f"\n🧹 Removing {total} like(s)...")

    for index, activity in enumerate(activities, start=1):
        try:
            client.delete_activity(str(activity["id"]))
        except Exception as exc:
            raise RuntimeError(
                f"Like reset stopped after {removed}/{total} successful deletions. "
                f"The album may now be partially reset.\n{exc}"
            ) from exc

        removed += 1
        print(f"\r   Removed {index}/{total} like(s)", end="", flush=True)

    print()
    print("✅ All asset likes were removed from the album.")


def main() -> int:
    print("🖨️  Immich Print Picker")
    print("   Export and manage the photos your group liked in a shared Immich album.")

    immich_url = os.getenv("IMMICH_URL", "").strip()
    api_key = os.getenv("IMMICH_API_KEY", "").strip()
    download_dir = Path(os.getenv("DOWNLOAD_DIR", DEFAULT_DOWNLOAD_DIR)).expanduser()

    if not immich_url:
        print("\n❌ Missing IMMICH_URL.", file=sys.stderr)
        return 2

    if not api_key:
        print("\n❌ Missing IMMICH_API_KEY.", file=sys.stderr)
        return 2

    try:
        verify_ssl = env_bool("IMMICH_VERIFY_SSL", True)
        client = ImmichClient(immich_url, api_key, verify_ssl=verify_ssl)

        albums = client.get_albums()
        album = choose_album(albums)
        if album is None:
            print("\nBye! 👋")
            return 0

        album_id = str(album["id"])
        album_name = str(album.get("albumName") or "Untitled album")

        print(f"\n🔎 Looking for liked assets in “{album_name}”...")
        activities = client.get_like_activities(album_id)

        if not activities:
            print("⚠️  No liked photos or videos were found in this album.")
            return 0

        asset_ids = sorted({str(activity["assetId"]) for activity in activities})
        print(
            f"❤️  Found {len(asset_ids)} unique liked asset(s) "
            f"with {len(activities)} total like(s)."
        )

        action = choose_action()
        if action is None:
            print("\nBye! 👋")
            return 0

        if action in {"download", "download_reset"}:
            download_print_picks(client, asset_ids, album_name, download_dir)

        if action == "reset":
            if not confirm_reset(album_name, len(activities), len(asset_ids)):
                print("\nReset cancelled.")
                return 0
            reset_likes(client, activities)

        if action == "download_reset":
            print("\nThe download completed successfully.")
            if not confirm_reset(album_name, len(activities), len(asset_ids)):
                print("\nLike reset skipped. Your downloaded files are safe.")
                return 0
            reset_likes(client, activities)

        return 0

    except (RequestException, RuntimeError, ValueError, KeyError) as exc:
        print(f"\n❌ {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n\nCancelled.")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
