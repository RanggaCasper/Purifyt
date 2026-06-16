import uvicorn
import os

from app.main import app

def main() -> None:
    port = int(os.getenv("PURIFYT_BACKEND_PORT", "51441"))
    uvicorn.run(app, host="127.0.0.1", port=port)

if __name__ == "__main__":
    main()
