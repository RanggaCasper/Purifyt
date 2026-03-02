import re
from datetime import datetime
from typing import List, Optional
import httpx
from fastapi import HTTPException

from app.config.logging_config import get_logger
from app.config.settings import get_settings

logger = get_logger(__name__)
settings = get_settings()
BASE_URL = "https://www.googleapis.com/youtube/v3"

class YouTubeService:
    def __init__(self):
        if not settings.YOUTUBE_API_KEY:
            raise HTTPException(
                status_code=500,
                detail="YOUTUBE_API_KEY is not configured. Set it in .env",
            )
        self.api_key = settings.YOUTUBE_API_KEY

    async def search_videos(
        self, query: str, max_results: int = 5
    ) -> List[dict]:
        """Return a list of {video_id, title, channel_name, published_at}."""
        logger.info("[YOUTUBE] Searching videos — query='%s' max_results=%d", query, max_results)
        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": max_results,
            "key": self.api_key,
        }
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{BASE_URL}/search", params=params, timeout=15)
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail=resp.json())
            data = resp.json()

        videos = []
        for item in data.get("items", []):
            video_id = item.get("id", {}).get("videoId")
            if not video_id:
                continue
            snippet = item["snippet"]
            videos.append(
                {
                    "video_id": video_id,
                    "title": snippet["title"],
                    "channel_name": snippet["channelTitle"],
                    "published_at": snippet["publishedAt"],
                }
            )
        return videos

    async def fetch_comments(
        self, video_id: str, max_results: Optional[int] = None
    ) -> List[dict]:
        """
        Return a list of comment dicts ready for DB insertion.
        If max_results is None, fetch ALL available comments.
        """
        logger.info("[YOUTUBE] Fetching comments — video_id=%s max_results=%s", video_id, max_results)
        # First get video details
        video_info = await self._get_video_info(video_id)

        params = {
            "part": "snippet",
            "videoId": video_id,
            "maxResults": 100,  # max per page allowed by YouTube API
            "textFormat": "plainText",
            "key": self.api_key,
        }

        all_comments: List[dict] = []
        page_token: Optional[str] = None

        async with httpx.AsyncClient() as client:
            while True:
                if max_results is not None and len(all_comments) >= max_results:
                    break

                if page_token:
                    params["pageToken"] = page_token

                resp = await client.get(
                    f"{BASE_URL}/commentThreads", params=params, timeout=30
                )
                if resp.status_code == 403:
                    raise HTTPException(
                        status_code=403,
                        detail="Comments are disabled for this video or API quota exceeded.",
                    )
                if resp.status_code != 200:
                    raise HTTPException(
                        status_code=resp.status_code, detail=resp.json()
                    )
                data = resp.json()

                for item in data.get("items", []):
                    snippet = item["snippet"]["topLevelComment"]["snippet"]
                    published = snippet.get("publishedAt")
                    comment_date = (
                        datetime.fromisoformat(published.replace("Z", "+00:00"))
                        if published
                        else None
                    )
                    all_comments.append(
                        {
                            "video_id": video_id,
                            "title": video_info.get("title"),
                            "channel_name": video_info.get("channel_name"),
                            "date": comment_date,
                            "author": snippet.get("authorDisplayName"),
                            "comment": snippet.get("textDisplay"),
                            "label": None,
                            "clean_comment": None,
                            "predicted_label": None,
                        }
                    )

                page_token = data.get("nextPageToken")
                if not page_token:
                    break

        if max_results is not None:
            return all_comments[:max_results]
        return all_comments

    async def _get_video_info(self, video_id: str) -> dict:
        params = {
            "part": "snippet",
            "id": video_id,
            "key": self.api_key,
        }
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{BASE_URL}/videos", params=params, timeout=15)
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail=resp.json())
            data = resp.json()

        items = data.get("items", [])
        if not items:
            raise HTTPException(status_code=404, detail=f"Video {video_id} not found")
        snippet = items[0]["snippet"]
        return {
            "title": snippet["title"],
            "channel_name": snippet["channelTitle"],
            "published_at": snippet["publishedAt"],
        }

    async def get_channel_info(self, channel_input: str) -> dict:
        """
        Get channel info from a channel ID, @handle, or custom URL.
        Returns: {"channel_id": str, "title": str, "description": str}
        """
        # Try as channel ID first (starts with UC)
        if channel_input.startswith("UC") and len(channel_input) == 24:
            return await self._get_channel_by_id(channel_input)

        # Try as @handle
        handle = channel_input.lstrip("@")
        return await self._get_channel_by_handle(handle)

    async def _get_channel_by_id(self, channel_id: str) -> dict:
        params = {
            "part": "snippet",
            "id": channel_id,
            "key": self.api_key,
        }
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{BASE_URL}/channels", params=params, timeout=15)
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail=resp.json())
            data = resp.json()

        items = data.get("items", [])
        if not items:
            raise HTTPException(status_code=404, detail=f"Channel '{channel_id}' not found")
        snippet = items[0]["snippet"]
        return {
            "channel_id": items[0]["id"],
            "title": snippet["title"],
            "description": snippet.get("description", ""),
        }

    async def _get_channel_by_handle(self, handle: str) -> dict:
        params = {
            "part": "snippet",
            "forHandle": handle,
            "key": self.api_key,
        }
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{BASE_URL}/channels", params=params, timeout=15)
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail=resp.json())
            data = resp.json()

        items = data.get("items", [])
        if not items:
            raise HTTPException(
                status_code=404,
                detail=f"Channel '@{handle}' not found",
            )
        snippet = items[0]["snippet"]
        return {
            "channel_id": items[0]["id"],
            "title": snippet["title"],
            "description": snippet.get("description", ""),
        }

    @staticmethod
    def _parse_duration_seconds(iso_duration: str) -> int:
        """Parse ISO 8601 duration string (e.g. PT1M30S) to total seconds."""
        pattern = r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?"
        match = re.match(pattern, iso_duration)
        if not match:
            return 0
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        return hours * 3600 + minutes * 60 + seconds

    async def _filter_regular_videos(
        self, client: httpx.AsyncClient, video_ids: List[str]
    ) -> List[str]:
        """
        Given a list of video IDs, return only those that are regular content videos:
        - Not a Short (duration > 60 seconds)
        - Not a live stream or premiere (liveStreamingDetails absent or liveBroadcastContent == 'none')
        """
        if not video_ids:
            return []

        # Batch in groups of 50 (API limit)
        regular_ids: List[str] = []
        for i in range(0, len(video_ids), 50):
            batch = video_ids[i : i + 50]
            params = {
                "part": "contentDetails,snippet",
                "id": ",".join(batch),
                "key": self.api_key,
            }
            resp = await client.get(f"{BASE_URL}/videos", params=params, timeout=30)
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail=resp.json())
            data = resp.json()

            for item in data.get("items", []):
                vid_id = item["id"]
                snippet = item.get("snippet", {})
                content_details = item.get("contentDetails", {})

                # Filter out live streams / premieres
                live_status = snippet.get("liveBroadcastContent", "none")
                if live_status in ("live", "upcoming"):
                    continue

                # Filter out Shorts (duration <= 60 seconds)
                duration_str = content_details.get("duration", "PT0S")
                duration_secs = self._parse_duration_seconds(duration_str)
                if duration_secs <= 60:
                    continue

                regular_ids.append(vid_id)

        return regular_ids

    async def get_channel_videos(
        self, channel_id: str, max_results: Optional[int] = None
    ) -> List[dict]:
        """
        Fetch regular content videos from a channel (excludes Shorts and live streams).
        If max_results is None, fetch all available videos.
        Returns: [{video_id, title, published_at}, ...]
        """
        search_params = {
            "part": "snippet",
            "channelId": channel_id,
            "type": "video",
            "order": "date",
            "maxResults": 50,  # max per page
            "key": self.api_key,
        }

        all_videos: List[dict] = []
        page_token: Optional[str] = None

        async with httpx.AsyncClient() as client:
            while True:
                if page_token:
                    search_params["pageToken"] = page_token

                resp = await client.get(
                    f"{BASE_URL}/search", params=search_params, timeout=30
                )
                if resp.status_code != 200:
                    raise HTTPException(
                        status_code=resp.status_code, detail=resp.json()
                    )
                data = resp.json()

                # Collect candidate videos (pre-filter live from search snippet)
                candidate_ids: List[str] = []
                candidate_meta: dict = {}
                for item in data.get("items", []):
                    vid = item.get("id", {}).get("videoId")
                    if not vid:
                        continue
                    snippet = item["snippet"]
                    # Quick pre-filter: skip ongoing/upcoming live streams
                    if snippet.get("liveBroadcastContent", "none") in ("live", "upcoming"):
                        continue
                    candidate_ids.append(vid)
                    candidate_meta[vid] = {
                        "title": snippet["title"],
                        "published_at": snippet["publishedAt"],
                    }

                # Deep-filter: remove Shorts and completed live streams by duration
                regular_ids = await self._filter_regular_videos(client, candidate_ids)

                for vid_id in regular_ids:
                    meta = candidate_meta[vid_id]
                    all_videos.append({
                        "video_id": vid_id,
                        "title": meta["title"],
                        "published_at": meta["published_at"],
                    })
                    if max_results is not None and len(all_videos) >= max_results:
                        break

                if max_results is not None and len(all_videos) >= max_results:
                    break

                page_token = data.get("nextPageToken")
                if not page_token:
                    break

        if max_results is not None:
            return all_videos[:max_results]
        return all_videos
