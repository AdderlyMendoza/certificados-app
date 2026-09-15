"""Repositorios de plantillas y versiones."""
from __future__ import annotations

from app.models.template import Template, TemplateVersion
from app.repositories.base import BaseRepository


class TemplateRepository(BaseRepository[Template]):
    model = Template


class TemplateVersionRepository(BaseRepository[TemplateVersion]):
    model = TemplateVersion
