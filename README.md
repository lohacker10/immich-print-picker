# 🖨️ Immich Print Picker

> Turn ❤️ likes in a shared [Immich](https://immich.app/) album into a ready-to-download set of original files for printing.

**Immich Print Picker** is a small command-line utility built for a simple workflow: multiple people browse a shared Immich album, like the photos they want to keep or print, and then one command downloads every asset that received **at least one like**.

No tags to maintain. No duplicate albums. No manual cross-user selection. Just **like → pick → download → reset**.

---

## ✨ Why this project exists

Shared albums are great when photos come from more than one Immich user. Selecting a final set for printing, however, can become awkward when the assets belong to different people.

Likes already work naturally as a lightweight voting/selection mechanism inside a shared album, so Immich Print Picker treats them as **print picks**:

1. 👨‍👩‍👧‍👦 Everyone browses the shared album.
2. ❤️ Anyone likes the photos they want.
3. 🖨️ Run Immich Print Picker.
4. 📚 Choose the album.
5. 📦 The tool downloads every uniquely liked asset as one or more ZIP archives.
6. 🧹 When you're done, you can optionally remove all asset likes from the album and start fresh.

A photo with several likes is downloaded **only once**. Resetting likes is always an explicit, confirmed action.

---

## 🌟 Features

- 📚 Lists albums available to the API key owner
- 🤝 Works with shared albums
- ❤️ Selects assets with **at least one like**, regardless of who liked them
- 🔁 Automatically removes duplicate selections
- 📦 Downloads the **original files** through Immich's API
- 🧹 Can reset **all asset likes** in an album after printing
- ✅ Supports a safe **download first, reset afterwards** workflow
- ⚠️ Requires typing `RESET` before any destructive reset
- 📁 Configurable export folder through `.env`
- 🧩 Supports large selections split by Immich into multiple ZIP archives
- 🐍 Runs directly with Python
- 🐳 Fully Docker-friendly
- 🔐 Uses an Immich API key — no password is stored
- 🛡️ Does not modify albums, assets, or metadata; likes are only changed when you explicitly choose a reset action

---

## 🚀 Quick start with Docker Compose

### 1. Clone the repository

```bash
git clone https://github.com/lohacker10/immich-print-picker.git
cd immich-print-picker
```

### 2. Create your configuration

```bash
cp .env.example .env
```

Edit `.env`:

```dotenv
IMMICH_URL=https://immich.example.com
IMMICH_API_KEY=your-api-key-here
DOWNLOAD_DIR=./downloads
IMMICH_VERIFY_SSL=true
```

> `IMMICH_URL` can be either your normal Immich URL or the URL ending in `/api`.

`DOWNLOAD_DIR` controls where exported ZIP archives are saved **on the host machine** when using Docker Compose.

For example:

```dotenv
DOWNLOAD_DIR=/mnt/photos/print-exports
```

or:

```dotenv
DOWNLOAD_DIR=./exports
```

### 3. Start the picker

```bash
docker compose run --rm immich-print-picker
```

The downloaded ZIP files will appear in the folder configured by `DOWNLOAD_DIR`.

---

## 🔑 Create an Immich API key

In Immich, create an API key for the user who should run the picker.

The recommended permissions are:

```text
album.read
activity.read
activity.delete
asset.download
user.read
```

`activity.delete` and `user.read` are required only for the like-reset feature. If you only want to download print picks, the original read/download permissions are enough.

The API key can only work with albums and assets that its Immich user is allowed to access.

> 🔒 Keep the key private. Never commit your `.env` file. It is ignored by this repository's `.gitignore`.

---

## 🐳 Docker

### Build

```bash
docker build -t immich-print-picker .
```

### Run

```bash
docker run --rm -it \
  -e IMMICH_URL="https://immich.example.com" \
  -e IMMICH_API_KEY="your-api-key-here" \
  -v "/path/on/host:/downloads" \
  immich-print-picker
```

The container is intentionally interactive because the tool asks you which album to process.

When using plain `docker run`, choose the host export folder with the left side of the volume mapping:

```text
/path/on/host:/downloads
```

### Docker Compose

Create `.env` from the included example:

```bash
cp .env.example .env
```

Then choose the host export directory:

```dotenv
DOWNLOAD_DIR=/mnt/photos/print-exports
```

and run:

```bash
docker compose run --rm immich-print-picker
```

Docker Compose mounts that host folder into the container at `/downloads`.

---

## 🐍 Run without Docker

### Requirements

- Python 3.10+
- Access to your Immich server
- An Immich API key

### Install

```bash
git clone https://github.com/lohacker10/immich-print-picker.git
cd immich-print-picker

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Configure

Linux/macOS:

```bash
export IMMICH_URL="https://immich.example.com"
export IMMICH_API_KEY="your-api-key-here"
export DOWNLOAD_DIR="./downloads"
```

Optional:

```bash
export IMMICH_VERIFY_SSL="true"
```

When running without Docker, `DOWNLOAD_DIR` is used directly by the Python script as the destination folder.

### Run

```bash
python3 immich_print_picker.py
```

---

## 🎯 Usage

A typical session looks like this:

```text
🖨️  Immich Print Picker
   Export the photos your group liked in a shared Immich album.

📚 Available albums

    1. Summer Holiday (421 assets • shared)
    2. Wedding (843 assets • shared)
    3. Family (128 assets)

Choose an album number (or q to quit): 1

🔎 Looking for liked assets in “Summer Holiday”...
❤️  Found 37 unique liked asset(s) with 52 total like(s).

What would you like to do?

  1. 📦 Download print picks
  2. 🧹 Reset all likes
  3. 📦🧹 Download print picks, then reset all likes
  q. Quit

Choose an action: 3

📦 Asking Immich to prepare the original files...
⬇️  Downloading 184.3 MB in 1 archive(s) to /downloads
   ✅ Saved: /downloads/Summer Holiday - print picks.zip

✨ Download complete. Your print picks are ready.

The download completed successfully.

⚠️  WARNING: this is a destructive action.
   It will remove 52 like(s) from 37 asset(s) in “Summer Holiday”.
   This can include likes created by other users.
   The operation cannot be undone by Immich Print Picker.

Type RESET to continue: RESET

🧹 Removing 52 like(s)...
✅ All asset likes were removed from the album.
```

If the selected album has no liked assets:

```text
⚠️  No liked photos or videos were found in this album.
```

---

## ⚙️ Configuration

| Variable | Required | Default | Description |
|---|---:|---|---|
| `IMMICH_URL` | ✅ | — | Base URL of your Immich server |
| `IMMICH_API_KEY` | ✅ | — | Immich API key |
| `DOWNLOAD_DIR` | ❌ | `./downloads` | Export folder. With Docker Compose this is a host path; without Docker it is used directly by Python |
| `IMMICH_VERIFY_SSL` | ❌ | `true` | Set to `false` only if you intentionally use an untrusted/self-signed certificate |

Example `.env`:

```dotenv
IMMICH_URL=https://immich.example.com
IMMICH_API_KEY=replace-me
DOWNLOAD_DIR=./downloads
IMMICH_VERIFY_SSL=true
```

### Export folder examples

Relative path:

```dotenv
DOWNLOAD_DIR=./exports
```

Absolute Linux path:

```dotenv
DOWNLOAD_DIR=/mnt/storage/immich-print-exports
```

NAS-mounted folder:

```dotenv
DOWNLOAD_DIR=/mnt/photos/to-print
```

> When Docker Compose is used, this path must be accessible to the Docker host.

---

## 🧠 How it works

Immich Print Picker talks only to the Immich HTTP API.

It:

1. Retrieves the albums available to the authenticated user.
2. Lets you select one interactively.
3. Reads the album's `like` activities at asset level.
4. Collects all non-null asset IDs.
5. Deduplicates them, so multiple likes on the same photo still produce one download.
6. Asks Immich for download archive information.
7. Streams the ZIP archive(s) to the configured export folder.
8. If requested, verifies that the API key belongs to the album owner before deleting likes.
9. Deletes the album's asset-level like activities only after explicit confirmation.

The project does **not** connect directly to Immich's PostgreSQL database.

---

## 📁 Output

By default, exports are written to:

```text
./downloads/
```

You can change this with:

```dotenv
DOWNLOAD_DIR=/your/export/folder
```

Archive names follow this format:

```text
<Album name> - print picks.zip
```

If Immich splits a large export into several archives:

```text
<Album name> - print picks - part 1.zip
<Album name> - print picks - part 2.zip
<Album name> - print picks - part 3.zip
```

Original filenames inside the archives are produced by Immich.

---

## 🧹 Resetting likes

After a print/export cycle, you can reset the album so it is ready for a new selection.

The tool offers:

- **Download print picks** — export only; likes stay untouched.
- **Reset all likes** — remove every asset-level like in the selected album.
- **Download print picks, then reset all likes** — download first, and only offer the reset after all archives were saved successfully.

Before deleting anything, the tool requires:

1. an API key with `activity.delete` and `user.read`;
2. the API key user to be the **owner of the selected album**;
3. an explicit confirmation by typing `RESET`.

The album-owner check is important because Immich allows an album owner to remove other users' activities, while a non-owner can only remove activities they are allowed to delete. Immich Print Picker blocks the full reset in advance when it cannot safely remove everyone's likes.

Only **asset-level likes** are reset. Album-level likes and comments are left untouched.

> ⚠️ Resetting likes is destructive. Immich Print Picker cannot restore deleted likes.

---

## 🛡️ Privacy & security

- Your Immich credentials stay on your machine/server.
- The tool requires an API key, not your Immich password.
- `.env` is ignored by Git.
- No analytics or telemetry are included.
- No external service is contacted by the application.
- The tool only reads album/activity information and downloads accessible assets.

If you expose Immich over the internet, use HTTPS and keep your API key secret.

---

## 🧯 Troubleshooting

### `Missing IMMICH_URL` or `Missing IMMICH_API_KEY`

The required environment variables are not set. If you use Docker Compose, make sure you created `.env`.

### `HTTP 401`

The API key is invalid, expired, or not being accepted by the server.

### `HTTP 403`

The API key is missing one of the required permissions, or its user does not have access to the requested album/assets.

### Reset says additional permissions are required

For the reset feature, add:

```text
activity.delete
user.read
```

to the API key.

### Reset says the API key must belong to the album owner

Immich only allows a full cross-user like reset when the authenticated user owns the album. Use an API key created by the album owner. No likes are removed when this preflight check fails.

### No albums are listed

The Immich user associated with the API key cannot access any albums.

### No liked assets are found

Make sure the likes are attached to individual photos/videos inside the album. A like on the album itself is intentionally ignored.

### Export folder errors

If Docker cannot create or write files in `DOWNLOAD_DIR`, make sure:

- the folder exists or Docker can create it;
- the Docker host has permission to access it;
- the path is valid on the machine running Docker.

### Self-signed HTTPS certificate

For a trusted home-network setup with a deliberately self-signed certificate, you can set:

```dotenv
IMMICH_VERIFY_SSL=false
```

When `IMMICH_VERIFY_SSL=false`, Immich Print Picker suppresses urllib3's expected `InsecureRequestWarning` to keep the interactive output clean. Certificate verification is still disabled, so use this option only on networks you trust.

Using a valid certificate is recommended whenever possible.

---

## 🧩 Compatibility

Immich evolves quickly. This project uses public Immich API endpoints rather than accessing the database directly, which should make upgrades easier, but API behavior can still change between Immich releases.

If an Immich update breaks the picker, please open an issue with:

- your Immich version;
- the error message;
- the command you used.

**Never include your API key in an issue.**

---

## 🤝 Contributing

Issues and pull requests are welcome.

Useful contributions include:

- compatibility fixes for new Immich releases;
- better terminal UX;
- optional non-interactive album selection;
- tests;
- packaging improvements.

Please keep the project focused on the core idea: **use shared-album likes as a simple selection mechanism, export the selected originals, and optionally reset the selection for the next print cycle**.

---

## 📄 License

Released under the [MIT License](LICENSE).

---

## 🙏 Acknowledgements

Built for the excellent [Immich](https://immich.app/) ecosystem.

This is an independent community project and is not affiliated with or endorsed by the Immich project.
