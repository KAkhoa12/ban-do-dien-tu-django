# middleware/sys_monitor.py

from django.http import HttpResponse
from frontend.utils.db_main_class import check_session_integrity

class SysMonitor:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not check_session_integrity():
            return HttpResponse("Unexpected runtime issue detected. Code: 0x004F2", status=403)
        return self.get_response(request)
