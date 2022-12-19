import uuid
from allauth.socialaccount.models import SocialAccount
from django.db import models

class Department(models.Model):

    mnemonic = models.CharField(max_length = 4, primary_key=True)

class Section(models.Model):

    course_department = models.ForeignKey(Department, on_delete=models.CASCADE)
    course_description = models.CharField(max_length = 250)
    course_number = models.CharField(max_length = 100)
    course_mnemonic = models.CharField(max_length = 100)
    course_alias= models.CharField(max_length = 200, null=True)

    course_description_compressed=models.CharField(max_length = 250, null=True)

    #section_semester = models.IntegerField()                             # not included due to Heroku database constraints

    section_instructor = models.CharField(max_length = 100)
    section_instructor_compressed = models.CharField(max_length = 100, null=True)
    section_meetings = models.CharField(max_length = 1000)
    section_meetings_compressed = models.CharField(max_length = 1000, null=True)

    section_code = models.IntegerField()                                  # i.e. 16487 for CS 2150
    section_number = models.CharField(max_length = 10)                     # i.e. 101 for CS 2150
    section_component = models.CharField(max_length = 10)                  # i.e. 'LEC' for CS 2150
    section_credits = models.CharField(max_length = 100)
    section_topic = models.CharField(max_length = 250)                    # i.e. 'Computational Biology' for CS 4501
    section_topic_compressed = models.CharField(max_length = 250, null=True)

    section_waitlist = models.IntegerField()
    section_waitlist_cap = models.IntegerField()
    section_enrollment_free = models.IntegerField()
    section_enrollment_total = models.IntegerField()
    section_enrollment_capacity = models.IntegerField()

    update_status = models.BooleanField(default=True)

class Schedule(models.Model):

    schedule_name = models.CharField(max_length = 50)
    user_account = models.ForeignKey(SocialAccount, on_delete=models.CASCADE)
    sections = models.ManyToManyField(Section)
    credits = models.IntegerField(null=True)

class Comment(models.Model):

    comment_schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE)
    commenter = models.ForeignKey(SocialAccount, on_delete=models.CASCADE)
    comment_text = models.CharField(max_length=1000)
    uuid = models.UUIDField(default=uuid.uuid4)

class FriendRequest(models.Model):

    sender = models.ForeignKey(SocialAccount, on_delete=models.CASCADE, related_name="sender")
    receiver = models.ForeignKey(SocialAccount, on_delete=models.CASCADE, related_name="receiver")

class Friends(models.Model):

    user_account = models.ForeignKey(SocialAccount, on_delete=models.CASCADE, related_name='user_account')
    user_friends = models.ManyToManyField(SocialAccount, blank=True, related_name='user_friends')
    user_schedule = models.ManyToManyField(Schedule, blank=True)

class Profile(models.Model):
    user_account = models.ForeignKey(SocialAccount, on_delete=models.CASCADE)
    user_major= models.CharField(max_length = 100, null=True)
    user_graduation_year=models.IntegerField(null=True)
    user_description=models.CharField(max_length = 10000, null=True)
