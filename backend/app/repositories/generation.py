"""Repositorios de generaciones."""
from __future__ import annotations

from app.models.generation import Generation, GenerationItem
from app.repositories.base import BaseRepository


class GenerationRepository(BaseRepository[Generation]):
    model = Generation


class GenerationItemRepository(BaseRepository[GenerationItem]):
    model = GenerationItem
