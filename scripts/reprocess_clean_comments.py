import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db.connection import AsyncSessionLocal
from app.db.repositories.comment_repository import CommentRepository


async def main():
    print("Starting reprocess of clean_comment for existing data...")
    async with AsyncSessionLocal() as session:
        repo = CommentRepository(session)
        total = await repo.reprocess_clean_comments(batch_size=500)
        await session.commit()
    print(f"Done. {total} comment(s) updated.")


if __name__ == "__main__":
    asyncio.run(main())
