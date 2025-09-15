import sqlite3
from datetime import datetime
import random
# Hàm đọc dữ liệu từ file txt
def read_file(file_path):
    data = []
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            parts = line.strip().split(' <> ')
            data.append(parts)
    return data

# # Kết nối đến SQLite database
# conn = sqlite3.connect('db.sqlite3')
# cursor = conn.cursor()

# # Đọc dữ liệu từ tệp brands.txt
# brands = read_file('craw_data/brands.txt')
# for name, slug, image_url in brands:
#     cursor.execute("""
#         INSERT INTO frontend_brand (name, slug, image_url, created_at)
#         VALUES (?, ?, ?, ?)
#     """, (name, slug, image_url, datetime.now()))
# print("Dữ liệu từ brands.txt đã được thêm thành công!")

# # Đọc dữ liệu từ tệp categories.txt
# categories = read_file('craw_data/categories.txt')
# for name, slug, image_url in categories:
#     cursor.execute("""
#         INSERT INTO frontend_category (name, slug, image_url, description, created_at)
#         VALUES (?, ?, ?, ?, ?)
#     """, (name, slug, image_url, "", datetime.now()))
# print("Dữ liệu từ categories.txt đã được thêm thành công!")

# # Lưu thay đổi và đóng kết nối
# Hàm tìm kiếm ID của Category dựa vào tên
# Hàm tìm kiếm ID của Category dựa vào từ khóa trong tên

# Hàm tìm kiếm ID của Category dựa vào từ khóa trong tên
def get_category_id_by_name(cursor, category_name_keyword):
    cursor.execute("""
        SELECT id FROM frontend_category WHERE slug LIKE ?
    """, (f"%{category_name_keyword}%",))
    result = cursor.fetchone()
    return result[0] if result else None

# Hàm tìm kiếm ID của Brand dựa vào từ khóa trong tên
def get_brand_id_by_name(cursor, brand_name_keyword):
    cursor.execute("""
        SELECT id FROM frontend_brand WHERE slug LIKE ?
    """, (f"%{brand_name_keyword}%",))
    result = cursor.fetchone()
    return result[0] if result else None

# Kết nối đến SQLite database
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Đọc dữ liệu từ tệp products.txt
products = read_file('craw_data/products.txt')
for name, price, brand_name,category_name, image_url in products:
    try:
        # Lấy ID của category và brand bằng tên
        category_id = get_category_id_by_name(cursor, category_name)  # Thay "Tên danh mục mẫu" bằng tên cần tìm
        brand_id = get_brand_id_by_name(cursor, brand_name)
        
        # Nếu không tìm thấy category hoặc brand, bỏ qua dòng này
        if not category_id or not brand_id:
            print(f"Category hoặc Brand không tồn tại cho sản phẩm: {name}")
            continue

        # Sinh giá trị ngẫu nhiên cho number_of_sell và number_of_like
        number_of_sell = random.randint(300, 3000)
        number_of_like = random.randint(300, 3000)

        # Chèn dữ liệu vào bảng Product
        price = float(price) if price != "0" else 1500000
        cursor.execute("""
            INSERT INTO frontend_product (
                name, description, price, old_price, tags, stock, category_id, brand_id, created_at, number_of_sell, image_url, number_of_like
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, name, price, float(price + (price * 0.3)), 'news', 100, category_id, brand_id, datetime.now(), number_of_sell, image_url, number_of_like))
    except Exception as e:
        print(f"Error inserting product: {str(e)}")

print("Dữ liệu từ products.txt đã được thêm thành công!")
conn.commit()
conn.close()
print("Hoàn thành!")
