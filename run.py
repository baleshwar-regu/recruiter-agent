import uvicorn
from config import VAPI_EXPOSE_PORT

if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app", 
        host="0.0.0.0", 
        port=VAPI_EXPOSE_PORT, 
        reload=True
    )