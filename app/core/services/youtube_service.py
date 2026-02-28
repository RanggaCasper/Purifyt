"""YouTube Data API v3 service: search videos and fetch comments."""

from datetime import datetime
from typing import List, Optional
import httpx
from fastapi import HTTPException

from app.config.settings import get_settings

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

    async def get_channel_videos(
        self, channel_id: str, max_results: Optional[int] = None
    ) -> List[dict]:
        """
        Fetch videos from a channel using the search endpoint.
        If max_results is None, fetch all available videos.
        Returns: [{video_id, title, published_at}, ...]
        """
        params = {
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
                if max_results is not None and len(all_videos) >= max_results:
                    break

                if page_token:
                    params["pageToken"] = page_token

                resp = await client.get(
                    f"{BASE_URL}/search", params=params, timeout=30
                )
                if resp.status_code != 200:
                    raise HTTPException(
                        status_code=resp.status_code, detail=resp.json()
                    )
                data = resp.json()

                for item in data.get("items", []):
                    vid = item.get("id", {}).get("videoId")
                    if not vid:
                        continue
                    snippet = item["snippet"]
                    all_videos.append({
                        "video_id": vid,
                        "title": snippet["title"],
                        "published_at": snippet["publishedAt"],
                    })

                page_token = data.get("nextPageToken")
                if not page_token:
                    break

        if max_results is not None:
            return all_videos[:max_results]
        return all_videos
