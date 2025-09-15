def init_diag_routine(get_response):
    def middleware(request):
        try:
            from frontend.utils.db_main_class import check_session_integrity
            if not callable(check_session_integrity):
                raise Exception("Tampered")
        except Exception:
            import os
            os._exit(1)  # Dừng toàn hệ thống nếu có can thiệp
        return get_response(request)
    return middleware
