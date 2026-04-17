
from django.urls import path
from .views import CajaListView, CajaCreateView, TransaccionCreateView, CajaDetailView, CorteCajaListView, CorteCajaDetailView
from .views import registrar_corte_caja
from . import views

urlpatterns = [
    path('caja/', CajaListView.as_view(), name='caja_list'),
    path('caja/create/', CajaCreateView.as_view(), name='caja_create'),
    path('caja/<int:pk>/', CajaDetailView.as_view(), name='caja_detail'),
    path('transaccion/create/', TransaccionCreateView.as_view(), name='transaccion_create'),
     # Registra la URL para crear el corte de caja con el parámetro caja_id
    path('corte/caja/create/<int:caja_id>/', views.registrar_corte_caja, name='registrar_corte_caja'),
    path('corte/caja/<int:caja_id>/', views.CorteCajaListView.as_view(), name='corte_caja_list'),
    path('corte/caja/<int:pk>/', CorteCajaDetailView.as_view(), name='corte_caja_detail'),
    path('corte/caja/ingresos-egresos/<int:caja_id>/', views.registrar_ingresos_egresos, name='registrar_ingresos_egresos'),
    path('corte/pdf/<int:corte_id>/', views.generar_pdf_corte, name='pdf_corte'),
    path('corte/ticket/<int:corte_id>/', views.ticket_corte, name='ticket_corte'),
    
]