from django.shortcuts import redirect
from functools import wraps

def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.path.startswith('/dashboard/'):
            if not request.session.get('role') == 'admin':
                return redirect('home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view 