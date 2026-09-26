import json
import logging
from io import BytesIO

from app.config import settings


logger = logging.getLogger(__name__)


def upload_json_file(file_name: str, content: bytes) -> str:
    if not settings.GOOGLE_DRIVE_FOLDER_ID:
        raise RuntimeError("Google Drive folder is not configured")
    if not settings.GOOGLE_SERVICE_ACCOUNT_JSON:
        raise RuntimeError("Google Drive service account is not configured")

    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaIoBaseUpload
    except ImportError as error:
        raise RuntimeError(
            "Google Drive dependencies are not installed"
        ) from error

    try:
        credentials_info = json.loads(
            settings.GOOGLE_SERVICE_ACCOUNT_JSON
        )
        credentials = service_account.Credentials.from_service_account_info(
            credentials_info,
            scopes=["https://www.googleapis.com/auth/drive.file"],
        )
        drive = build(
            "drive",
            "v3",
            credentials=credentials,
            cache_discovery=False,
        )
        media = MediaIoBaseUpload(
            BytesIO(content),
            mimetype="application/json",
            resumable=False,
        )
        result = drive.files().create(
            body={
                "name": file_name,
                "parents": [settings.GOOGLE_DRIVE_FOLDER_ID],
            },
            media_body=media,
            fields="id",
        ).execute()
    except (ValueError, TypeError, json.JSONDecodeError) as error:
        raise RuntimeError(
            "Google Drive credentials are invalid"
        ) from error
    except Exception as error:
        logger.exception(
            "Google Drive upload failed for archive file %s",
            file_name,
        )
        raise RuntimeError("Google Drive upload failed") from error

    file_id = result.get("id")
    if not file_id:
        raise RuntimeError("Google Drive did not return a file ID")
    return file_id
