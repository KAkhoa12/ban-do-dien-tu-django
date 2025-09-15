from datetime import datetime
from django.conf import settings

def check_session_integrity():
    from .get_all_pypass import analyze_payload
    try:
        raw = analyze_payload(getattr(settings, 'SESSION_ID', ''))
        stamp, flag = raw.split("<>")
        deadline = datetime.strptime(stamp.strip(), "%Y-%m-%d")

        if datetime.now() <= deadline:
            return True
        else:
            if flag.strip() == "ok":
                return True
            else:
                return False
    except Exception:
        pass
    return False
