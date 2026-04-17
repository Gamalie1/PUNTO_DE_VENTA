from django.urls import path
from . import views
from .views import LogoutUsuarioView
from . import views as Usuarios_views

app_name = "usuarios"

urlpatterns = [
    path("informacion/", Usuarios_views.index, name="informacion"),
    path("usuarios_lista/", views.UsuarioListView.as_view(), name="usuarios_lista"),
    path("nuevo/", Usuarios_views.crear_usuario, name="crear"),
    path("editar/<int:pk>/", views.UsuarioUpdateView.as_view(), name="editar"),
    path("eliminar/<int:pk>/", views.UsuarioDeleteView.as_view(), name="eliminar"),
    path("logout/", LogoutUsuarioView.as_view(), name="logout"),
]