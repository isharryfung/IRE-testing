from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ire import __version__
from ire.config import config
from ire.models import GoldenRecord  # re-used existing models per POC guidance
from ire.service import IREService

from ire.api.full_demo_repository import FullDemoRepository
from ire.api.routes import (
    audit,
    dashboard,
    duplicates,
    golden_records,
    ingestion,
    manual_review,
    matching,
    matching_settings,
    source_records,
    source_systems,
    survivorship,
)


def create_app() -> FastAPI:
    app = FastAPI(title='Identity Resolution Engine - Full Stack POC', version=__version__)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

    for route_module in (
        dashboard,
        ingestion,
        golden_records,
        source_records,
        matching,
        manual_review,
        duplicates,
        matching_settings,
        survivorship,
        source_systems,
        audit,
    ):
        app.include_router(route_module.router)

    @app.on_event('startup')
    def startup() -> None:
        repo = FullDemoRepository(config=config)
        app.state.repo = repo
        app.state.service = IREService(repo, config)
        app.state.sample_models = [GoldenRecord(golden_id='demo-model-reference')]

    @app.get('/health')
    def health() -> dict:
        return {'status': 'ok', 'mode': config.IRE_MODE, 'version': __version__}

    return app


app = create_app()
