import os
import sqlite3
from datetime import datetime

class DataProcessor:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.data_dir = os.path.join(self.base_dir, 'chatbot_langchain', 'docs')
        
        # Tạo thư mục docs nếu chưa tồn tại
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
    def get_db_connection(self):
        """Kết nối với database SQLite"""
        try:
            db_path = os.path.join(self.base_dir, 'db.sqlite3')
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row  # Để có thể truy cập kết quả bằng tên cột
            return conn
        except sqlite3.Error as e:
            print(f"Lỗi kết nối database: {e}")
            return None
            
    def generate_product_data(self):
        """
        Tạo file products.txt chứa thông tin chi tiết sản phẩm
        từ database để AI Agent có thể truy xuất
        """
        conn = self.get_db_connection()
        if not conn:
            return "Lỗi kết nối database", 0
            
        products_file = os.path.join(self.data_dir, 'products.txt')
        
        try:
            cursor = conn.cursor()
            
            # Query để lấy thông tin sản phẩm, danh mục, thương hiệu
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
            product_count = len(products)
            
            # Ghi dữ liệu vào file
            with open(products_file, 'w', encoding='utf-8') as f:
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
                        f"Tên sản phẩm là {product['name']} kèm theo mã sản phẩm là {product['id']} đây là sản phẩm nằm trong danh mục {product['category_name']} là hãng của {product['brand_name']} với {product['number_of_like']} lượt thích và {product['number_of_sell']} lượt mua. Giá sản phẩm là {price:,.0f} VNĐ. "
                    )
            
            # Lưu thời gian cập nhật
            timestamp_file = os.path.join(self.data_dir, 'last_update.txt')
            with open(timestamp_file, 'w', encoding='utf-8') as f:
                f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                
            return f"Đã tạo dữ liệu cho {product_count} sản phẩm tại {products_file}", product_count
            
        except sqlite3.Error as e:
            return f"Lỗi khi truy vấn database: {e}", 0
        finally:
            conn.close()
            
    def save_custom_data(self, custom_data):
        """
        Lưu dữ liệu tùy chỉnh vào file custom_data.txt
        """
        custom_data_file = os.path.join(self.data_dir, 'custom_data.txt')
        
        try:
            with open(custom_data_file, 'w', encoding='utf-8') as f:
                f.write(custom_data)
                
            return f"Đã lưu dữ liệu tùy chỉnh tại {custom_data_file}"
        except Exception as e:
            return f"Lỗi khi lưu dữ liệu tùy chỉnh: {e}"
            
    def get_custom_data(self):
        """
        Đọc dữ liệu tùy chỉnh từ file custom_data.txt
        """
        custom_data_file = os.path.join(self.data_dir, 'custom_data.txt')
        
        if not os.path.exists(custom_data_file):
            return ""
            
        try:
            with open(custom_data_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Lỗi khi đọc dữ liệu tùy chỉnh: {e}")
            return ""
            
    def get_last_update_time(self):
        """
        Lấy thời gian cập nhật dữ liệu gần nhất
        """
        timestamp_file = os.path.join(self.data_dir, 'last_update.txt')
        
        if not os.path.exists(timestamp_file):
            return None
            
        try:
            with open(timestamp_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            print(f"Lỗi khi đọc thời gian cập nhật: {e}")
            return None
            
    def get_product_count(self):
        """
        Lấy số lượng sản phẩm trong database
        """
        conn = self.get_db_connection()
        if not conn:
            return 0
            
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM frontend_product")
            count = cursor.fetchone()[0]
            return count
        except sqlite3.Error as e:
            print(f"Lỗi khi đếm sản phẩm: {e}")
            return 0
        finally:
            conn.close() 