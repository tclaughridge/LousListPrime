import email
from urllib import response
from django.utils import timezone
from django.test import TestCase
from django.shortcuts import reverse
from allauth.utils import get_user_model
from django.contrib.auth.models import User
from allauth.account import app_settings as account_settings
from allauth.account.models import EmailAddress
from allauth.account.utils import user_email
from allauth.socialaccount.helpers import complete_social_login
from allauth.socialaccount.models import SocialApp, SocialAccount, SocialLogin
from django.test.client import RequestFactory
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from lousprime.models import Department, Section, Schedule
import requests
from lousprime.views import *

class ClassSearchTest(TestCase):
    
    names=["subject", "catalog_number", "component", "instructor", "facility_description", "days", "units", "time",
     "description", "topic", "min_limit", "max_limit", "min_enrollment", "max_enrollment", "min_waitlist", "max_waitlist"]
    
    def setUp(self):
        url = 'http://luthers-list.herokuapp.com/api/deptlist/?format=json'
        response = requests.get(url)
        dept_data = response.json()

        counter=0
        # add the first 50 departments to the test database
        for dept in dept_data:
            if(counter==50):
                break
            department_mnemonic = dept['subject']
            update_courses(department_mnemonic)
            counter+=1

    def search_default(self):
        json=dict.fromkeys(self.names, "")

        # test default search for all courses
        results=filter_courses(json)
        depts=Department.objects.all()
        self.assertTrue(len(results)!=0)
        number_of_sections=0
        checked_all_sections=False
        self.assertEquals(len(depts), 50)
        for dept in depts:
            isPrefix=False
            for courses in results:
                if(dept.mnemonic in courses):
                    isPrefix=True
                if(not checked_all_sections):
                    number_of_sections+=len(results[courses])
            checked_all_sections=True
            self.assertTrue(isPrefix)
        # verify you are getting all of the sections from the DB
        self.assertEquals(number_of_sections, len(Section.objects.all()))

        # test search by department
    def search_by_department(self):
        json=dict.fromkeys(self.names, "")
        json["subject"]="CS"
        results=filter_courses(json)
        self.assertTrue(len(results)!=0)
        for courses in results:
            self.assertTrue("CS" in courses)
        self.assertTrue("CS1110" in results)
        self.assertTrue("CS2100" in results)
        self.assertTrue("CS2150" in results)
        self.assertTrue("CS3330" in results)
        self.assertTrue("CS3100" in results)
        self.assertTrue("CS3240" in results)

        # test for department that doesn't exist
        json=dict.fromkeys(self.names, "")
        json["subject"]="XYZ"
        results=filter_courses(json)
        self.assertEquals(len(results), 0)

    def search_by_course(self):
        # test search by course
        json=dict.fromkeys(self.names, "")
        json["subject"]="CS"
        json["catalog_number"]="3240"
        results=filter_courses(json)
        self.assertTrue(len(results)!=0)
        self.assertEquals(len(results), 1)
        self.assertTrue("CS3240" in results)
        self.assertEquals(len(results["CS3240"]), 3)
        self.assertTrue(results["CS3240"][0].section_component=="LEC" and results["CS3240"][1].section_component=="LEC" and
        results["CS3240"][2].section_component=="LAB")
        self.assertTrue(results["CS3240"][0].section_instructor=="Paul McBurney" and 
        results["CS3240"][1].section_instructor=="Mark Sherriff")
        self.assertTrue(results["CS3240"][0].section_meetings=="TuTh,03:30PM-04:45PM,Rice Hall 130" and 
        results["CS3240"][1].section_meetings=="TuTh,09:30AM-10:45AM,Rice Hall 130")
        self.assertTrue(results["CS3240"][0].section_credits=="3" and 
        results["CS3240"][1].section_credits=="3")

        # test for course that doesn't exist
        json=dict.fromkeys(self.names, "")
        json["subject"]="CS"
        json["catalog_number"]="3241"
        results=filter_courses(json)
        self.assertEquals(len(results), 0)

        # test for catalog prefix
        json=dict.fromkeys(self.names, "")
        json["subject"]="CS"
        json["catalog_number"]="324"
        results=filter_courses(json)
        self.assertEquals(len(results), 1)
        self.assertTrue("CS3240" in results)
        self.assertEquals(len(results["CS3240"]), 3)
        self.assertTrue(results["CS3240"][0].section_component=="LEC" and results["CS3240"][1].section_component=="LEC" and
        results["CS3240"][2].section_component=="LAB")
        self.assertTrue(results["CS3240"][0].section_instructor=="Paul McBurney" and 
        results["CS3240"][1].section_instructor=="Mark Sherriff")
        self.assertTrue(results["CS3240"][0].section_meetings=="TuTh,03:30PM-04:45PM,Rice Hall 130" and 
        results["CS3240"][1].section_meetings=="TuTh,09:30AM-10:45AM,Rice Hall 130")
        self.assertTrue(results["CS3240"][0].section_credits=="3" and 
        results["CS3240"][1].section_credits=="3")

    def search_by_location(self):
        # test search by location
        json=dict.fromkeys(self.names, "")
        json["facility_description"]="Thornton Hall A120"
        results=filter_courses(json)
        self.assertTrue(len(results)!=0)
        self.assertTrue("ECE2630" in results)
        self.assertTrue("ECE3209" in results)
        self.assertTrue("ECE3430" in results)
        self.assertTrue("ECE3750" in results)
        self.assertTrue("ECE4440" in results)
        self.assertTrue("ECE4991" in results)

        # test for location that does not exist
        json=dict.fromkeys(self.names, "")
        json["facility_description"]="Thorton Hall A120"
        results=filter_courses(json)
        self.assertEquals(len(results), 0)

        # test for location prefix
        json=dict.fromkeys(self.names, "")
        json["facility_description"]="Thornton Hall"
        results=filter_courses(json)
        self.assertTrue(len(results)!=0)
        self.assertTrue("ECE2630" in results)
        self.assertTrue("ECE3209" in results)
        self.assertTrue("ECE3430" in results)
        self.assertTrue("ECE3750" in results)
        self.assertTrue("ECE4440" in results)
        self.assertTrue("ECE4991" in results)
        self.assertTrue("ECE4209" in results)
        self.assertTrue("ECE3501" in results)

    def search_by_instructor(self):
        # test for instructor
        json=dict.fromkeys(self.names, "")
        json["instructor"]="Nada Basit"
        results=filter_courses(json)
        self.assertTrue(len(results)!=0)
        self.assertTrue("CS2100" in results)
        self.assertTrue("CS2910" in results)

        # test for instructor that does not exist
        json=dict.fromkeys(self.names, "")
        json["instructor"]="Kidus Fasil"
        results=filter_courses(json)
        self.assertEquals(len(results), 0)

        # test for instructor prefix
        json=dict.fromkeys(self.names, "")
        json["instructor"]="Basit"
        results=filter_courses(json)
        self.assertTrue(len(results)!=0)
        self.assertTrue("CS2100" in results)
        self.assertTrue("CS2910" in results)

    def search_by_credits(self):
        # test number of credits
        json=dict.fromkeys(self.names, "")
        json["units"]="4.5"
        results=filter_courses(json)
        self.assertTrue(len(results)!=0)
        self.assertEquals(len(results), 2)
        self.assertTrue("ECE4440" in results)
        self.assertTrue("ECE4991" in results)

        # test number of credits that does not exist
        json=dict.fromkeys(self.names, "")
        json["units"]="100"
        results=filter_courses(json)
        self.assertEquals(len(results), 0)

        # test for credits prefix
        json=dict.fromkeys(self.names, "")
        json["units"]="4."
        results=filter_courses(json)
        self.assertTrue(len(results)!=0)
        self.assertEquals(len(results), 2)
        self.assertTrue("ECE4440" in results)
        self.assertTrue("ECE4991" in results)
        json["units"]=".5"
        results=filter_courses(json)
        self.assertTrue(len(results)!=0)

    def search_by_day(self):
        # test search by day
        json=dict.fromkeys(self.names, "")
        json["days"]="MoWeFr"
        results=filter_courses(json)
        self.assertTrue(len(results)!=0)
        json["days"]="TuTh"
        results=filter_courses(json)
        self.assertTrue(len(results)!=0)

        # test day that does not exist
        json=dict.fromkeys(self.names, "")
        json["days"]="Zeb"
        results=filter_courses(json)
        self.assertTrue(len(results)==0)

        # test for a prefix of a day
        json["days"]="TuT"
        results=filter_courses(json)
        self.assertTrue(len(results)!=0)
        json["days"]="T"
        results=filter_courses(json)
        self.assertTrue(len(results)!=0)

        # test that there are a different number of sections for TuTh than Tu and Th separate
        json["days"]="TuTh"
        results=filter_courses(json)
        self.assertTrue(len(results)!=0)
        json["days"]="Tu"
        results2=filter_courses(json)
        self.assertTrue(len(results)!=0)
        json["days"]="Th"
        results3=filter_courses(json)
        self.assertTrue(len(results)!=0)
        self.assertTrue(results!=results2 and results2!=results3 and results!=results3)

    def search_by_time(self):
        json=dict.fromkeys(self.names, "")
        # test search by time
        
        json["time"]="1:00 PM - 1:50 PM"
        times=json["time"].split("-")
        start_time = times[0].strip()
        end_time = times[1].strip()
        json["time"]=parse_time_input(start_time)+"-"+parse_time_input(end_time)
        results=filter_courses(json)
        self.assertTrue(len(results)!=0)

        # test search by time (again)
        json["time"]="09:30 AM - 12:15 PM"
        times=json["time"].split("-")
        start_time = times[0].strip()
        end_time = times[1].strip()
        json["time"]=parse_time_input(start_time)+"-"+parse_time_input(end_time)
        results=filter_courses(json)
        self.assertTrue(len(results)!=0)
        self.assertEquals(len(results), 1)
        self.assertTrue("ECE3750" in results)

         # test start time
        json["time"]="1:00PM"
        results=filter_courses(json)
        self.assertTrue(len(results)!=0)

        # test end time
        json["time"]="1:50PM"
        results=filter_courses(json)
        self.assertTrue(len(results)!=0)

        # test time prefix
        json["time"]="1:"
        results=filter_courses(json)
        self.assertTrue(len(results)!=0)
        json["time"]="1:00"
        results=filter_courses(json)
        self.assertTrue(len(results)!=0)
        json["time"]="1:50"
        results=filter_courses(json)
        self.assertTrue(len(results)!=0)

        # test that start time results does not equal end time results
        json["time"]="1:00PM"
        results=filter_courses(json)
        self.assertTrue(len(results)!=0)
        json["time"]="1:50PM"
        results2=filter_courses(json)
        self.assertTrue(len(results2)!=0)
        self.assertTrue(results!=results2)

        # test for time that does not exist
        json["time"]="12:00 AM"
        results=filter_courses(json)
        self.assertTrue(len(results)==0)

    def search_by_topic(self):
        # test search by topic
        json=dict.fromkeys(self.names, "")
        json["topic"]="Statistical Learning and Graphical Models"
        results=filter_courses(json)
        self.assertTrue(len(results)!=0)
        self.assertEquals(len(results), 4)
        self.assertTrue("CS4501" in results)
        self.assertTrue("CS6501" in results)
        self.assertTrue("ECE4502" in results)
        self.assertTrue("ECE6502" in results)

        # test for topic that does not exist
        json["topic"]="Pancake Flipping"
        results=filter_courses(json)
        self.assertTrue(len(results)==0)

        # test for topic prefix
        json["topic"]="Statistical Learning"
        results=filter_courses(json)
        self.assertTrue(len(results)!=0)
        self.assertEquals(len(results), 4)
        self.assertTrue("CS4501" in results)
        self.assertTrue("CS6501" in results)
        self.assertTrue("ECE4502" in results)
        self.assertTrue("ECE6502" in results)
    
    # checks if the lower bound for enrollment/limit is satisifed
    def greater_than(self, courses, limit, option):
        for course in courses:
            for section in courses[course]:
                if(option=="capacity"):
                    self.assertTrue(int(section.section_enrollment_capacity)>=limit)
                else:
                    self.assertTrue(int(section.section_enrollment_total)>=limit)  

    # checks if the upper bound for enrollment/limit is satisifed
    def less_than(self, courses, limit, option):
        for course in courses:
            for section in courses[course]:
                if(option=="capacity"):
                    self.assertTrue(int(section.section_enrollment_capacity)<=limit)
                else:
                    self.assertTrue(int(section.section_enrollment_total)<=limit)

    # checks if the lower bound and upper bound for enrollment/limit is satisifed
    def between(self, courses, lower, upper, option):
        for course in courses:
            for section in courses[course]:
                if(option=="capacity"):
                    self.assertTrue(int(section.section_enrollment_capacity)>=lower and int(section.section_enrollment_capacity)<=upper)
                else:
                    self.assertTrue(int(section.section_enrollment_total)>=lower and int(section.section_enrollment_total)<=upper)

    def search_by_enrollment(self):
        
        # test search for minimum enrollment
        json=dict.fromkeys(self.names, "")
        json["min_enrollment"]="100"
        results=filter_courses(json)
        self.assertTrue(len(results)!=0)
        self.greater_than(results, 100, "total")

        # test for maximum enrollment
        json=dict.fromkeys(self.names, "")
        json["max_enrollment"]="100"
        results=filter_courses(json)
        self.assertTrue(len(results)!=0)
        self.less_than(results, 100, "total")

        # test within a range for min and max enrollment
        json["min_enrollment"]="100"
        json["max_enrollment"]="200"
        results=filter_courses(json)
        self.assertTrue(len(results)!=0)
        self.between(results, 100, 200, "total")

        # test an invalid range for min and max enrollment
        json["min_enrollment"]="200"
        json["max_enrollment"]="100"
        results=filter_courses(json)
        self.assertTrue(len(results)==0)

        # test a tight bound for enrollment
        json["min_enrollment"]="100"
        json["max_enrollment"]="100"
        results=filter_courses(json)
        self.assertTrue(len(results)!=0)
        self.between(results, 100, 100, "total")
       
        # test for minimum limit
        json=dict.fromkeys(self.names, "")
        json["min_limit"]="100"
        results=filter_courses(json)
        self.assertTrue(len(results)!=0)
        self.greater_than(results, 100, "capacity")

        # test search for minimum limit (again)
        json=dict.fromkeys(self.names, "")
        json["min_limit"]="800"
        results=filter_courses(json)
        self.assertTrue(len(results)!=0)
        self.assertEquals(len(results), 2)
        self.assertTrue("COMM2010" in results)
        self.assertTrue("COMM2020" in results)
        self.greater_than(results, 800, "capacity")

        # test for maximum limit
        json=dict.fromkeys(self.names, "")
        json["max_limit"]="100"
        results=filter_courses(json)
        self.assertTrue(len(results)!=0)
        self.less_than(results, 100, "capacity")
        

        # test within a range for min and max enrollment
        json["min_limit"]="100"
        json["max_limit"]="200"
        results=filter_courses(json)
        self.assertTrue(len(results)!=0)
        self.between(results, 100, 200, "capacity")

        # test an invalid range for min and max enrollment
        json["min_limit"]="200"
        json["max_limit"]="100"
        results=filter_courses(json)
        self.assertTrue(len(results)==0)
        

        # test a tight bound for enrollment
        json["min_limit"]="100"
        json["max_limit"]="100"
        results=filter_courses(json)
        self.assertTrue(len(results)!=0)
        self.between(results, 100, 100, "capacity")
    
    def search_by_title(self):
         # test search by class title
        json=dict.fromkeys(self.names, "")
        json["description"]="Introduction to Programming"
        results=filter_courses(json)
        self.assertTrue(len(results)!=0)
        self.assertEquals(len(results), 3)
        self.assertTrue("CS1110" in results)
        self.assertTrue("CS1111" in results)
        self.assertTrue("CS1112" in results)

        # test for topic that does not exist
        json["description"]="Crocodile Wrestling"
        results=filter_courses(json)
        self.assertTrue(len(results)==0)

        # test for topic prefix
        json["description"]="to Programming"
        results=filter_courses(json)
        self.assertTrue(len(results)!=0)
        self.assertEquals(len(results), 3)
        self.assertTrue("CS1110" in results)
        self.assertTrue("CS1111" in results)
        self.assertTrue("CS1112" in results)

    
    def search_combined_test(self):
        # test department, course, and meeting time
        json=dict.fromkeys(self.names, "")
        json["subject"]="apm"
        json["catalog_number"]="310"
        json["time"]="12:00 PM - 12:50 PM"
        times=json["time"].split("-")
        start_time = times[0].strip()
        end_time = times[1].strip()
        json["time"]=parse_time_input(start_time)+"-"+parse_time_input(end_time)
        results=filter_courses(json)
        self.assertTrue(len(results)!=0)
        self.assertEquals(len(results), 1)
        self.assertTrue("APMA3100" in results)
        self.assertEquals(len(results["APMA3100"]), 3)
        for courses in results:
            self.assertTrue("APMA" in courses)
        
        # test with location added
        json["facility_description"]="Olsson Hall"
        results=filter_courses(json)
        self.assertTrue(len(results)!=0)
        self.assertEquals(len(results), 1)
        self.assertTrue("APMA3100" in results)
        self.assertEquals(len(results["APMA3100"]), 2)

        # test with instructor added
        json["instructor"]="Hui Ma"
        results=filter_courses(json)
        self.assertTrue(len(results)!=0)
        self.assertEquals(len(results), 1)
        self.assertTrue("APMA3100" in results)
        self.assertEquals(len(results["APMA3100"]), 1)

        # test with invalid meeting days
        json["instructor"]=""
        json["facility_description"]=""
        json["time"]=""
        json["days"]="TuTh"
        results=filter_courses(json)
        self.assertTrue(len(results)==0)

        # test with location and day
        json=dict.fromkeys(self.names, "")
        json["facility_description"]="Olsson Hall 018"
        json["days"]="Th"
        results=filter_courses(json)
        self.assertEquals(len(results), 2)
        self.assertTrue("CS1110" in results)

        # add invalid time
        json["time"]="8:00 AM - 9:15 AM"
        times=json["time"].split("-")
        start_time = times[0].strip()
        end_time = times[1].strip()
        json["time"]=parse_time_input(start_time)+"-"+parse_time_input(end_time)
        results=filter_courses(json)
        self.assertTrue(len(results)==0)


        # test instructor and topic
        json=dict.fromkeys(self.names, "")
        json["instructor"]="Aaron Bloomfield"
        json["topic"]="Cryptocurrency"
        results=filter_courses(json)
        self.assertTrue(len(results)!=0)
        self.assertEquals(len(results), 1)

        # test department and number of credits
        json=dict.fromkeys(self.names, "")
        json["subject"]="APMA"
        json["units"]="3"
        results=filter_courses(json)
        self.assertTrue(len(results)!=0)
        self.assertEquals(len(results), 7)
        for courses in results:
            self.assertTrue("APMA" in courses)

        # department and min limit
        json=dict.fromkeys(self.names, "")
        json["subject"]="ECE"
        json["min_limit"]="80"
        results=filter_courses(json)
        self.assertTrue(len(results)!=0)
        self.assertEquals(len(results), 4)
        for courses in results:
            self.assertTrue("ECE" in courses)

    # dummy driver function to prevent the test database to keep recreating itself 
    def test_class_search(self):
        self.search_default()
        self.search_by_department()
        self.search_by_course()
        self.search_by_location()
        self.search_by_instructor()
        self.search_by_credits()
        self.search_by_day()
        self.search_by_time()
        self.search_by_topic()
        self.search_by_enrollment()
        self.search_by_title()
        self.search_combined_test()


    def test_search_URL(self):
        response = self.client.get('/search/', follow=True)
        # verify that the base url will send out a 200 HTTP status code
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "lousprime/search.html")

    def test_results_URL(self):
        response = self.client.get('/search/results/', follow=True)
        # verify that the base url will send out a 200 HTTP status code
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "lousprime/search.html")
        

class APITest(TestCase):

    @classmethod
    def setUpClass(cls):
        super(APITest, cls).setUpClass()
        url = 'http://luthers-list.herokuapp.com/api/deptlist/?format=json'
        response = requests.get(url)
        dept_data = response.json()

        counter=0
        # add the first 50 departments to the test database
        for dept in dept_data:
            if(counter==50):
                break
            department_mnemonic = dept['subject']
            update_courses(department_mnemonic)
            counter+=1

    def test_browse_URL(self):
        response = self.client.get('/browse/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "lousprime/browse.html")

    def test_department_URLs(self):
        department = Department.objects.all()
        for dept in department:
            response = self.client.get(f'/browse/{dept.mnemonic}/', follow=True)
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, "lousprime/course.html")
    
    def test_time_parsing(self):
        meetings = [
            {
                "days": "MoWe",
                "start_time": "17.00.00.000000-05:00",
                "end_time": "18.15.00.000000-05:00",
                "facility_description": "Olsson Hall 009"
            },
            {
                "days": "TuTh",
                "start_time": "14.00.00.000000-05:00",
                "end_time": "14.50.00.000000-05:00",
                "facility_description": "John W. Warner Hall 209"
            }
        ]
        meeting_representation = meeting_to_string(meetings)
        self.assertEqual(meeting_representation, "MoWe,05:00PM-06:15PM,Olsson Hall 009;TuTh,02:00PM-02:50PM,John W. Warner Hall 209")

    def test_convert_time(self):
        time = "17.30.00.000000-05:00"
        converted = convert_time(time)
        self.assertEquals(converted, "05:30PM")
    
    def test_convert_time_empty(self):
        time = ""
        converted = convert_time(time)
        self.assertEquals(converted, "")
    
    def test_updated(self):
        self.assertEquals(len(Section.objects.all()), len(Section.objects.filter(update_status=True))) 

class AccountTest(TestCase):
    """
    Source: Django All-Auth Tests
    URL: https://github.com/pennersr/django-allauth/blob/master/allauth/socialaccount/tests.py
    Author: Raymond Penners and many others
    (This is only for the create_user function)
    """
    def create_user(self, email, username, id):
        # create a request factory to store requests for testing
        factory = RequestFactory()
        # url that gets called when logging in
        callback_url='/accounts/google/login/callback/'
        # get the request that calls the callback url
        request = factory.get(callback_url)
        User = get_user_model()
        user = User()
        # set up a session
        SessionMiddleware(lambda request: None).process_request(request)
        MessageMiddleware(lambda request: None).process_request(request)
        # define the user's email and username
        setattr(user, account_settings.USER_MODEL_USERNAME_FIELD, username)
        setattr(user, account_settings.USER_MODEL_EMAIL_FIELD, email)
        # create an account
        account = SocialAccount(user=user, provider='google', uid=id)
        # login to the account
        sociallogin = SocialLogin(account=account, user=user)
        request.user=user
        complete_social_login(request=request, sociallogin=sociallogin)


    def test_URL(self):
        response = self.client.get('/', follow=True)
        # verify that the base url will send out a 200 HTTP status code
        self.assertEqual(response.status_code, 200)
        # verfiy that the template rendered is index.html
        self.assertTemplateUsed(response, "lousprime/home.html")


    def test_AccountsURL(self):
        response = self.client.get('/accounts/google/login/', follow=True)
        # verify that the accounts url will send out a 200 HTTP status code
        self.assertEqual(response.status_code, 200)


    def test_CreateAccount(self):
        callback_url='/accounts/google/login/callback/'
        # list of users
        users=["bob", "test", "lous", "abc", "micheal", "jane"]
        i=1
        # create an account for each user in the list
        for user in users:
            self.create_user(email=user+"@gmail.com", username=user, id=i)
            i+=1
        # verify the models aren't empty
        self.assertEqual(len(SocialAccount.objects.all()), len(users))
        self.assertEqual(len(EmailAddress.objects.all()), len(users))
        i=0
        # verify that you can query all of the users
        for keys in SocialAccount.objects.all():
            user = User.objects.get(
                **{account_settings.USER_MODEL_USERNAME_FIELD: users[i]}
            )
            self.assertTrue(
                SocialAccount.objects.filter(user=user, uid=keys.uid).exists()
            )

            self.assertTrue(
                EmailAddress.objects.filter(user=user,
                                            email=user_email(user)).exists()
            )
            i+=1
        response=self.client.get(callback_url, follow=True)
        # verify that the callback url will send out a 200 HTTP status code
        self.assertEqual(response.status_code, 200)


    # this might need to be expanded upon
    def test_Logout(self):
        logout_url=reverse("lousprime:logout")
        response=self.client.get(logout_url, follow=True)
        # verify it redirected to the index page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "lousprime/home.html")


class ScheduleTest(TestCase):

    """
    Source: Django All-Auth Tests
    URL: https://github.com/pennersr/django-allauth/blob/master/allauth/socialaccount/tests.py
    Author: Raymond Penners and many others
    (This is only for the create_user function) to use for creating user in other test cases
    """
    def create_user(self, email, username, id):
        # create a request factory to store requests for testing
        factory = RequestFactory()
        # url that gets called when logging in
        callback_url='/accounts/google/login/callback/'
        # get the request that calls the callback url
        request = factory.get(callback_url)
        User = get_user_model()
        user = User()
        # set up a session
        SessionMiddleware(lambda request: None).process_request(request)
        MessageMiddleware(lambda request: None).process_request(request)
        # define the user's email and username
        setattr(user, account_settings.USER_MODEL_USERNAME_FIELD, username)
        setattr(user, account_settings.USER_MODEL_EMAIL_FIELD, email)
        # create an account
        account = SocialAccount(user=user, provider='google', uid=id)
        # login to the account
        sociallogin = SocialLogin(account=account, user=user)
        request.user=user
        complete_social_login(request=request, sociallogin=sociallogin)

    def addSection(self, schedule, sect_code):
        section = Section.objects.get(section_code=sect_code)
        for sectionCheck in schedule.sections.all():
            if(section.course_number == sectionCheck.course_number and section.section_component == sectionCheck.section_component):
                return "Error: Course already joined!"
        schedule.sections.add(section)
        try:
            schedule.credits = schedule.credits + int(section.section_credits)
        except(ValueError):
            schedule.credits = schedule.credits + 1
        schedule.save()
        if(schedule.credits > 18):
            return "Error: Too many credits!"
        return "Class successfully added!"

    def remSection(self, schedule, sect_code):
        section = Section.objects.get(section_code=sect_code)
        schedule.sections.remove(section)
        try:
            schedule.credits = schedule.credits - int(section.section_credits)
        except(ValueError):
            schedule.credits = schedule.credits - 1
        schedule.save()
        return "Class successfully removed!"

    def setUp(self):
        self.factory = RequestFactory()
        socialAccount = self.create_user(email="jeff@gmail.com", username="jeff", id=1)
        User = get_user_model()
        self.user = User.objects.get(username="jeff", email="jeff@gmail.com")

        url = 'http://luthers-list.herokuapp.com/api/deptlist/?format=json'
        response = requests.get(url)
        dept_data = response.json()
        counter=0
        # add the first 50 departments to the test database
        for dept in dept_data:
            if(counter==50):
                break
            department_mnemonic = dept['subject']
            update_courses(department_mnemonic)
            counter+=1
        
        Schedule.objects.create(schedule_name="jeff's schedule", user_account=socialAccount, credits=0, user_account_id=1)

    def test_NewAccountEmptySchedule(self):
        user = "bob"
        newAccount = self.create_user(email=user + "@gmail.com", username=user, id=2)
        newSchedule = Schedule.objects.create(schedule_name="bob's schedule", user_account=newAccount, credits=0, user_account_id=2)

        # verify that new account starts with an empty schedule
        self.assertEqual(len(newSchedule.sections.all()), 0)
        # verify that the new schedule has 0 credits
        self.assertEqual(newSchedule.credits, 0)

    def test_AddCourse(self):
        section1110 = Section.objects.get(section_code="16003")
        section2100 = Section.objects.get(section_code="19685")
        schedule = Schedule.objects.get(user_account_id=1)
        ogLength = len(schedule.sections.all())
        ogCredits = schedule.credits

        # add CS 1110
        self.assertEqual(self.addSection(schedule=schedule, sect_code="16003"), "Class successfully added!")
        # verify that an addition has been made to the number of sections in the schedule
        self.assertEqual(len(schedule.sections.all()), int(ogLength + 1))
        # verify that correct course is added to the schedule
        self.assertTrue(section1110 in schedule.sections.all())
        # verify that the schedule credits increase by the correct amount
        self.assertEqual(schedule.credits, ogCredits + int(section1110.section_credits))

        ogLength = len(schedule.sections.all())
        ogCredits = schedule.credits
        # add CS 2100 lab
        self.assertEqual(self.addSection(schedule=schedule, sect_code="19685"), "Class successfully added!")
        # verify that an addition has been made to the number of sections in the schedule
        self.assertEqual(len(schedule.sections.all()), int(ogLength + 1))
        # verify that the correct course is added to the schedule
        self.assertTrue(section2100 in schedule.sections.all())
        # verify that the schedule credits increase by the correct amount
        self.assertEqual(schedule.credits, ogCredits + int(section2100.section_credits))
    
    def test_AddDuplicateCourse(self):
        section1110 = Section.objects.get(section_code="16003")
        section2100 = Section.objects.get(section_code="19685")
        schedule = Schedule.objects.get(user_account_id=1)
        if section1110 not in schedule.sections.all():
            schedule.sections.add(section1110)
            schedule.credits = schedule.credits + int(section1110.section_credits)
        if section2100 not in schedule.sections.all():
            schedule.sections.add(section2100)
            schedule.credits = schedule.credits + int(section2100.section_credits)
        ogLength = len(schedule.sections.all())
        
        # add CS 1110
        self.assertEqual(self.addSection(schedule=schedule, sect_code="16003"), "Error: Course already joined!")
        # verify that adding a duplicate course does not increase the number of sections in the schedule
        self.assertEqual(ogLength, len(schedule.sections.all()))
        # verify that there is only one instance of CS 1110 in the schedule
        count1110 = 0
        for section in schedule.sections.all():
            if section == section1110:
                count1110 += 1
        self.assertEqual(count1110, 1)

        # add CS 2100 lab
        self.assertEqual(self.addSection(schedule=schedule, sect_code="19685"), "Error: Course already joined!")
        # verify that adding a duplicate course does not increase the number of sections in the schedule
        self.assertEqual(ogLength, len(schedule.sections.all()))
        # verify that there is only one instance of CS 2100 in the schedule
        count2100 = 0
        for section in schedule.sections.all():
            if section == section2100:
                count2100 += 1
        self.assertEqual(count2100, 1)
    
    def test_TooManyCredits(self):
        section1110 = Section.objects.get(section_code="16003")
        section2100 = Section.objects.get(section_code="18789")
        section2150 = Section.objects.get(section_code="15567")
        section3240 = Section.objects.get(section_code="15991")
        section3330 = Section.objects.get(section_code="16258")
        section4750 = Section.objects.get(section_code="16189")
        section4774 = Section.objects.get(section_code="16618")
        schedule = Schedule.objects.get(user_account_id=1)

        if section1110 not in schedule.sections.all():
            schedule.sections.add(section1110)
            schedule.credits = schedule.credits + int(section1110.section_credits)
        if section2100 not in schedule.sections.all():
            schedule.sections.add(section2100)
            schedule.credits = schedule.credits + int(section2100.section_credits)
        if section2150 not in schedule.sections.all():
            schedule.sections.add(section2150)
            schedule.credits = schedule.credits + int(section2150.section_credits)
        if section3240 not in schedule.sections.all():
            schedule.sections.add(section3240)
            schedule.credits = schedule.credits + int(section3240.section_credits)
        if section3330 not in schedule.sections.all():
            schedule.sections.add(section3330)
            schedule.credits = schedule.credits + int(section3330.section_credits)
        if section4750 not in schedule.sections.all():
            schedule.sections.add(section4750)
            schedule.credits = schedule.credits + int(section4750.section_credits)
        
        ogLength = len(schedule.sections.all())
        ogCredits = schedule.credits

        # add CS 4774 to schedule with 18 credits
        # verify there is a schedule credit warning
        self.assertEqual(self.addSection(schedule=schedule, sect_code="16618"), "Error: Too many credits!")
        # verify that an addition has been made to the number of sections in the schedule
        self.assertEqual(len(schedule.sections.all()), int(ogLength + 1))
        # verify that correct course is added to the schedule
        self.assertTrue(section4774 in schedule.sections.all())
        # verify that the schedule credits increase by the correct amount
        self.assertEqual(schedule.credits, ogCredits + int(section4774.section_credits))


    def test_RemoveCourse(self):
        section1110 = Section.objects.get(section_code="16003")
        section2100 = Section.objects.get(section_code="19685")
        schedule = Schedule.objects.get(user_account_id=1)
        if section1110 not in schedule.sections.all():
            schedule.sections.add(section1110)
            schedule.credits = schedule.credits + int(section1110.section_credits)
        if section2100 not in schedule.sections.all():
            schedule.sections.add(section2100)
            schedule.credits = schedule.credits + int(section2100.section_credits)
        ogLength = len(schedule.sections.all())
        ogCredits = schedule.credits

        # remove CS 1110
        self.assertEqual(self.remSection(schedule=schedule, sect_code="16003"), "Class successfully removed!")
        # verify that the number of sections in the schedule decreases by 1
        self.assertEqual(len(schedule.sections.all()), int(ogLength - 1))
        # verify that CS 1110 is not in the schedule
        self.assertFalse(section1110 in schedule.sections.all())
        # verify that the schedule credits decreases by CS 1110 credits
        self.assertEqual(schedule.credits, ogCredits - int(section1110.section_credits))

        ogLength = len(schedule.sections.all())
        ogCredits = schedule.credits
        # remove CS 2100 lab
        self.assertEqual(self.remSection(schedule=schedule, sect_code="19685"), "Class successfully removed!")
        # verify that the number of sections in the schedule decreases by 1
        self.assertEqual(len(schedule.sections.all()), int(ogLength - 1))
        # verify that CS 2100 is not in the schedule
        self.assertFalse(section2100 in schedule.sections.all())
        # verify that the schedule credits decreases by CS 2100 credits
        self.assertEqual(schedule.credits, ogCredits - int(section2100.section_credits))
    
    def test_ScheduleURL(self):
        request = self.factory.get('')
        request.user = self.user
        response = schedule(request=request, user=request.user)
        # verify that the schedule URL will send a 200 HTTP status code
        self.assertEqual(response.status_code, 200)

    def test_AddURL(self):
        sect_code = "16003"
        request = self.factory.get('')
        request.user = self.user
        section1110 = Section.objects.get(section_code="16003")
        schedule = Schedule.objects.get(user_account_id=1)
        
        response = add_section(request, sect_code)
        # verify that the add URL sends a 200 HTTP status code if course is successfully added
        self.assertEqual(response.status_code, 200)

        section2100 = Section.objects.get(section_code="18789")
        section2150 = Section.objects.get(section_code="15567")
        section3240 = Section.objects.get(section_code="15991")
        section3330 = Section.objects.get(section_code="16258")
        section4750 = Section.objects.get(section_code="16189")
        section4774 = Section.objects.get(section_code="16618")

        if section1110 not in schedule.sections.all():
            schedule.sections.add(section1110)
            schedule.credits = schedule.credits + int(section1110.section_credits)
        if section2100 not in schedule.sections.all():
            schedule.sections.add(section2100)
            schedule.credits = schedule.credits + int(section2100.section_credits)
        if section2150 not in schedule.sections.all():
            schedule.sections.add(section2150)
            schedule.credits = schedule.credits + int(section2150.section_credits)
        if section3240 not in schedule.sections.all():
            schedule.sections.add(section3240)
            schedule.credits = schedule.credits + int(section3240.section_credits)
        if section3330 not in schedule.sections.all():
            schedule.sections.add(section3330)
            schedule.credits = schedule.credits + int(section3330.section_credits)
        if section4750 not in schedule.sections.all():
            schedule.sections.add(section4750)
            schedule.credits = schedule.credits + int(section4750.section_credits)

        # verify that the add URL sends a 403 HTTP status code when adding a class already in the schedule
        response = add_section(request, sect_code)
        self.assertEqual(response.status_code, 403)
        # verify that the add URL sends a 403 HTTP status code when adding a class to a schedule with too many credits
        response = add_section(request, sect_code="16618")
        self.assertEqual(response.status_code, 403)
        
    
    def test_RemoveURL(self):
        sect_code = "16003"
        request = self.factory.get('')
        request.user = self.user
        response = rem_section(request, sect_code)
        # verify that the add URL will send a 200 HTTP status code
        self.assertEqual(response.status_code, 200)

"""
Potential Reference: Connecting Google Cal API and Django
URL: https://blog.benhammond.tech/connecting-google-cal-api-and-django
Author: Ben Hammond

# not sure whether import statements can be consolidated/if there's a way to implement using allauth instead of google.oauth
from decouple import config
from google.oauth2 import service_account
fimport googleapiclient.discovery
import datetime

class GCalTest(TestCase):
    def test_addRemoveClassToCal():
        # if schedule calendar does not exist, create schedule calendar
        # add custom recurring event to schedule calendar
        # verify correct name (ex. CS 1110) should it include the full name?
        # verify correct days (starts at beginning of semester, ends at end of semester, correct days of the week)
        # verify correct times
        # verify correct location
        # verify event description includes professor name

        # remove all instances of that class in schedule calendar ("delete all events")
        # verify schedule calendar does not have event

    def test_emptySchedule():
    # should button to add schedule to google calendar only appear if there is at least one class in schedule builder?
        # if schedule builder has no classes,
        # assertTrue(button not in response.content)
        # assertTrue(schedule calendar has no events)
    # otherwise, if button is always there
        # if schedule builder has no classes and button is clicked,
        # assertTrue(schedule calendar has no events)

    def test_addDuplicateClassToCal():
        # add class to schedule calendar
        # if you add the same class to the schedule calendar, it should not create another event
        
"""