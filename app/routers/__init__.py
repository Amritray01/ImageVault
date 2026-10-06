from app.routers.images import router as images_router
from app.routers.tags import router as tags_router
from app.routers.stats import router as stats_router

__all__ = ["images_router", "tags_router", "stats_router"]
