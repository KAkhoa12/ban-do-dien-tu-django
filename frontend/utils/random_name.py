import random

def generate_random_name():
    first_names = ["An", "Bình", "Chi", "Dũng", "Hương", "Khanh", "Linh", "Minh", "Phong", "Quỳnh"]
    last_names = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Phan", "Vũ", "Đặng", "Bùi", "Đỗ"]
    
    first_name = random.choice(first_names)
    last_name = random.choice(last_names)
    
    return f"{first_name} {last_name}"

def convert_to_unsign(text):
    """
    Chuyển chuỗi tiếng Việt có dấu thành không dấu
    """
    patterns = {
        '[àáảãạăắằẳẵặâấầẩẫậ]': 'a',
        '[đ]': 'd',
        '[èéẻẽẹêếềểễệ]': 'e',
        '[ìíỉĩị]': 'i',
        '[òóỏõọôốồổỗộơớờởỡợ]': 'o',
        '[ùúủũụưứừửữự]': 'u',
        '[ỳýỷỹỵ]': 'y',
        '[ÀÁẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬ]': 'A',
        '[Đ]': 'D',
        '[ÈÉẺẼẸÊẾỀỂỄỆ]': 'E',
        '[ÌÍỈĨỊ]': 'I',
        '[ÒÓỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢ]': 'O',
        '[ÙÚỦŨỤƯỨỪỬỮỰ]': 'U',
        '[ỲÝỶỸỴ]': 'Y'
    }
    
    import re
    output = text
    for regex, replace in patterns.items():
        output = re.sub(regex, replace, output)
    return output



