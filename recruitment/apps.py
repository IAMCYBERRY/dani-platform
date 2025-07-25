"""
Django app configuration for recruitment.
"""

from django.apps import AppConfig


class RecruitmentConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'recruitment'
    verbose_name = 'Recruitment & ATS'