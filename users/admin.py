from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import AdminUserCreationForm, UserChangeForm

from .models import GymMembership, User


class EmailUserCreationForm(AdminUserCreationForm):
    class Meta(AdminUserCreationForm.Meta):
        model = User
        fields = ('email',)
        field_classes = {}


class EmailUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        field_classes = {}


class GymMembershipInline(admin.TabularInline):
    """Gimnasios del usuario y su rol en cada uno."""
    model = GymMembership
    extra = 1


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin de usuarios adaptado al login por email (el modelo no tiene username)."""
    form = EmailUserChangeForm
    add_form = EmailUserCreationForm
    inlines = [GymMembershipInline]

    ordering = ('email',)
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_active')
    search_fields = ('email', 'first_name', 'last_name')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Datos personales', {'fields': ('first_name', 'last_name')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'usable_password', 'password1', 'password2'),
        }),
    )


@admin.register(GymMembership)
class GymMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'gym', 'role')
    list_filter = ('gym', 'role')
    search_fields = ('user__email',)
