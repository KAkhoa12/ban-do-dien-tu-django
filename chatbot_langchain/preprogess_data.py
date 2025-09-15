import os
import sqlite3

def get_db_connection():
    """Kết nối với database SQLite"""
    try:
        # Đường dẫn tới file db.sqlite3 trong thư mục gốc của project
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'db.sqlite3')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Để có thể truy cập kết quả bằng tên cột
        return conn
    except sqlite3.Error as e:
        print(f"Lỗi kết nối database: {e}")
        return None

def generate_product_data():
    """
    Tạo file txt chứa thông tin sản phẩm từ database SQLite
    với định dạng rõ ràng và nhất quán cho RAG
    """
    conn = get_db_connection()
    if not conn:
        return

    try:
        cursor = conn.cursor()
        
        # Query để lấy thông tin sản phẩm kèm theo category và brand
        query = """
        SELECT 
            p.id,
            p.name,
            p.price,
            p.stock,
            p.number_of_sell,
            p.number_of_like,
            p.description,
            c.name as category_name,
            b.name as brand_name
        FROM frontend_product p
        LEFT JOIN frontend_category c ON p.category_id = c.id
        LEFT JOIN frontend_brand b ON p.brand_id = b.id
        """
        
        cursor.execute(query)
        products = cursor.fetchall()

        # Tạo thư mục docs nếu chưa tồn tại
        docs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'docs')
        if not os.path.exists(docs_dir):
            os.makedirs(docs_dir)
        
        # Mở file để ghi - định dạng chính (một file cho tất cả sản phẩm)
        with open(os.path.join(docs_dir, 'products.txt'), 'w', encoding='utf-8') as f:
            f.write("Cửa hàng tên là Nghĩa Thơm Audio. \n")
            f.write("Chúng tôi chuyên cung cấp các sản phẩm âm thanh chất lượng cao và các phụ kiện âm thanh. \n")
            f.write("Địa chỉ: 136 tổ 10, đường Cách Mạng Tháng 8, Thành phố Sông Công Thái Nguyên.\n")
            f.write("SĐT: 0912269059 \n")
            f.write("Email liên lạc: nghiathomsc@gmail.com.\n")
            f.write("Website: https://www.nghiathomsc.com. \n")
            f.write("Giờ làm việc: 8:00 - 17:00.\n")
            f.write("Chúng tôi cam kết cung cấp sản phẩm chất lượng cao và dịch vụ tốt nhất cho khách hàng. \n")
            f.write("Chúng tôi bán các mặt hàng dưới đây: ")
            for product in products:
                price = product['price']
                f.write(
                    f"\n"
                    f"- Tên sản phẩm là {product['name']} kèm theo mã sản phẩm là {product['id']} đây là sản phẩm nằm trong danh mục {product['category_name']} và hãng của sản phẩm là {product['brand_name']}, được bán với giá {price:,.0f} VNĐ, tổng số lượng chúng tôi đã bán ra là {product['number_of_sell']} sản phẩm với rất nhiều lượt yêu thích lên đến {product['number_of_like']} lượt yêu thích. "
                )
        
            
        print(f"- File tổng hợp: {os.path.join(docs_dir, 'products.txt')}")

    except sqlite3.Error as e:
        print(f"Lỗi khi truy vấn database: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    generate_product_data()