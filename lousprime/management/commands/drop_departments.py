from django.core.management.base import BaseCommand, CommandError
from lousprime.models import Department, Section
import requests
import datetime

class Command(BaseCommand):
    
    help = "Delete all the departments and course data in the database"

    def handle(self, *args, **options):
        Department.objects.all().delete()
        return