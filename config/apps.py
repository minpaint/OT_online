# config/apps.py

from django.contrib.admin.apps import AdminConfig

class OTAdminConfig(AdminConfig):
    default_site = 'config.admin_site.OTAdminSite'
