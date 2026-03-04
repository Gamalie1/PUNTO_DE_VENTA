from django.shortcuts import render,  redirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Usuario
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView,  LogoutView
from .forms import UsuarioForm
from django.contrib.auth import logout

def index(request):
    return render(request, 'index.html')

class UsuarioListView( ListView):
    model = Usuario
    template_name = "lista_usuarios.html"


class UsuarioCreateView(LoginRequiredMixin, CreateView):
    model = Usuario
    form_class = UsuarioForm
    template_name = "form.html"
    success_url = reverse_lazy("usuarios:lista")

    def form_valid(self, form):
        user = form.save(commit=False)
        user.set_password(form.cleaned_data["password"])
        user.save()
        return super().form_valid(form)


class UsuarioUpdateView(LoginRequiredMixin, UpdateView):
    model = Usuario
    fields = ["email", "rol", "telefono"]
    template_name = "form.html"
    success_url = reverse_lazy("usuarios:lista")


class UsuarioDeleteView(LoginRequiredMixin, DeleteView):
    model = Usuario
    template_name = "eliminar.html"
    success_url = reverse_lazy("usuarios:lista")




class LoginUsuarioView(LoginView):
    template_name = "login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy("usuarios:informacion")


class LogoutUsuarioView(LogoutView):
    next_page = reverse_lazy("usuarios:login")
