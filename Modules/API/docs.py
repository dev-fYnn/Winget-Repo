import os

from fastapi import FastAPI, Request
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from fastapi.staticfiles import StaticFiles

from settings import BASE_DIR


def configure_offline_docs(api: FastAPI) -> None:
    static_directory = os.path.join(BASE_DIR, "static")
    api.mount("/docs-assets", StaticFiles(directory=static_directory), name="docs-assets")

    @api.get("/docs", include_in_schema=False)
    async def swagger_docs(request: Request):
        root_path = request.scope.get("root_path", "").rstrip("/")
        return get_swagger_ui_html(
            openapi_url=root_path + api.openapi_url,
            title=api.title + " - Swagger UI",
            swagger_js_url=root_path + "/docs-assets/api-docs/swagger-ui-bundle.js",
            swagger_css_url=root_path + "/docs-assets/api-docs/swagger-ui.css",
            swagger_favicon_url=root_path + "/docs-assets/images/favicon.png",
            oauth2_redirect_url=root_path + api.swagger_ui_oauth2_redirect_url,
            swagger_ui_parameters={"validatorUrl": None},
        )

    @api.get(api.swagger_ui_oauth2_redirect_url, include_in_schema=False)
    async def swagger_redirect():
        return get_swagger_ui_oauth2_redirect_html()

    @api.get("/redoc", include_in_schema=False)
    async def redoc_docs(request: Request):
        root_path = request.scope.get("root_path", "").rstrip("/")
        return get_redoc_html(
            openapi_url=root_path + api.openapi_url,
            title=api.title + " - ReDoc",
            redoc_js_url=root_path + "/docs-assets/api-docs/redoc.standalone.js",
            redoc_favicon_url=root_path + "/docs-assets/images/favicon.png",
            with_google_fonts=False,
        )
