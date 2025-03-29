import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "3001"))
    # Use the correct module path for the FastAPI app
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
