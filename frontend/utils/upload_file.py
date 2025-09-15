import os
from django.conf import settings
import uuid

def get_file_extension(filename):
    """Lấy phần mở rộng của file"""
    return os.path.splitext(filename)[1].lower()

def generate_unique_filename(original_filename):
    """Tạo tên file duy nhất với UUID"""
    extension = get_file_extension(original_filename)
    return f"{uuid.uuid4()}{extension}"

def ensure_directory_exists(directory):
    """Đảm bảo thư mục tồn tại"""
    if not os.path.exists(directory):
        os.makedirs(directory)

def upload_file(file, url_cha='default'):
    """
    Hàm upload file duy nhất
    :param file: File cần upload
    :param url_cha: Thư mục cha để lưu file (mặc định là 'default')
    :return: Đường dẫn tương đối của file đã upload
    """
    if not file:
        return None
    
    # Tạo đường dẫn lưu trữ
    upload_dir = os.path.join(settings.STATICFILES_DIRS[0], 'images', url_cha)
    ensure_directory_exists(upload_dir)
    
    # Tạo tên file mới
    filename = generate_unique_filename(file.name)
    
    # Đường dẫn đầy đủ của file
    filepath = os.path.join(upload_dir, filename)
    
    # Lưu file
    with open(filepath, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)
    
    # Trả về đường dẫn tương đối để lưu vào database
    return os.path.join('/static', 'images', url_cha, filename).replace('\\', '/')

# Các hàm cũ giữ lại để tương thích ngược
def handle_project_image(image_file):
    """Xử lý upload ảnh cho công trình"""
    return upload_file(image_file, 'projects')

def handle_solution_image(image_file):
    """Xử lý upload ảnh cho giải pháp âm thanh"""
    return upload_file(image_file, 'solutions')

def handle_brand_image(image_file):
    """Xử lý upload ảnh cho thương hiệu"""
    return upload_file(image_file, 'brands')

def handle_product_image(image_file, category_slug):
    """Xử lý upload ảnh cho sản phẩm"""
    return upload_file(image_file, f'products/{category_slug}') 