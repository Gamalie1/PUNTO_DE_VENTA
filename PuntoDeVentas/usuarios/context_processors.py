def user_modulos(request):
    if request.user.is_authenticated:
        # Obtener la lista de códigos de módulos permitidos
        modulos_codigos = list(request.user.modulos_permitidos.values_list('codigo', flat=True))
        return {
            'user_modulos_codigos': modulos_codigos,
            'user_es_admin': request.user.rol == 'ADMIN'
        }
    return {'user_modulos_codigos': [], 'user_es_admin': False}