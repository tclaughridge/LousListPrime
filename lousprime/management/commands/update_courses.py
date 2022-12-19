from django.core.management.base import BaseCommand, CommandError
from lousprime.models import Department, Section
from lousprime.views import update_courses, convert_time
import requests
import datetime

class Command(BaseCommand):
    
    help = "Given department mnemonic, update course data from API"

    def add_arguments(self, parser):
        parser.add_argument('dept_name', type=str)
    
    def handle(self, *args, **options):
        dept_name = options['dept_name']
        update_courses(dept_name)
        return