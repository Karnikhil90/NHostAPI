"""
Nbrouser v1.0.0 - A basic utility Brouser specially for handle downloading files


MIT License

Copyright (c) 2026 Nikhil Karmakar

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

"""
from __future__ import annotations
import os
import pathlib
import re
import requests
import urllib.parse
import mimetypes
import hashlib
import time
import sys
from typing import Optional, Callable, Dict, Any


class NBrouser:
    """
    Network utility for browsing and safe file downloads.

    Features:
      1. HTTP GET helpers
      2. Atomic downloads using `.tmp` files
      3. Deterministic, filename can be contomize sepratly 
    """

    DEFAULT_NAME = "download.bin"
    TEMP_SUFFIX = ".tmp"
    CHUNK_SIZE = 64 * 1024  # 64 KB

    def __init__(
        self,
        *,
        base_headers: Optional[Dict[str, str]] = None,
        timeout: int = 20,
    ):
        self._session = requests.Session()
        self._timeout = timeout
        self._session.headers.update(
            base_headers or {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept": "*/*",
                "Accept-Language": "en-US,en;q=0.9",
                "Connection": "keep-alive",
            }
        )



    def get(self, url: str, **kwargs) -> requests.Response:
        response = self._session.get(url, timeout=self._timeout, **kwargs)
        response.raise_for_status()
        return response

    def get_text(self, url: str, **kwargs) -> str:
        return self.get(url, **kwargs).text

    def get_json(self, url: str, **kwargs) -> Any:
        return self.get(url, **kwargs).json()

    def download(
        self,
        url: str,
        destination: os.PathLike | str = "",
        *,
        filename: Optional[str] = None,
        resume: bool = True,
        show_progress: bool = True,
        on_progress: Optional[Callable[[int, Optional[int]], None]] = None
    ) -> Dict[str, Any]:
        """
        1.Atomic `.tmp` writes
        2.Built-in progress bar (show_progress=True)
        3.Optional custom progress callback (on_progress)
        
        Returns dictionary or map type:
            {
                "path": pathlib.Path,
                "size": int (bytes),
                "speed": float (bytes/sec),
                "time": float (seconds)
            }
        """
        dest_path = pathlib.Path(destination) if destination else pathlib.Path.cwd()
        dest_path.mkdir(parents=True, exist_ok=True)

        try:
            head_resp = self._session.head(url, timeout=self._timeout, allow_redirects=True)
            head_resp.raise_for_status()
        except (requests.exceptions.RequestException, requests.exceptions.ConnectionError):
            head_resp = None

        final_name = self._resolve_filename(url, filename, response=head_resp)
        target_path = dest_path / final_name if dest_path.is_dir() else pathlib.Path(destination)
        temp_path = target_path.with_suffix(target_path.suffix + self.TEMP_SUFFIX)

        supports_resume = False
        if head_resp:
            supports_resume = head_resp.headers.get("Accept-Ranges", "").lower() == "bytes"

        headers = {}
        mode = "wb"
        written = 0
        if resume and supports_resume and temp_path.exists():
            written = temp_path.stat().st_size
            headers["Range"] = f"bytes={written}-"
            mode = "ab"

        start_time = time.time()

        with self._session.get(url, stream=True, headers=headers, timeout=self._timeout) as response:
            if response.status_code not in (200, 206):
                response.raise_for_status()

            total = self._compute_total_size(response, written)

            with open(temp_path, mode) as stream:
                for chunk in response.iter_content(self.CHUNK_SIZE):
                    if not chunk:
                        continue
                    stream.write(chunk)
                    written += len(chunk)

                    # costom callback for Progress of the downloading
                    if on_progress:
                        on_progress(written, total)

                    elif show_progress:
                        elapsed = time.time() - start_time
                        avg_speed = written / elapsed if elapsed > 0 else 0

                        written_str = self.format_size_str(written)
                        total_str = self.format_size_str(total) if total else "??"
                        speed_str = self.format_size_str(int(avg_speed)) + "/s"

                        if total:
                            percent = written * 100 / total
                            print(f"\rDownloading {written_str}/{total_str} ({percent:.1f}%) @ {speed_str}", end="")
                        else:
                            print(f"\rDownloading {written_str} @ {speed_str}", end="")

                        sys.stdout.flush()

        temp_path.replace(target_path)

        if show_progress and not on_progress:
            print()  # newline after progress

        elapsed = time.time() - start_time
        avg_speed = written / elapsed if elapsed > 0 else 0

        return {
            "path": target_path,
            "size": written,
            "speed": avg_speed,
            "time": elapsed
        }

    @staticmethod
    def _compute_total_size(response: requests.Response, already_written: int) -> Optional[int]:
        length = response.headers.get("Content-Length")
        if not length:
            return None
        size = int(length)
        return size + already_written if response.status_code == 206 else size

    def _resolve_filename(self, url: str, user_name: Optional[str], response: Optional[requests.Response] = None) -> str:
        """
        Determine a safe, deterministic filename:
          1. User-supplied name (validated)
          2. Content-Disposition header
          3. URL path
          4. Query parameter hints (?file=)
          5. Fallback: hashed name + extension from content-type
        """
        # 1. User-supplied
        if user_name and self._is_valid_filename(user_name):
            return self._sanitize_filename(user_name)

        # 2. From response headers
        header_name = None
        if response:
            cd = response.headers.get("Content-Disposition")
            if cd:
                # RFC 5987: filename*
                match_star = re.search(r"filename\*\s*=\s*[^']*'[^']*'([^;]+)", cd, flags=re.I)
                if match_star:
                    header_name = urllib.parse.unquote(match_star.group(1))
                else:
                    # regular filename
                    match = re.search(r'filename\s*=\s*"?(.*?)"?($|;)', cd, flags=re.I)
                    if match:
                        header_name = match.group(1)
            if header_name and self._is_valid_filename(header_name):
                return self._sanitize_filename(header_name)

        # 3. From URL path
        url_name = self._name_from_url(url)
        if self._is_valid_filename(url_name):
            return self._sanitize_filename(url_name)

        # 4. From query parameters
        parsed = urllib.parse.urlparse(url)
        query_name = urllib.parse.parse_qs(parsed.query).get("file")
        if query_name:
            query_name = query_name[0]
            if self._is_valid_filename(query_name):
                return self._sanitize_filename(query_name)

        # 5. Fallback: hash + extension from content type
        ext = ""
        if response:
            ext = mimetypes.guess_extension(response.headers.get("Content-Type", "application/octet-stream")) or ".bin"
        hash_name = hashlib.sha256(url.encode()).hexdigest()[:10]
        return f"file_{hash_name}{ext}"

    @staticmethod
    def _name_from_url(url: str) -> str:
        """Get last component of URL path."""
        parsed = urllib.parse.urlparse(url)
        tail = os.path.basename(parsed.path)
        return tail or ""

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        """Replace illegal filesystem characters with underscores."""
        name = name.strip()
        name = re.sub(r"[<>:\"/\\|?*\x00-\x1F]", "_", name)
        return name

    @staticmethod
    def _is_valid_filename(name: str) -> bool:
        if not name or not name.strip():
            return False
        if any(sep in name for sep in (os.sep, os.altsep) if sep):
            return False
        return not re.search(r'[<>:"/\\|?*\x00-\x1F]', name)
    
    @staticmethod
    def _compute_size(size_bytes: int | float) -> tuple[float, str]:
        SIZE_UNITS = ["B", "KB", "MB", "GB", "TB"]
        factor = 1024.0
        size = float(size_bytes)

        for unit in SIZE_UNITS:
            if size < factor:
                value = round(size, 1) if size % 1 != 0 else int(size)
                return value, unit
            size /= factor

        return round(size, 1), "PB"  # fallback

    @staticmethod
    def format_size_str(size_bytes: int | float) -> str:
        value, unit = NBrouser._compute_size(size_bytes)
        return f"{value} {unit}"

    @staticmethod
    def format_size(size_bytes: int | float) -> tuple[float, str]:
        return NBrouser._compute_size(size_bytes)

    @staticmethod
    def format_size_dict(size_bytes: int | float) -> dict:
        value, unit = NBrouser._compute_size(size_bytes)
        return {"value": value, "unit": unit}