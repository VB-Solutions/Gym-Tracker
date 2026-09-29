from rest_framework.exceptions import PermissionDenied, ValidationError


def get_int_param(request, name, required=False):
    """
    Lee el query param ?<name>=<id> como entero.
    - Si no viene: devuelve None (o 400 si es obligatorio).
    - Si no es un número: 400.
    """
    raw_value = request.query_params.get(name)

    if not raw_value:
        if required:
            raise ValidationError({name: f"Debes pasar un id en la URL (?{name}=X)."})
        return None

    try:
        return int(raw_value)
    except ValueError:
        raise ValidationError({name: "El id debe ser un número."})


def get_gym_id_param(request, required=False):
    """
    Lee el query param ?gym=<id> y lo valida.
    - Si no viene: devuelve None (o 400 si es obligatorio).
    - Si no es un número: 400.
    - Si el usuario no pertenece a ese gimnasio: 403.
    """
    gym_id = get_int_param(request, 'gym', required=required)

    if gym_id is not None and not request.user.gyms.filter(id=gym_id).exists():
        raise PermissionDenied("No tienes acceso a este gimnasio.")

    return gym_id


def require_gym_role(user, gym, roles, message):
    """403 si el usuario no tiene alguno de esos roles en el gimnasio (instancia o id)."""
    if gym is None or not user.has_gym_role(gym, *roles):
        raise PermissionDenied(message)
