import sys
from tracemalloc import start
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.models import User
from xml.dom.minidom import NamedNodeMap

from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from lousprime.models import *
from django.urls import reverse
from django.db.models import Q
from django.contrib import messages
import requests
import datetime
import uuid
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.views.decorators.cache import cache_control

def filter_courses(json):
    subject=json["subject"].upper()
    courses = Section.objects.filter(
       Q(section_meetings_compressed__contains=(json["days"]).replace(" ", "").upper()),
        Q(section_meetings_compressed__contains=(json["time"]).replace(" ", "").upper()),
        Q(section_meetings_compressed__contains=(json["facility_description"]).replace(" ", "").upper()),
        Q(course_mnemonic__contains=subject), 
        Q(course_number__contains=json["catalog_number"]), 
        Q(course_description_compressed__contains=(json["description"].replace(" ", "")).upper()),
        Q(section_credits__contains=json["units"]), 
        Q(section_topic_compressed__contains=(json["topic"].replace(" ", "")).upper()),
        Q(section_instructor_compressed__contains=(json["instructor"].replace(" ", "")).upper()),
        Q(section_component__contains=json["component"])).order_by("course_mnemonic", "course_number")

    
    # May be possible to combine all the filters into one (should improve runtime) by setting a default value if json has no value for it
    try:
        if(json["min_limit"]!=""):
            courses=courses.filter(section_enrollment_capacity__gte=json["min_limit"]).order_by("course_mnemonic", "course_number" )
        if(json["max_limit"]!=""):
            courses=courses.filter(section_enrollment_capacity__lte=json["max_limit"]).order_by("course_mnemonic", "course_number" )
        if(json["min_enrollment"]!=""):
            courses=courses.filter(section_enrollment_total__gte=json["min_enrollment"]).order_by("course_mnemonic", "course_number" )
        if(json["max_enrollment"]!=""):
            courses=courses.filter(section_enrollment_total__lte=json["max_enrollment"]).order_by("course_mnemonic", "course_number" )
        if(json["min_waitlist"]!=""):
            courses=courses.filter(section_waitlist__gte=json["min_waitlist"]).order_by("course_mnemonic", "course_number" )
        if(json["max_waitlist"]!=""):
            courses=courses.filter(section_waitlist__lte=json["max_waitlist"]).order_by("course_mnemonic", "course_number" )
    except ValueError:
        return {}
    # Parse as hierarchy of courses and sections for template rendering
    results = {}
    for course in courses:
        course_id = course.course_mnemonic + course.course_number
        if course_id in results.keys():
            results[course_id].append(course)
        else:
            results[course_id] = [course]
    
    return results

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def search(request):
    return render(request, "lousprime/search.html", {})

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def search_results(request):
    if(request.method!="POST"):
        return render(request, 'lousprime/search.html', {
            'error_message': "Something went wrong",
    })

    json={}
    names=["subject", "catalog_number", "component", "instructor", "facility_description", "days", "units", "time",
     "description", "topic", "min_limit", "max_limit", "min_enrollment", "max_enrollment", "min_waitlist", "max_waitlist"]
    for name in names:
        if(name=="time"):
            if("-" in request.POST.get(name)):
                times=request.POST.get(name).split("-")
                start_time = times[0].strip()
                end_time = times[1].strip()
                json["time"]=parse_time_input(start_time)+"-"+parse_time_input(end_time)
            else:
                json["time"]=parse_time_input(request.POST.get(name).strip())
        else:
            json[name]=request.POST.get(name)
    courses=filter_courses(json)
    if request.user.is_authenticated:
        schedule = get_user_schedule(request, None)
    else:
        return render(request, "lousprime/results.html", { "courses": courses, "queries": json})
    return render(request, "lousprime/results.html", { "courses": courses, "queries": json, "schedule": schedule})

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def home_search(request):
    query=request.POST.get("query")
    if( not query):
        json={"You searched for": "None"}
        return render(request, "lousprime/results.html", { "queries": json})
    courses=Section.objects.filter(
        Q(course_mnemonic__contains=query.upper()) | 
        Q(course_description_compressed__contains=(query.replace(" ", "")).upper()) |
        Q(section_topic_compressed__contains=(query.replace(" ", "")).upper()) |
        Q(section_instructor_compressed__contains=(query.replace(" ", "")).upper()) |
        Q(course_description_compressed=(query.replace(" ", "")).upper()) |
        Q(section_topic_compressed=(query.replace(" ", "")).upper()) |
        Q(section_instructor_compressed=(query.replace(" ", "")).upper()) | 
        Q(course_alias__contains=(query.replace(" ", "")).upper()) |
        Q(course_alias=(query.replace(" ", "")).upper()) 
        ).order_by("course_mnemonic", "course_number")
    results = {}
    json={"You searched for": query}
    for course in courses:
        course_id = course.course_mnemonic + course.course_number
        if course_id in results.keys():
            results[course_id].append(course)
        else:
            results[course_id] = [course]
    courses=results
    if request.user.is_authenticated:
            schedule = get_user_schedule(request, None)
    else:
            return render(request, "lousprime/results.html", { "courses": courses, "queries": json})
    return render(request, "lousprime/results.html", { "courses": courses, "queries": json, "schedule": schedule})

def force_course_update(request, dept_name):
    update_courses(dept_name)
    return get_courses(request, dept_name)

# Help parse time inputs from search form (can be improved!)
def parse_time_input(time):
    period=""
    if "AM" in time.upper() or "PM" in time.upper():
        period = time[-2:]
        time = time[:-2]
    if ":" in time:
        hour, min = time.split(":")
        hour = int(hour.strip())
        min = int(min.strip())
    
        time = str(datetime.time(hour, min))[0:-3]
    return f"{time}{period}"

# Given a department mnemonic, update the courses for that department according to the API
def update_courses(dept_name):

    url = 'http://luthers-list.herokuapp.com/api/dept/' + dept_name + '/?format=json'
    response = requests.get(url)
    dept_data = response.json()

    if Department.objects.filter(pk = dept_name).exists():
        department = Department.objects.get(pk = dept_name)
    else:
        department = Department(
            mnemonic = dept_name
        )
        department.save()

    department_sections = Section.objects.filter(course_department=department)
    department_sections.update(update_status = False)

    for course in dept_data:

        course_subject = course['subject']               # i.e. CS for CS 2150
        course_number = course['catalog_number']         # i.e. 2150 for CS 2150
        course_description = course['description']

        section_code = course['course_number']
        section_number = course['course_section']
        semester_code = course['semester_code']

        # Need to update when switching to new semester data (database not large enough to fit both semesters)
        if semester_code!= 1228:
            continue

        if department_sections.filter(course_department=department, course_number=course_number, course_mnemonic=course_subject, course_description=course_description, section_code=section_code, section_number=section_number).exists():
            section = department_sections.get(course_department=department, course_number=course_number, course_mnemonic=course_subject, course_description=course_description, section_code=section_code, section_number=section_number)
            section.section_instructor = course['instructor']['name']
            section.section_component = course['component']
            section.section_credits = course['units']
            section.section_topic = course['topic']
            section.section_waitlist = course['wait_list']
            section.section_waitlist_cap = course['wait_cap']
            section.section_enrollment_free = course['enrollment_available']
            section.section_enrollment_total = course['enrollment_total']
            section.section_enrollment_capacity = course['class_capacity']
            section.section_meetings = meeting_to_string(course['meetings'])
            section.section_meetings_compressed=(meeting_to_string(course['meetings']).replace(" ", "")).upper()
            section.update_status = True
            section.course_description_compressed=(course_description.replace(" ", "")).upper()
            section.section_instructor_compressed=(course['instructor']['name'].replace(" ", "")).upper()
            section.section_topic_compressed=(course['topic'].replace(" ", "")).upper()
            section.course_alias=course_subject+course_number
        else:
            section = Section(
                course_department=department,
                course_number=course_number,
                course_mnemonic=course_subject,
                course_description=course_description,
                course_description_compressed=(course_description.replace(" ", "")).upper(),
                section_code = course['course_number'],                 # i.e. 16487 for CS 2150
                section_number = course['course_section'],              # i.e. 101 for CS 2150
                section_component = course['component'],                # i.e. 'LEC' for CS 2150
                section_credits = course['units'],                      # i.e. 3 credits

                section_instructor = course['instructor']['name'],
                section_instructor_compressed = (course['instructor']['name'].replace(" ", "")).upper(),
                section_topic = course['topic'],
                section_topic_compressed= (course['topic'].replace(" ", "")).upper(),
                section_waitlist = course['wait_list'],
                section_waitlist_cap = course['wait_cap'],
                section_enrollment_free = course['enrollment_available'],
                section_enrollment_total = course['enrollment_total'],
                section_enrollment_capacity = course['class_capacity'],
                section_meetings = meeting_to_string(course['meetings']),
                section_meetings_compressed=(meeting_to_string(course['meetings']).replace(" ", "")).upper(),
                course_alias=course_subject+course_number,
                update_status = True
            )
        section.save()
    
    # Delete any outdated sections that were not found in the most recent API parse
    Section.objects.filter(course_department=department, update_status=False).delete()

# Helper method to represent the meeting data as a string
"""
Given the meeting JSON information, returns a string formatted as:
Day,Time,Location;Day,Time,Location; ... ;Day,Time,Location
i.e. TuTh,01:00PM-01:50PM,Thornton D303;Tu,08:30PM-10:00PM,Thornton E301
"""
def meeting_to_string(meetings):
    meeting_string = ""
    
    if not meetings:
        return ",,"

    for m in meetings:
        start_time = convert_time(m['start_time'])
        end_time = convert_time(m['end_time'])
        meeting_string += f"{m['days']},{start_time}-{end_time},{m['facility_description']};"
    
    return meeting_string[:-1]

"""
Converts time in the API given in the form of hour.min.second.milliseconds to hour:minAM/PM
i.e. 17.30.00.000000-05:00 ==> 05:30PM
"""
def convert_time(time):
    divide = time.find('-')

    if len(time) == 0:
        return ""
    
    if divide>=0:
        pieces = time[:divide].split('.')

        hour = int(pieces[0])
        min = int(pieces[1])
        period = "AM"
        if hour==12:
            period = "PM"
        elif hour>12:
            hour -= 12
            period = "PM"
        
        time = str(datetime.time(hour, min))[0:-3]
        return f"{time}{period}"
    
    return time

# Used in manage.py commands to reupdate all department data, run daily in Heroku Scheduler
def update_departments():
    
    url = 'http://luthers-list.herokuapp.com/api/deptlist/?format=json'
    response = requests.get(url)
    dept_data = response.json()

    for dept in dept_data:
        department_mnemonic = dept['subject']
        update_courses(department_mnemonic)

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def get_courses(request, dept_name):
    sections = Section.objects.filter(course_department=dept_name).order_by('course_number', 'section_number')
    course_dict = {}
    for s in sections:
        if s.course_number in course_dict.keys():
            course_dict[s.course_number].append(s)
        else:
            course_dict[s.course_number] = [s]
    if request.user.is_authenticated:
        schedule = get_user_schedule(request, None)
        return render(request, 'lousprime/course.html', {"dept": dept_name, "courses": course_dict, "schedule": schedule})
    else:
        return render(request, 'lousprime/course.html', {"dept": dept_name, "courses": course_dict})
    

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def get_department(request):
    departments = Department.objects.all().order_by('mnemonic')
    midpoint = int(len(departments)/2+0.5)

    # For table formatting reasons, divide it into two columns so it is alphabetical by row
    first_table_column = departments[:midpoint]
    second_table_column = departments[midpoint:]
    if len(second_table_column)<midpoint:
        second_table_column.append({'mnemonic':""})
    reversed_departments = [[first_table_column[i], second_table_column[i]] for i in range(midpoint)]

    return render(request, 'lousprime/browse.html', {"departments": departments, "reversed_departments": reversed_departments})

# For dropdown selection on browse page
def redirect_course(request):
    try:
        dept_name = request.POST['dept_name']
    except (KeyError):
        return render(request, 'lousprime/course.html', {'error_message': "INCORRECT"})
    return HttpResponseRedirect(reverse('lousprime:browse_course', args=(dept_name,)))

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def schedule(request, user):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('lousprime:home'))
    schedule = get_user_schedule(request, user)
    days = ["Mo", "Tu", "We", "Th", "Fr"]
    meeting_list = []
    for day in days:
        for section in schedule.sections.all():
            for meeting in section.section_meetings.split(";"):
                date_time_location = meeting.split(",")
                if (day in date_time_location[0]):
                    times = date_time_location[1].split("-")
                    start = float(times[0][:2])
                    if (times[0][-2:] == "PM" and start != 12):
                        start += 12
                    start += float(times[0][3:5]) / 60
                    end = float(times[1][:2])
                    if (times[1][-2:] == "PM" and end != 12):
                        end += 12
                    end += float(times[1][3:5]) / 60
                    length = (end - start) * 100
                    meeting_list.append({"day": day, "name": section.course_description, "section_code": section.section_code, "start": start, "end": end, "start_frac": (start % 1 * 100), "start_text": times[0], "end_text": times[1], "length": length, "alias": (section.course_mnemonic+" "+section.course_number)})
    times = []
    for i in range(7, 22):
        i2 = i+1
        if(i == 12):
            time_start = "12:00PM"
        elif(i > 12):
            time_start = str(i-12) + ":00PM"
        else:
            time_start = str(i) + ":00AM"
        if (i2 == 12):
            time_end = "12:00PM"
        elif (i2 > 12):
            time_end = str(i2-12) + ":00PM"
        else:
            time_end = str(i2) + ":00AM"
        times.append({ "start": time_start, "end": time_end, "num_start": i, "num_end": i2 })

    friends = get_user_friends(request)
    comments = Comment.objects.filter(comment_schedule=schedule)
    try:
        user = User.objects.get(username=user)
        uid = user.id
    except(ObjectDoesNotExist):
        user = request.user
        uid = user.id
    social_account_check = SocialAccount.objects.get(user=uid)
    if(social_account_check in friends.user_friends.all() or uid == request.user.id):
        return render(request, "lousprime/schedule.html", {"schedule": schedule, "comments": comments, "viewing_user": user,"days": days, "times": times, "meeting_list": meeting_list})
    else:
        num_admins = len(User.objects.filter(is_staff=True))
        return render(request, "lousprime/schedule.html", {"non_friend_uid": uid-num_admins})

def add_comment(request, user, commenter):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('lousprime:home'))
    comment = request.POST['comment']
    if (len(comment) != 0):
        schedule = get_user_schedule(request, user)
        try:
            uid = User.objects.get(username=commenter).id
        except(ObjectDoesNotExist):
            uid = request.user.id
        commenter_account = SocialAccount.objects.get(user=uid)
        if(commenter_account.user.username == commenter and schedule.user_account.user.username == user):
            friends = get_user_friends(request)
            if(schedule.user_account in friends.user_friends.all() or schedule.user_account == friends.user_account):
                c = Comment(comment_schedule=schedule, commenter=commenter_account, comment_text=comment, uuid=uuid.uuid4())
                c.save()

    return HttpResponseRedirect(reverse('lousprime:schedule', args=(user,)))

def rem_comment(request, user, uuid):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('lousprime:home'))
    schedule = get_user_schedule(request, user)
    try:
        comment = Comment.objects.get(uuid=uuid)
    except(ObjectDoesNotExist):
        return HttpResponseRedirect(reverse('lousprime:schedule', args=(user,)))
    if(request.user == comment.commenter.user or request.user == schedule.user_account.user):
        comment.delete()
    return HttpResponseRedirect(reverse('lousprime:schedule', args=(user,)))

def get_user_schedule(request, user):
    if(user != None):
        try:
            uid = User.objects.get(username=user).id
        except(ObjectDoesNotExist):
            uid = request.user.id
    else:
        uid = request.user.id
    social_account = SocialAccount.objects.get(user=uid)
    schedule = Schedule.objects.get_or_create(user_account=social_account)
    if (schedule[1]):
        schedule[0].schedule_name = social_account.user.username.capitalize() + "'s Schedule"
        schedule[0].credits = 0
        schedule[0].sections.clear()
        schedule[0].save()
    return schedule[0]


#TuTh,01:00PM-01:50PM,Thornton D303,Tu,08:30PM-10:00PM,Thornton E301
def check_overlap(section1, section2):
    days_of_week=["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
    meetings1=section1.split(",")
    meetings2=section2.split(",")
    days1, days2, times1, times2=None, None, None, None
    if(len(meetings1)>0):
        days1=meetings1[0]
    if(len(meetings2)>0):
        days2=meetings2[0]
    if(not(days1 and days2)):
        return False
    shared_day=False
    for day in days_of_week:
        if day in days1 and day in days2:
            shared_day=True
    if(not shared_day):
        return False
    start_time1, start_time2, end_time1, end_time2= None, None, None, None
    if(len(meetings1)>1):
        times1=meetings1[1]
        period=times1.split("-")
        if(len(period)>1):
            start_time1=datetime.datetime.strptime(period[0], "%I:%M%p")
            end_time1=datetime.datetime.strptime(period[1], "%I:%M%p")
    if(len(meetings2)>1):
        times2=meetings2[1]
        period=times2.split("-")
        if(len(period)>1):
            start_time2=datetime.datetime.strptime(period[0], "%I:%M%p")
            end_time2=datetime.datetime.strptime(period[1], "%I:%M%p")
    
    return start_time1<=end_time2 and end_time1>=start_time2

def section_overlap(intervals1, intervals2):
    sections1=intervals1.split(";")
    sections2=intervals2.split(";")
    for section1 in sections1:
        for section2 in sections2:
            if(check_overlap(section1, section2)):
                return True
    return False

@csrf_exempt
def add_section(request, sect_code, override=0):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('lousprime:home'))
    schedule = get_user_schedule(request, None)
    section = Section.objects.get(section_code=sect_code)
    if not override:
        for sectionCheck in schedule.sections.all():
            if(section.course_mnemonic == sectionCheck.course_mnemonic and section.course_number == sectionCheck.course_number and section.section_component == sectionCheck.section_component):
                response = JsonResponse({"error": f"{sectionCheck.course_mnemonic} {sectionCheck.course_number} is already in your schedule!"})
                response.status_code = 403
                return response
            if(section_overlap(section.section_meetings, sectionCheck.section_meetings)):
                response = JsonResponse({"error": f"This section has a time conflict with {sectionCheck.course_mnemonic} {sectionCheck.course_number}!"})
                response.status_code = 403
                return response
    try:
        schedule.credits = schedule.credits + int(section.section_credits)
    except(ValueError):
        schedule.credits = schedule.credits + 1
    if(override or schedule.credits <= 25):
        schedule.sections.add(section)
        schedule.save()
        return JsonResponse({"message":f"Successfully added section {sect_code} of {section.course_mnemonic} {section.course_number} to schedule! You are taking {schedule.credits} credits!"})
    else:
        response = JsonResponse({"error": "You have surpassed your credit limit!"})
        response.status_code = 403
        return response

@csrf_exempt
def rem_section(request, sect_code):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('lousprime:home'))
    schedule = get_user_schedule(request, None)
    section = Section.objects.get(section_code=sect_code)
    if (section in schedule.sections.all()):
        schedule.sections.remove(section)
        try:
            schedule.credits = schedule.credits - int(section.section_credits) if schedule.credits - int(
                section.section_credits) >= 0 else 0
        except(ValueError):
            schedule.credits = schedule.credits - 1
        schedule.save()
        return JsonResponse({"message": "Successfully removed course!"})
    else:
        return JsonResponse({"message": "Failed to remove course..."})

# Friends

def get_possible_friends(request):
    sender = SocialAccount.objects.get(user=(request.user.id))
    sender_friends=Friends.objects.get(user_account=sender)
    possible_accounts=SocialAccount.objects.all()
    outgoing_requests=FriendRequest.objects.filter(sender=sender)
    pending_requests=FriendRequest.objects.filter(receiver=sender)
    num_admins=len(User.objects.filter(is_staff=True))
    if(sender_friends.user_friends.all()):
        for friend in sender_friends.user_friends.all():
            possible_accounts=possible_accounts.exclude(user=(friend.id+num_admins))
    possible_accounts=possible_accounts.exclude(user=request.user.id)
    if(outgoing_requests):
        for friend in outgoing_requests:
            possible_accounts=possible_accounts.exclude(user=(friend.receiver.id+num_admins))
    if(pending_requests):
        for friend in pending_requests:
            possible_accounts=possible_accounts.exclude(user=(friend.sender.id+num_admins))

    return possible_accounts

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def social(request, user):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('lousprime:home'))
    friends = get_user_friends(request)
    users=get_possible_friends(request)
    social_account =  SocialAccount.objects.get(user=request.user.id)
    friend_requests=FriendRequest.objects.filter(receiver=social_account)
    outgoing_requests=FriendRequest.objects.filter(sender=social_account)
    return render(request, 'lousprime/social.html', {"friends": friends, "users": users, "friend_requests": friend_requests, "outgoing_requests": outgoing_requests})

def get_user_friendrequests(request, user):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('lousprime:home'))
    social_account =  SocialAccount.objects.get(user=request.user.id)
    friend_requests=FriendRequest.objects.filter(receiver=social_account)
    return JsonResponse({'friend_request_count': len(friend_requests)})

def get_user_friends(request):
    social_account = SocialAccount.objects.get(user=request.user.id)
    friends = Friends.objects.get_or_create(user_account=social_account)
    if (friends[1]):
        friends[0].user_friends.clear()
        friends[0].save()
    return friends[0]

def send_friend_request(request, userID):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('lousprime:home'))
    num_admins=len(User.objects.filter(is_staff=True))
    receiver = SocialAccount.objects.get(user=userID+num_admins)
    sender = SocialAccount.objects.get(user=request.user.id)
    friend_request, created = FriendRequest.objects.get_or_create(sender=sender, receiver=receiver)
    if created:
        return HttpResponseRedirect(reverse('lousprime:social', args=(request.user,)))
    else:
        return HttpResponse("Friend request already sent!")

def cancel_friend_request(request, requestID):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('lousprime:home'))
    num_admins=len(User.objects.filter(is_staff=True))
    receiver = SocialAccount.objects.get(user=requestID+num_admins)
    sender = SocialAccount.objects.get(user=request.user.id)
    friend_request=FriendRequest.objects.get(sender=sender, receiver=receiver)
    friend_request.delete()
    return HttpResponseRedirect(reverse('lousprime:social', args=(request.user,)))

def accept_friend_request(request, requestID):
    #FriendRequest.objects.get(sender_id=9, receiver_id=6)
    num_admins=len(User.objects.filter(is_staff=True))
    friend_request = FriendRequest.objects.get(sender_id=(requestID), receiver_id=(request.user.id-num_admins))
    sender_friends=Friends.objects.get(user_account=friend_request.sender)
    receiver_friends=Friends.objects.get(user_account=friend_request.receiver)
    sender_friends.user_friends.add(friend_request.receiver)
    receiver_friends.user_friends.add(friend_request.sender)
    friend_request.delete()
    return HttpResponseRedirect(reverse('lousprime:social', args=(request.user,)))

def reject_friend_request(request, requestID):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('lousprime:home'))
    num_admins=len(User.objects.filter(is_staff=True))
    friend_request = FriendRequest.objects.get(sender_id=(requestID), receiver_id=(request.user.id-num_admins))
    friend_request.delete()
    return HttpResponseRedirect(reverse('lousprime:social', args=(request.user,)))

def remove_friend(request, friendID):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('lousprime:home'))
    num_admins=len(User.objects.filter(is_staff=True))
    social_account =  SocialAccount.objects.get(user=request.user.id)
    removed_account=SocialAccount.objects.get(user=(friendID+num_admins))
    social_friends=Friends.objects.get(user_account=social_account)
    removed_friends=Friends.objects.get(user_account=removed_account)
    social_friends.user_friends.remove(removed_account)
    removed_friends.user_friends.remove(social_account)
    return HttpResponseRedirect(reverse('lousprime:social', args=(request.user,)))

def get_user_profile(request, user):
    if(user != None):
        try:
            uid = User.objects.get(username=user).id
        except(ObjectDoesNotExist):
            uid = request.user.id
    else:
        uid = request.user.id
    social_account =  SocialAccount.objects.get(user=uid)
    user_profile=Profile.objects.get_or_create(user_account=social_account)
    if(user_profile[1]):
        user_profile[0].user_major ="Undecided"
        user_profile[0].user_graduation_year=0
        user_profile[0].user_description=""
        user_profile[0].save()
    return (user_profile[0], uid)

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def profile(request, user):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('lousprime:home'))
    num_admins = len(User.objects.filter(is_staff=True))
    user_profile, uid=get_user_profile(request, user)
    if(uid==request.user.id):
        return render(request, 'lousprime/profile.html', {"username": user, "viewing_user":request.user.get_username(), "profile": user_profile})
    friends = get_possible_friends(request)
    social_account_check = SocialAccount.objects.get(user=uid)
    try:
        pending_request=FriendRequest.objects.get(sender=user_profile.user_account, receiver_id=request.user.id-num_admins)
        return render(request, "lousprime/profile.html", {"username": user, "viewing_user":request.user.get_username(), "profile": user_profile, "pending_request_id": uid-num_admins})
    except FriendRequest.DoesNotExist:
        try:
            outgoing_request=FriendRequest.objects.get(receiver=user_profile.user_account, sender_id=request.user.id-num_admins)
            return render(request, "lousprime/profile.html", {"username": user, "viewing_user":request.user.get_username(), "profile": user_profile, "outgoing_request_id": uid-num_admins})
        except FriendRequest.DoesNotExist:
            if( not social_account_check in friends.all()):
                return render(request, 'lousprime/profile.html', {"username": user, "viewing_user":request.user.get_username(), "profile": user_profile})
            else:
                return render(request, "lousprime/profile.html", {"username": user, "viewing_user":request.user.get_username(), "profile": user_profile, "non_friend_uid": uid-num_admins})

def profile_edit(request, user):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('lousprime:home'))
    social_account =  SocialAccount.objects.get(user=request.user.id)
    user_profile, uid=get_user_profile(request, user)
    years=[i for i in range(2000, 2051, 1) if i!=user_profile.user_graduation_year]
    return render(request, 'lousprime/edit.html', {"username": user, "social_account": social_account, "profile": user_profile, "years": years})

def profile_save(request, user):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('lousprime:home'))
    social_account=SocialAccount.objects.get(user=request.user.id)
    user_profile=Profile.objects.get(user_account=social_account)
    major=request.POST.get("major")
    description = request.POST.get("description")
    user_profile.user_major = major
    user_profile.user_description=description
    user_profile.save()

    # We do a little trolling ;)
    graduation_year=request.POST.get("grad_year")
    error = "NONE"
    if len(graduation_year) == 0:
        error = "Please input a graduation year :)"
    if 'E' in graduation_year.upper():
        error = "Last I checked, E was a letter ;)"
    if error == "NONE" and len(graduation_year) >= 17:
        error = "We haven't hit the heat death of the universe just yet...\nLets try that again ;)"
    if error == "NONE" and int(graduation_year) >= 3000:
        error = "Let's try to be a little more... realistic about when you plan on graduating.\n Come on, we have faith in you :)"
    if error == "NONE" and int(graduation_year) < 0:
        error = "Wow, a negative number!\nPlease send us the blueprint to your time machine ASAP!"
    if error == "NONE" and int(graduation_year) < 1819:
        error = "Graduation before the university was even built is a liiittle bit hard to believe...\nBut hey, if you live long enough maybe you'll see TJ!"
    if error != "NONE":
        social_account = SocialAccount.objects.get(user=request.user.id)
        user_profile, uid = get_user_profile(request, user)
        years = [i for i in range(2000, 2051, 1) if i != user_profile.user_graduation_year]
        return render(request, 'lousprime/edit.html', {"username": user, "social_account": social_account, "profile": user_profile, "years": years, 'error_message': error})
    user_profile.user_graduation_year=graduation_year
    user_profile.save()
    return HttpResponseRedirect(reverse('lousprime:profile', args=(request.user,)))

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def about(request):
    return render(request, "lousprime/about.html")