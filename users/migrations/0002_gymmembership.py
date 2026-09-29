import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def copy_global_roles_to_memberships(apps, schema_editor):
    """Cada gimnasio del usuario pasa a ser una membresía con el rol global que tenía."""
    User = apps.get_model('users', 'User')
    GymMembership = apps.get_model('users', 'GymMembership')

    GymMembership.objects.bulk_create(
        GymMembership(user=user, gym=gym, role=user.role)
        for user in User.objects.prefetch_related('gyms')
        for gym in user.gyms.all()
    )


def copy_memberships_to_global_roles(apps, schema_editor):
    """Reversa: el usuario recupera sus gimnasios y el rol de su primera membresía."""
    User = apps.get_model('users', 'User')
    GymMembership = apps.get_model('users', 'GymMembership')

    for user in User.objects.all():
        memberships = GymMembership.objects.filter(user=user).order_by('id')
        user.gyms.set([membership.gym_id for membership in memberships])
        if memberships:
            user.role = memberships[0].role
            user.save(update_fields=['role'])


class Migration(migrations.Migration):
    """
    El rol deja de ser global (User.role) y pasa a ser por gimnasio (GymMembership.role).
    Se crea GymMembership, se copian los datos y recién ahí se reemplaza la M2M.
    """

    dependencies = [
        ('gym_tracker', '0007_exercise_description'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='GymMembership',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('ADMIN', 'Gym Admin'), ('STAFF', 'Staff/Trainer'), ('PERSON', 'Socio/Cliente')], default='PERSON', max_length=10)),
                ('gym', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='memberships', to='gym_tracker.gym')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='memberships', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'constraints': [models.UniqueConstraint(fields=('user', 'gym'), name='unique_user_gym_membership')],
            },
        ),
        migrations.RunPython(copy_global_roles_to_memberships, copy_memberships_to_global_roles),
        # Django no permite agregarle `through` a una M2M existente: se saca y se vuelve a crear
        migrations.RemoveField(
            model_name='user',
            name='gyms',
        ),
        migrations.AddField(
            model_name='user',
            name='gyms',
            field=models.ManyToManyField(blank=True, related_name='users', through='users.GymMembership', to='gym_tracker.gym'),
        ),
        migrations.RemoveField(
            model_name='user',
            name='role',
        ),
    ]
