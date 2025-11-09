"""Main entry point for voice-api."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.middleware.gzip import GZipMiddleware
# from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

from voice_api.routers import health_router, twilio_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """This is the startup and shutdown code for the FastAPI application."""
    yield


app = FastAPI(
    title="Voice API", description="REST API for the Voice Agent", lifespan=lifespan
)

# app.add_middleware(HTTPSRedirectMiddleware)
# app.add_middleware(GZipMiddleware)
# app.add_middleware(CORSMiddleware)

app.include_router(health_router)
app.include_router(twilio_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
