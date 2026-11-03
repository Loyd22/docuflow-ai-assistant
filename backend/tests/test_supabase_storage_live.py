"""Opt-in test for real Supabase Storage operations."""

import os
from io import BytesIO
from pathlib import Path
from uuid import uuid4

import pytest

from app.core.config import settings
from app.storage.factory import get_document_storage_for_provider


@pytest.mark.skipif(
    os.getenv("RUN_SUPABASE_STORAGE_LIVE_TESTS") != "1",
    reason="Live Supabase Storage testing is disabled.",
)
def test_live_supabase_storage_lifecycle(
    tmp_path: Path,
) -> None:
    """Verify upload, download, and deletion in Supabase."""

    if not settings.supabase_url or not settings.supabase_secret_key:
        pytest.fail("Supabase credentials are missing.")

    # Connect using the existing storage factory.
    storage = get_document_storage_for_provider("supabase")

    # Give the test object a unique name.
    storage_key = f"docuflow-live-test-{uuid4().hex}.txt"
    content = b"DocuFlow live Supabase Storage test."

    # Upload one disposable test object.
    saved_key = storage.save(
        BytesIO(content),
        storage_key,
    )

    assert saved_key == storage_key

    destination = tmp_path / "downloaded.txt"

    try:
        # Download the object and compare its contents.
        storage.download_to_path(saved_key, destination)

        assert destination.read_bytes() == content

    finally:
        # Attempt cleanup even if downloading fails.
        storage.delete(saved_key)

    # Confirm the deleted object cannot be downloaded.
    with pytest.raises(FileNotFoundError):
        storage.download_to_path(
            saved_key,
            tmp_path / "deleted.txt",
        )
