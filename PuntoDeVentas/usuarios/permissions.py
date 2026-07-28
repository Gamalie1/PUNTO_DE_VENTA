from functools import wraps

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied


def rol_required(*roles):
    """Exige sesión iniciada y que el rol del usuario esté en `roles`."""
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if request.user.rol not in roles:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


class RolRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Vista basada en clase que exige sesión iniciada y un rol permitido.

    Uso: class MiVista(RolRequiredMixin, ...):
             roles_permitidos = ('ADMIN',)
    """
    roles_permitidos = ()

    def test_func(self):
        return self.request.user.rol in self.roles_permitidos
