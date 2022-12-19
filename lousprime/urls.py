from django.urls import path, include
from django.views.generic import TemplateView
from django.contrib.auth.views import LogoutView
from . import views

app_name = 'lousprime'
urlpatterns = [
    path('', TemplateView.as_view(template_name="lousprime/home.html"), name='home'),
    path('logout/', LogoutView.as_view(), name="logout"),
    path('browse/', views.get_department, name='browse_department'),
    path('browse/redirect_course/', views.redirect_course, name="redirect_page"),
    path('browse/<str:dept_name>/', views.get_courses, name="browse_course"),
    path('home/search/', views.home_search, name="home_search"),
    path('search/', views.search, name="search"),
    path('search/results/', views.search_results, name="search_results"),
    path('<str:user>/schedule/', views.schedule, name="schedule"),
    path('<str:user>/<str:commenter>/addComment/', views.add_comment, name="add_comment"),
    path('<str:user>/<uuid:uuid>/remComment/', views.rem_comment, name="rem_comment"),
    path('<int:sect_code>/addSection/', views.add_section, name="add_section"),
    path('<int:sect_code>/remSection/', views.rem_section, name="rem_section"),
    path('send_request/<int:userID>/', views.send_friend_request, name="send_request"),
    path('cancel_request/<int:requestID>/', views.cancel_friend_request, name="cancel_request"),
    path('accept_request/<int:requestID>/', views.accept_friend_request, name="accept_request"),
    path('reject_request/<int:requestID>/', views.reject_friend_request, name="reject_request"),
    path('<str:user>/social/', views.social, name="social"),
    path('<str:user>/social/friendrequestcount/', views.get_user_friendrequests, name="friend_request_count"),
    path('remove_friend/<int:friendID>/', views.remove_friend, name="remove_friend"),
    path('<str:user>/profile/', views.profile, name="profile"),
    path('<str:user>/profile/edit', views.profile_edit, name="profile_edit"),
    path('<str:user>/profile/save', views.profile_save, name="profile_save"),
    #path('about/', TemplateView.as_view(template_name="lousprime/about.html"), name='about'),
    path('about/', views.about, name='about'),
    path('privacy/', TemplateView.as_view(template_name="lousprime/privacy.html"), name='privacy'),
]