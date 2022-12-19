from django.core.management.base import BaseCommand, CommandError
from lousprime.models import Department, Section
from lousprime.views import update_departments
import requests
import datetime

class Command(BaseCommand):
    
    help = "Update all the departments and courses from the API"
    
    def handle(self, *args, **options):
        update_departments()
        return