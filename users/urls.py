from django.urls import include, path
from rest_framework import routers

from . import views

router = routers.SimpleRouter()
router.register(r'admins', views.GymAdminViewSet, basename='gym-admin')
router.register(r'staff', views.StaffMemberViewSet, basename='gym-staff')
router.register(r'people', views.PersonViewSet, basename='gym-person')

urlpatterns = [
    path('', include(router.urls)),
    
]
