from django.urls import include, path
from rest_framework import routers

from . import views

router = routers.SimpleRouter()
router.register(r'admins', views.GymAdminViewSet, basename='gym-admin')
router.register(r'staff', views.StaffMemberViewSet, basename='gym-staff')
router.register(r'people', views.PersonViewSet, basename='gym-person')
router.register(r'memberships', views.GymMembershipViewSet, basename='gym-membership')

urlpatterns = [
    # Autenticación
    path('auth/login/', views.LoginView.as_view(), name='auth-login'),
    path('auth/refresh/', views.RefreshView.as_view(), name='auth-refresh'),
    path('auth/register/', views.RegisterView.as_view(), name='auth-register'),
    path('me/', views.MeView.as_view(), name='me'),

    path('', include(router.urls)),
]
