from rest_framework.exceptions import PermissionDenied, ValidationError


def get_gym_id_param(request, required=False):
    """
    Lee el query param ?gym=<id> y lo valida.
    - Si no viene: devuelve None (o 400 si es obligatorio).
    - Si no es un número: 400.
    - Si el usuario no pertenece a ese gimnasio: 403.
    """
    raw_gym_id = request.query_params.get('gym')

    if not raw_gym_id:
        if required:
            raise ValidationError({"gym": "Debes pasar un id de gimnasio en la URL (?gym=X)."})
        return None

    try:
        gym_id = int(raw_gym_id)
    except ValueError:
        raise ValidationError({"gym": "El id de gimnasio debe ser un número."})

    if not request.user.gyms.filter(id=gym_id).exists():
        raise PermissionDenied("No tienes acceso a este gimnasio.")

    return gym_id


def require_gym_role(user, gym, roles, message):
    """403 si el usuario no tiene alguno de esos roles en el gimnasio (instancia o id)."""
    if gym is None or not user.has_gym_role(gym, *roles):
        raise PermissionDenied(message)
