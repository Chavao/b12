#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import hmac
import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone

SUBMISSION_URL = "https://b12.io/apply/submission"


def _build_payload() -> dict[str, str]:
    run_id = os.environ.get("GITHUB_RUN_ID")
    if not run_id:
        raise RuntimeError("GITHUB_RUN_ID must be set in GitHub Actions.")

    return {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "name": "Diego Chavão",
        "email": "diegochavao@gmail.com",
        "resume_link": "https://www.chavao.net/f/resume_chavao.pdf",
        "repository_link": "https://github.com/Chavao/b12",
        "action_run_link": f"https://github.com/Chavao/b12/actions/runs/{run_id}",
    }


def main() -> None:
    signing_secret = os.environ.get("B12_CHALLENGE")
    if not signing_secret:
        raise RuntimeError("Missing B12_CHALLENGE secret.")
    signing_secret = signing_secret.strip()
    if not signing_secret:
        raise RuntimeError("B12_CHALLENGE secret is empty after trimming whitespace.")

    payload = _build_payload()
    body = json.dumps(
        payload,
        separators=(",", ":"),
        sort_keys=True,
        ensure_ascii=True,
    ).encode("utf-8")
    digest = hmac.new(signing_secret.encode("utf-8"), body, hashlib.sha256).hexdigest()

    headers = {
        "Content-Type": "application/json",
        "X-Signature-256": f"sha256={digest}",
    }
    request = urllib.request.Request(SUBMISSION_URL, data=body, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            response_text = response.read().decode("utf-8", errors="replace")
            print(f"Submission sent successfully. Status: {response.status}")
            if response_text:
                print(response_text)
    except urllib.error.HTTPError as error:
        error_body = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Submission failed with status {error.code}: {error_body}") from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"Submission failed due to network error: {error.reason}") from error


if __name__ == "__main__":
    main()
