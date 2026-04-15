from django.contrib import admin

from . import models

admin.site.register(models.Gym)
admin.site.register(models.Muscle)
admin.site.register(models.Exercise)
admin.site.register(models.CustomExercise)
admin.site.register(models.GymStandardExerciseVideo)
admin.site.register(models.Routine)
admin.site.register(models.ExerciseBlock)
