from django.urls import path, include
from rest_framework import routers
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from . import views

router = routers.DefaultRouter()
router.register(r'gyms', views.GymViewSet, basename='gym')
router.register(r'muscles', views.MuscleViewSet, basename='muscle')
router.register(r'exercises', views.ExerciseViewSet, basename='exercise')
router.register(r'custom-exercises', views.CustomExerciseViewSet, basename='custom-exercise')
router.register(
    r'gym-standard-exercise-videos',
    views.GymStandardExerciseVideoViewSet,
    basename='gym-standard-exercise-video',
)
router.register(r'routines', views.RoutineViewSet, basename='routine')

urlpatterns = [
    # 1. Rutas generadas por el Router
    path('', include(router.urls)),

    # 2. Documentación Swagger (drf-spectacular)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]