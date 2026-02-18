import os
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# ============================================================
# FIND & REPLACE PAIRS — edit these if links change in future
# ============================================================
REPLACEMENTS = [
    ("https://ko-fi.com/taipeitours",  "https://ko-fi.com/walkaroundtaiwan"),
    ("@taipeipeacewalker",             "@walkaroundtaiwan"),
]

# ============================================================
# SET TO True TO TEST WITHOUT CHANGING ANYTHING ON YOUTUBE
# SET TO False WHEN YOU'RE READY TO ACTUALLY UPDATE
# ============================================================
DRY_RUN = False
# ============================================================

SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]


def authenticate():
    """
    Handles OAuth login. On first run it opens a browser to log in.
    After that it saves a token.pickle file so you don't have to log in again.
    """
    creds = None

    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("client_secrets.json", SCOPES)
            creds = flow.run_local_server(port=0)

        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    return build("youtube", "v3", credentials=creds)


def get_uploads_playlist_id(youtube):
    """
    Every channel has a hidden 'uploads' playlist that contains all their videos.
    This fetches that playlist ID from your channel info.
    """
    response = youtube.channels().list(
        part="contentDetails",
        mine=True
    ).execute()

    # Dig into the response to get the uploads playlist ID
    return response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]


def get_all_videos(youtube):
    """
    Fetches every video from your uploads playlist, page by page.
    This is more reliable than search().list() which can miss videos.
    """
    videos = []
    next_page_token = None

    # First get the uploads playlist ID for this channel
    uploads_playlist_id = get_uploads_playlist_id(youtube)
    print(f"Uploads playlist ID: {uploads_playlist_id}")

    print("Fetching your videos...")

    while True:
        # Get a page of video IDs from the uploads playlist
        playlist_response = youtube.playlistItems().list(
            part="contentDetails",
            playlistId=uploads_playlist_id,
            maxResults=50,
            pageToken=next_page_token
        ).execute()

        # Extract the video IDs from this page
        video_ids = [item["contentDetails"]["videoId"] for item in playlist_response.get("items", [])]

        if video_ids:
            # Fetch full snippet (title + description) for these video IDs
            details = youtube.videos().list(
                part="snippet",
                id=",".join(video_ids)
            ).execute()

            videos.extend(details.get("items", []))

        # Move to next page if there is one
        next_page_token = playlist_response.get("nextPageToken")
        if not next_page_token:
            break

    print(f"Found {len(videos)} videos total.")
    return videos


def apply_replacements(text):
    """
    Runs every find/replace pair against the given text.
    Returns the updated text and a count of how many substitutions were made.
    """
    total_changes = 0
    for old, new in REPLACEMENTS:
        count = text.count(old)
        if count > 0:
            text = text.replace(old, new)
            total_changes += count
    return text, total_changes


def preview_changes(video):
    """
    In dry run mode: prints exactly which strings would change in this video's description.
    Does NOT call the YouTube API to update anything.
    """
    snippet = video["snippet"]
    title = snippet["title"]
    description = snippet.get("description", "")

    matches = []
    for old, new in REPLACEMENTS:
        count = description.count(old)
        if count > 0:
            matches.append(f'  FIND:    "{old}"\n  REPLACE: "{new}"\n  ({count} occurrence(s))')

    if matches:
        print(f"\n📋 {title}")
        for m in matches:
            print(m)
        return True

    return False


def update_video(youtube, video):
    """
    Takes a single video, applies find/replace to its description,
    and sends the updated description back to YouTube.
    """
    snippet = video["snippet"]
    original_description = snippet.get("description", "")

    updated_description, changes = apply_replacements(original_description)

    # Only call the API if something actually changed — saves your quota
    if changes == 0:
        return False

    # Must re-send title and categoryId too or YouTube rejects the request
    snippet["description"] = updated_description

    youtube.videos().update(
        part="snippet",
        body={
            "id": video["id"],
            "snippet": snippet
        }
    ).execute()

    return True


def main():
    if DRY_RUN:
        print("=" * 50)
        print("  DRY RUN MODE — nothing will be changed")
        print("  Set DRY_RUN = False to apply for real")
        print("=" * 50)

    youtube = authenticate()
    videos = get_all_videos(youtube)

    updated_count = 0
    skipped_count = 0

    for i, video in enumerate(videos):
        title = video["snippet"]["title"]

        if DRY_RUN:
            found = preview_changes(video)
            if found:
                updated_count += 1
            else:
                skipped_count += 1
        else:
            success = update_video(youtube, video)
            if success:
                updated_count += 1
                print(f"[{i+1}/{len(videos)}] ✅ Updated: {title}")
            else:
                skipped_count += 1
                print(f"[{i+1}/{len(videos)}] — Skipped (no match): {title}")

    print("\n=============================")
    if DRY_RUN:
        print(f"Dry run complete.")
        print(f"{updated_count} videos WOULD be updated, {skipped_count} would be skipped.")
        print("If this looks right, set DRY_RUN = False and run again.")
    else:
        print(f"Done! {updated_count} videos updated, {skipped_count} skipped.")
    print("=============================")


if __name__ == "__main__":
    main()