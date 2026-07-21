"""
Custom User model for the extracao_contabil project.
Must be defined BEFORE the first migration.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    """Custom user model extending Django's AbstractUser.

    This model is configured as AUTH_USER_MODEL in settings.py
    and MUST be defined before any migration is created.
    """

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"
        db_table = "usuarios"

    def __str__(self) -> str:
        return self.get_full_name() or self.username
