import hashlib

from django.contrib.auth import views as auth_views
from django.core.cache import cache
from django.http import HttpResponse


class RateLimitedLoginView(auth_views.LoginView):
    max_attempts = 10
    window_seconds = 15 * 60

    def dispatch(self, request, *args, **kwargs):
        ip = request.META.get("REMOTE_ADDR", "unknown")
        key = "login-attempts:" + hashlib.sha256(ip.encode("utf-8", "replace")).hexdigest()
        if request.method == "POST":
            cache.add(key, 0, timeout=self.window_seconds)
            if cache.incr(key) > self.max_attempts:
                return HttpResponse("Quá nhiều lần đăng nhập. Thử lại sau 15 phút.", status=429)
        response = super().dispatch(request, *args, **kwargs)
        if request.method == "POST" and response.status_code in {302, 303}:
            cache.delete(key)
        return response
