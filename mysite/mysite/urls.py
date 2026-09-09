"""
URL configuration for mysite project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from myapp import views #importing the views from myapp to use in the urls.py file
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('scholarship/<slug:slug>/', views.scholarship_detail, name='scholarship_detail'),
    path('country/<slug:slug>/', views.country_detail, name='country_detail'),
    path('go/<slug:slug>/', views.scholarship_redirect, name='scholarship_redirect'),
    path('save/<slug:slug>/', views.toggle_save, name='toggle_save'),
    path('saved/', views.saved_scholarships, name='saved_scholarships'),
    path('dashboard/login/', views.admin_login, name='admin_login'),
    path('dashboard/logout/', views.admin_logout, name='admin_logout'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/scholarships/', views.admin_scholarship_list, name='admin_scholarship_list'),
    path('dashboard/scholarships/add/', views.admin_scholarship_add, name='admin_scholarship_add'),
    path('dashboard/scholarships/<int:pk>/edit/', views.admin_scholarship_edit, name='admin_scholarship_edit'),
    path('dashboard/scholarships/<int:pk>/delete/', views.admin_scholarship_delete, name='admin_scholarship_delete'),
    path('dashboard/countries/', views.admin_country_list, name='admin_country_list'),
    path('dashboard/countries/add/', views.admin_country_add, name='admin_country_add'),
    path('dashboard/countries/<int:pk>/edit/', views.admin_country_edit, name='admin_country_edit'),
    path('dashboard/countries/<int:pk>/delete/', views.admin_country_delete, name='admin_country_delete'),
    path('submit-scholarship/', views.submit_scholarship, name='submit_scholarship'),
    path('coaching/', views.request_coaching, name='request_coaching'),
    path('newsletter/signup/', views.newsletter_signup, name='newsletter_signup'),

    path('dashboard/submissions/', views.admin_submission_list, name='admin_submission_list'),
    path('dashboard/submissions/<int:pk>/', views.admin_submission_review, name='admin_submission_review'),
    path('dashboard/coaching/', views.admin_coaching_list, name='admin_coaching_list'),
    path('newsletter/unsubscribe/<uuid:token>/', views.newsletter_unsubscribe, name='newsletter_unsubscribe'),
    


]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)