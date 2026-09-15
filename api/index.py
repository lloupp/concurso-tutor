"""Entry point for Vercel Python Functions."""
from backend.app.main import app
from backend.app.quest_api_routes import router as quest_api_router

# main.py monta o frontend estático em "/" por último. Para registrar novas
# rotas depois da importação sem deixá-las atrás desse catch-all, removemos o
# mount, incluímos o router administrativo e recolocamos o frontend no fim.
_front_routes = [route for route in app.router.routes if getattr(route, "name", None) == "front"]
if _front_routes:
    app.router.routes = [route for route in app.router.routes if route not in _front_routes]
app.include_router(quest_api_router)
app.router.routes.extend(_front_routes)

__all__ = ["app"]
