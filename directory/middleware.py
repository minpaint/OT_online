from django.utils.deprecation import MiddlewareMixin

class DisableCSRFForSmartSelects(MiddlewareMixin):
    def process_request(self, request):
        if request.path.startswith("/chaining/"):
            setattr(request, '_dont_enforce_csrf_checks', True)
        return None