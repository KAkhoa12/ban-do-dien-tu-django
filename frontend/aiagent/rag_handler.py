import os
import json
import requests
import sqlite3
from datetime import datetime
import re
import logging

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("rag_handler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("RAGHandler")

class RAGHandler:
    def __init__(self, api_key=None, model=None, debug=False):
        """Khởi tạo với đường dẫn đến thư mục chứa dữ liệu"""
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.data_dir = os.path.join(self.base_dir, 'chatbot_langchain', 'docs')
        
        # Thông tin API Together.ai
        self.api_key = api_key or "75c9027a4aeca8e6415b7818ece22762cd806a3b7620e28f93c630e548d536b8"
        self.model = model or "deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free"
        self.api_url = "https://api.together.xyz/v1/completions"
        
        # Cấu hình cho embedding model
        self.embedding_model = "all-MiniLM-L6-v2"
        
        # Giới hạn token
        self.max_query_length = 500  # Giới hạn độ dài truy vấn
        self.max_total_tokens = 7168  # Giới hạn token tối đa của mô hình
        self.max_output_tokens = 1024  # Giới hạn token đầu ra
        self.token_estimator_ratio = 3.5  # Tỉ lệ ước tính ký tự:token
        
        # Danh sách các mức context size để thử
        self.context_sizes = [1500, 800, 400, 200, 0]
        
        # Danh sách các biến thể của lỗi token limit
        self.token_limit_errors = [
            'tokens', 
            'token limit', 
            'max_tokens', 
            'token + max_new',
            'input validation error',
            'too long'
        ]
        
        # Cache thông tin cửa hàng để tối ưu
        self.store_info_cache = self._load_store_info()
        
        # Chế độ debug
        self.debug = debug
        if self.debug:
            logger.setLevel(logging.DEBUG)
        
    def _load_store_info(self):
        """Tải trước thông tin cửa hàng từ các file để cache"""
        store_info = {
            'custom_data': "",
            'categories': [],
            'brands': [],
            'short_desc': "Nghĩa Thơm Audio - Chuyên cung cấp thiết bị âm thanh cao cấp."
        }
        
        # Đọc thông tin từ custom_data.txt
        try:
            custom_data_path = os.path.join(self.data_dir, 'custom_data.txt')
            if os.path.exists(custom_data_path):
                with open(custom_data_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    # Chuẩn hóa nội dung để đảm bảo format nhất quán
                    # Xóa khoảng trắng thừa và dòng trống
                    content_lines = [line.strip() for line in content.split('\n') if line.strip()]
                    store_info['custom_data'] = '\n'.join(content_lines)
                    
                    # Tìm kiếm thông tin quan trọng
                    store_info['name'] = "Nghĩa Thơm Audio"
                    for line in content_lines:
                        if "Địa chỉ:" in line:
                            store_info['address'] = line.replace("Địa chỉ:", "").strip()
                        elif "số điện thoại:" in line.lower() or "sđt:" in line.lower() or "điện thoại:" in line.lower():
                            store_info['phone'] = line.split(":", 1)[1].strip()
                        elif "Email" in line:
                            store_info['email'] = line.replace("Email liên lạc:", "").replace("Email:", "").strip().rstrip('.')
                        elif "Website:" in line:
                            store_info['website'] = line.replace("Website:", "").strip().rstrip('.')
                        elif "Giờ làm việc:" in line:
                            store_info['hours'] = line.replace("Giờ làm việc:", "").strip()
                    
                    logger.info("Đọc thành công thông tin từ custom_data.txt")
        except Exception as e:
            logger.error(f"Lỗi khi đọc file custom_data.txt: {e}")
            
        # Nếu không lấy được từ file, dùng thông tin mặc định
        if not store_info['custom_data']:
            store_info['custom_data'] = """Nghĩa Thơm Audio là cửa hàng chuyên cung cấp các sản phẩm âm thanh chất lượng cao và các phụ kiện âm thanh.
Địa chỉ: 136 tổ 10, đường Cách Mạng Tháng 8, Thành phố Sông Công Thái Nguyên.
SĐT: 0912269059
Email: nghiathomsc@gmail.com
Website: https://www.nghiathomsc.com
Giờ làm việc: 8:00 - 17:00."""
            
        # Phân tích danh mục và thương hiệu từ products.txt
        try:
            products_path = os.path.join(self.data_dir, 'products.txt')
            if os.path.exists(products_path):
                categories = set()
                brands = set()
                
                with open(products_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        
                        # Trích xuất thông tin danh mục và thương hiệu
                        category_match = re.search(r'trong danh mục\s+([^,]+)', line)
                        brand_match = re.search(r'hãng của\s+([^với]+)', line)
                        
                        if category_match and category_match.group(1).strip():
                            categories.add(category_match.group(1).strip())
                        
                        if brand_match and brand_match.group(1).strip():
                            brands.add(brand_match.group(1).strip())
                
                store_info['categories'] = list(categories)
                store_info['brands'] = list(brands)
        except Exception as e:
            logger.error(f"Lỗi khi phân tích file products.txt: {e}")
            
        # Tạo phiên bản medium description
        categories_text = ""
        brands_text = ""
        
        if store_info['categories']:
            top_categories = store_info['categories'][:5] if len(store_info['categories']) > 5 else store_info['categories']
            categories_text = "Chúng tôi có các danh mục sản phẩm: " + ", ".join(top_categories) + ".\n"
            
        if store_info['brands']:
            top_brands = store_info['brands'][:5] if len(store_info['brands']) > 5 else store_info['brands']
            brands_text = "Chúng tôi phân phối các thương hiệu: " + ", ".join(top_brands) + "."
            
        store_info['medium_desc'] = store_info['custom_data']
        if categories_text or brands_text:
            store_info['medium_desc'] += "\n\n" + categories_text + brands_text
            
        return store_info
    
    def get_db_connection(self):
        """Kết nối với database SQLite"""
        try:
            db_path = os.path.join(self.base_dir, 'db.sqlite3')
            
            # Kiểm tra xem file cơ sở dữ liệu có tồn tại không
            if not os.path.exists(db_path):
                logger.error(f"Không tìm thấy file cơ sở dữ liệu: {db_path}")
                return None
                
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row  # Để có thể truy cập kết quả bằng tên cột
            
            # Kiểm tra xem có thể truy vấn cơ sở dữ liệu hay không
            cursor = conn.cursor()
            cursor.execute("SELECT count(*) FROM sqlite_master")
            cursor.fetchone()
            
            # Ghi log thành công
            if self.debug:
                logger.debug(f"Kết nối thành công đến cơ sở dữ liệu: {db_path}")
                
            return conn
        except sqlite3.Error as e:
            logger.error(f"Lỗi kết nối database: {e}")
            return None
        except Exception as e:
            logger.error(f"Lỗi không xác định khi kết nối database: {e}")
            return None
    
    def get_context_from_files(self, max_length=3000):
        """Lấy context từ cache với độ dài phù hợp"""
        # Trả về phiên bản phù hợp dựa trên max_length
        if max_length < 300:
            return self.store_info_cache['short_desc']
            
        if max_length <= 1000:
            # Đảm bảo độ dài không vượt quá yêu cầu
            medium_desc = self.store_info_cache['medium_desc']
            if len(medium_desc) > max_length:
                return medium_desc[:max_length].rsplit('.', 1)[0] + "."
            return medium_desc
        
        # Với context dài, kết hợp nhiều thông tin
        context = self.store_info_cache['custom_data'] + "\n\n"
        remaining_length = max_length - len(context)
        
        # Thêm danh mục và thương hiệu nếu đủ không gian
        if remaining_length > 300:
            if self.store_info_cache['categories']:
                categories = self.store_info_cache['categories']
                context += "Chúng tôi có các danh mục sản phẩm: " + ", ".join(categories) + ".\n\n"
                
            remaining_length = max_length - len(context)
            if remaining_length > 200 and self.store_info_cache['brands']:
                brands = self.store_info_cache['brands']
                context += "Chúng tôi phân phối các thương hiệu: " + ", ".join(brands) + ".\n\n"
        
        # Cắt giảm nếu vượt quá độ dài tối đa
        if len(context) > max_length:
            context = context[:max_length].rsplit(' ', 1)[0] + "..."
            
        return context
    
    def get_top_selling_products(self, limit=5):
        """Lấy danh sách sản phẩm bán chạy nhất"""
        conn = self.get_db_connection()
        if not conn:
            logger.error("Không thể kết nối đến cơ sở dữ liệu để lấy sản phẩm bán chạy")
            return "Không thể kết nối đến cơ sở dữ liệu."
        
        try:
            cursor = conn.cursor()
            # Giới hạn số lượng sản phẩm hợp lý
            limit = min(max(1, limit), 10)
            
            query = """
            SELECT 
                p.id,
                p.name,
                p.price,
                p.number_of_sell,
                c.name as category_name,
                b.name as brand_name
            FROM frontend_product p
            LEFT JOIN frontend_category c ON p.category_id = c.id
            LEFT JOIN frontend_brand b ON p.brand_id = b.id
            ORDER BY p.number_of_sell DESC
            LIMIT ?
            """
            cursor.execute(query, (limit,))
            products = cursor.fetchall()
            
            if not products:
                logger.warning("Không tìm thấy sản phẩm bán chạy nào")
                return "Hiện tại không có thông tin về sản phẩm bán chạy."
                
            # Ghi log số lượng sản phẩm tìm được
            if self.debug:
                logger.debug(f"Đã tìm thấy {len(products)} sản phẩm bán chạy nhất")
                
            result = "Các sản phẩm bán chạy nhất:\n"
            for i, product in enumerate(products, 1):
                result += f"{i}. {product['name']} - Thương hiệu: {product['brand_name']} - Danh mục: {product['category_name']} - Giá: {product['price']:,.0f} VNĐ - Số lượng đã bán: {product['number_of_sell']}\n"
                
            return result
        except sqlite3.Error as e:
            logger.error(f"Lỗi khi truy vấn sản phẩm bán chạy: {e}")
            return f"Lỗi khi truy vấn sản phẩm bán chạy: {e}"
        finally:
            conn.close()
    
    def get_top_liked_products(self, limit=5):
        """Lấy danh sách sản phẩm được yêu thích nhất"""
        conn = self.get_db_connection()
        if not conn:
            logger.error("Không thể kết nối đến cơ sở dữ liệu để lấy sản phẩm yêu thích")
            return "Không thể kết nối đến cơ sở dữ liệu."
        
        try:
            cursor = conn.cursor()
            # Giới hạn số lượng sản phẩm hợp lý
            limit = min(max(1, limit), 10)
            
            query = """
            SELECT 
                p.id,
                p.name,
                p.price,
                p.number_of_like,
                c.name as category_name,
                b.name as brand_name
            FROM frontend_product p
            LEFT JOIN frontend_category c ON p.category_id = c.id
            LEFT JOIN frontend_brand b ON p.brand_id = b.id
            ORDER BY p.number_of_like DESC
            LIMIT ?
            """
            cursor.execute(query, (limit,))
            products = cursor.fetchall()
            
            if not products:
                logger.warning("Không tìm thấy sản phẩm được yêu thích nào")
                return "Hiện tại không có thông tin về sản phẩm được yêu thích."
                
            # Ghi log số lượng sản phẩm tìm được
            if self.debug:
                logger.debug(f"Đã tìm thấy {len(products)} sản phẩm được yêu thích nhất")
                
            result = "Các sản phẩm được yêu thích nhất:\n"
            for i, product in enumerate(products, 1):
                result += f"{i}. {product['name']} - Thương hiệu: {product['brand_name']} - Danh mục: {product['category_name']} - Giá: {product['price']:,.0f} VNĐ - Lượt thích: {product['number_of_like']}\n"
                
            return result
        except sqlite3.Error as e:
            logger.error(f"Lỗi khi truy vấn sản phẩm yêu thích: {e}")
            return f"Lỗi khi truy vấn sản phẩm yêu thích: {e}"
        finally:
            conn.close()
    
    def get_least_selling_products(self, limit=5):
        """Lấy danh sách sản phẩm bán ít nhất"""
        conn = self.get_db_connection()
        if not conn:
            logger.error("Không thể kết nối đến cơ sở dữ liệu để lấy sản phẩm bán ít")
            return "Không thể kết nối đến cơ sở dữ liệu."
        
        try:
            cursor = conn.cursor()
            # Giới hạn số lượng sản phẩm hợp lý
            limit = min(max(1, limit), 10)
            
            query = """
            SELECT 
                p.id,
                p.name,
                p.price,
                p.number_of_sell,
                c.name as category_name,
                b.name as brand_name
            FROM frontend_product p
            LEFT JOIN frontend_category c ON p.category_id = c.id
            LEFT JOIN frontend_brand b ON p.brand_id = b.id
            ORDER BY p.number_of_sell ASC
            LIMIT ?
            """
            cursor.execute(query, (limit,))
            products = cursor.fetchall()
            
            if not products:
                logger.warning("Không tìm thấy sản phẩm bán ít nào")
                return "Hiện tại không có thông tin về sản phẩm bán ít."
                
            # Ghi log số lượng sản phẩm tìm được
            if self.debug:
                logger.debug(f"Đã tìm thấy {len(products)} sản phẩm bán ít nhất")
                
            result = "Các sản phẩm bán ít nhất:\n"
            for i, product in enumerate(products, 1):
                result += f"{i}. {product['name']} - Thương hiệu: {product['brand_name']} - Danh mục: {product['category_name']} - Giá: {product['price']:,.0f} VNĐ - Số lượng đã bán: {product['number_of_sell']}\n"
                
            return result
        except sqlite3.Error as e:
            logger.error(f"Lỗi khi truy vấn sản phẩm bán ít: {e}")
            return f"Lỗi khi truy vấn sản phẩm bán ít: {e}"
        finally:
            conn.close()
    
    def verify_product(self, product_name_or_id):
        """Kiểm tra xem sản phẩm có tồn tại trong cơ sở dữ liệu không
        
        Args:
            product_name_or_id: Tên hoặc ID của sản phẩm cần kiểm tra
            
        Returns:
            bool: True nếu sản phẩm tồn tại, False nếu không
        """
        conn = self.get_db_connection()
        if not conn:
            logger.error("Không thể kết nối đến cơ sở dữ liệu để xác minh sản phẩm")
            return False
            
        try:
            cursor = conn.cursor()
            # Tìm bằng ID nếu là số
            if isinstance(product_name_or_id, (int, str)) and str(product_name_or_id).isdigit():
                query = "SELECT id FROM frontend_product WHERE id = ?"
                cursor.execute(query, (int(product_name_or_id),))
            else:
                # Tìm bằng tên (tìm kiếm chính xác hoặc gần đúng)
                query = "SELECT id FROM frontend_product WHERE name LIKE ?"
                cursor.execute(query, (f"%{product_name_or_id}%",))
                
            result = cursor.fetchone()
            return result is not None
        except sqlite3.Error as e:
            logger.error(f"Lỗi khi xác minh sản phẩm: {e}")
            return False
        finally:
            conn.close()
    
    def get_product_by_name_or_id(self, product_identifier):
        """Lấy thông tin sản phẩm theo tên hoặc ID"""
        conn = self.get_db_connection()
        if not conn:
            return "Không thể kết nối đến cơ sở dữ liệu."
        
        try:
            cursor = conn.cursor()
            # Thử tìm bằng ID nếu là số
            if product_identifier.isdigit():
                query = """
                SELECT 
                    p.id,
                    p.name,
                    p.price,
                    p.description,
                    p.number_of_sell,
                    p.number_of_like,
                    c.name as category_name,
                    b.name as brand_name
                FROM frontend_product p
                LEFT JOIN frontend_category c ON p.category_id = c.id
                LEFT JOIN frontend_brand b ON p.brand_id = b.id
                WHERE p.id = ?
                """
                cursor.execute(query, (int(product_identifier),))
            else:
                # Tìm bằng tên (tìm kiếm gần đúng)
                query = """
                SELECT 
                    p.id,
                    p.name,
                    p.price,
                    p.description,
                    p.number_of_sell,
                    p.number_of_like,
                    c.name as category_name,
                    b.name as brand_name
                FROM frontend_product p
                LEFT JOIN frontend_category c ON p.category_id = c.id
                LEFT JOIN frontend_brand b ON p.brand_id = b.id
                WHERE p.name LIKE ?
                """
                cursor.execute(query, (f"%{product_identifier}%",))
            
            product = cursor.fetchone()
            
            if not product:
                # Ghi log để theo dõi việc tìm kiếm không thành công
                logger.warning(f"Không tìm thấy sản phẩm với thông tin: {product_identifier}")
                return f"Không tìm thấy sản phẩm với thông tin: {product_identifier}"
            
            # Ghi log khi tìm thấy sản phẩm
            if self.debug:
                logger.debug(f"Đã tìm thấy sản phẩm: ID={product['id']}, Tên={product['name']}")
                
            result = f"Thông tin sản phẩm:\n"
            result += f"- Tên: {product['name']}\n"
            result += f"- Mã sản phẩm: {product['id']}\n"
            result += f"- Thương hiệu: {product['brand_name']}\n"
            result += f"- Danh mục: {product['category_name']}\n"
            result += f"- Giá: {product['price']:,.0f} VNĐ\n"
            result += f"- Số lượng đã bán: {product['number_of_sell']}\n"
            result += f"- Lượt thích: {product['number_of_like']}\n"
            if product['description']:
                result += f"- Mô tả: {product['description']}\n"
                
            return result
        except sqlite3.Error as e:
            logger.error(f"Lỗi khi truy vấn sản phẩm: {e}")
            return f"Lỗi khi truy vấn sản phẩm: {e}"
        finally:
            conn.close()
    
    def compare_products(self, product1_identifier, product2_identifier):
        """So sánh hai sản phẩm"""
        # Kiểm tra sản phẩm có tồn tại không trước khi truy vấn chi tiết
        if not self.verify_product(product1_identifier):
            logger.warning(f"Không tìm thấy sản phẩm để so sánh: {product1_identifier}")
            return f"Không tìm thấy sản phẩm với thông tin: {product1_identifier}"
            
        if not self.verify_product(product2_identifier):
            logger.warning(f"Không tìm thấy sản phẩm để so sánh: {product2_identifier}")
            return f"Không tìm thấy sản phẩm với thông tin: {product2_identifier}"
            
        conn = self.get_db_connection()
        if not conn:
            return "Không thể kết nối đến cơ sở dữ liệu."
        
        product1_info = None
        product2_info = None
        
        try:
            cursor = conn.cursor()
            
            # Hàm để truy vấn sản phẩm
            def get_product(identifier):
                # Thử tìm bằng ID nếu là số
                if identifier.isdigit():
                    query = """
                    SELECT 
                        p.id,
                        p.name,
                        p.price,
                        p.description,
                        p.number_of_sell,
                        p.number_of_like,
                        c.name as category_name,
                        b.name as brand_name
                    FROM frontend_product p
                    LEFT JOIN frontend_category c ON p.category_id = c.id
                    LEFT JOIN frontend_brand b ON p.brand_id = b.id
                    WHERE p.id = ?
                    """
                    cursor.execute(query, (int(identifier),))
                else:
                    # Tìm bằng tên (tìm kiếm gần đúng)
                    query = """
                    SELECT 
                        p.id,
                        p.name,
                        p.price,
                        p.description,
                        p.number_of_sell,
                        p.number_of_like,
                        c.name as category_name,
                        b.name as brand_name
                    FROM frontend_product p
                    LEFT JOIN frontend_category c ON p.category_id = c.id
                    LEFT JOIN frontend_brand b ON p.brand_id = b.id
                    WHERE p.name LIKE ?
                    """
                    cursor.execute(query, (f"%{identifier}%",))
                
                return cursor.fetchone()
            
            # Truy vấn thông tin sản phẩm
            product1_info = get_product(product1_identifier)
            product2_info = get_product(product2_identifier)
            
            if not product1_info:
                logger.warning(f"Không tìm thấy sản phẩm để so sánh: {product1_identifier}")
                return f"Không tìm thấy sản phẩm với thông tin: {product1_identifier}"
            
            if not product2_info:
                logger.warning(f"Không tìm thấy sản phẩm để so sánh: {product2_identifier}")
                return f"Không tìm thấy sản phẩm với thông tin: {product2_identifier}"
            
            # Ghi log sản phẩm tìm thấy
            if self.debug:
                logger.debug(f"So sánh sản phẩm: {product1_info['name']} vs {product2_info['name']}")
                
            # So sánh hai sản phẩm
            result = f"So sánh sản phẩm:\n\n"
            result += f"| Thông tin | {product1_info['name']} | {product2_info['name']} |\n"
            result += f"|------------|------------|------------|\n"
            result += f"| Mã sản phẩm | {product1_info['id']} | {product2_info['id']} |\n"
            result += f"| Thương hiệu | {product1_info['brand_name']} | {product2_info['brand_name']} |\n"
            result += f"| Danh mục | {product1_info['category_name']} | {product2_info['category_name']} |\n"
            result += f"| Giá | {product1_info['price']:,.0f} VNĐ | {product2_info['price']:,.0f} VNĐ |\n"
            result += f"| Số lượng đã bán | {product1_info['number_of_sell']} | {product2_info['number_of_sell']} |\n"
            result += f"| Lượt thích | {product1_info['number_of_like']} | {product2_info['number_of_like']} |\n"
            
            # Thêm đánh giá tổng quan
            price_diff = abs(product1_info['price'] - product2_info['price'])
            price_diff_percent = (price_diff / max(product1_info['price'], product2_info['price'])) * 100
            
            result += f"\nĐánh giá tổng quan:\n"
            result += f"- Chênh lệch giá: {price_diff:,.0f} VNĐ (~{price_diff_percent:.1f}%)\n"
            
            if product1_info['number_of_sell'] > product2_info['number_of_sell']:
                result += f"- {product1_info['name']} bán chạy hơn với {product1_info['number_of_sell']} lượt bán so với {product2_info['number_of_sell']} của {product2_info['name']}\n"
            elif product1_info['number_of_sell'] < product2_info['number_of_sell']:
                result += f"- {product2_info['name']} bán chạy hơn với {product2_info['number_of_sell']} lượt bán so với {product1_info['number_of_sell']} của {product1_info['name']}\n"
            else:
                result += f"- Cả hai sản phẩm có số lượng bán bằng nhau: {product1_info['number_of_sell']} lượt bán\n"
            
            if product1_info['number_of_like'] > product2_info['number_of_like']:
                result += f"- {product1_info['name']} được yêu thích hơn với {product1_info['number_of_like']} lượt thích so với {product2_info['number_of_like']} của {product2_info['name']}\n"
            elif product1_info['number_of_like'] < product2_info['number_of_like']:
                result += f"- {product2_info['name']} được yêu thích hơn với {product2_info['number_of_like']} lượt thích so với {product1_info['number_of_like']} của {product1_info['name']}\n"
            else:
                result += f"- Cả hai sản phẩm có số lượt thích bằng nhau: {product1_info['number_of_like']} lượt thích\n"
            
            return result
        except sqlite3.Error as e:
            logger.error(f"Lỗi khi so sánh sản phẩm: {e}")
            return f"Lỗi khi so sánh sản phẩm: {e}"
        finally:
            conn.close()
    
    def _get_optimized_functions(self):
        """Định nghĩa các hàm tối ưu cho DeepSeek model"""
        return [
            {
                "name": "get_top_selling_products",
                "description": "Lấy danh sách sản phẩm bán chạy nhất tại cửa hàng. Sử dụng khi người dùng hỏi về sản phẩm bán chạy, phổ biến, được mua nhiều.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Số lượng sản phẩm muốn hiển thị (mặc định: 5, tối đa: 10)"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "get_top_liked_products",
                "description": "Lấy danh sách sản phẩm được yêu thích nhất tại cửa hàng. Sử dụng khi người dùng hỏi về sản phẩm được yêu thích, được đánh giá cao, nhận nhiều lượt thích.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Số lượng sản phẩm muốn hiển thị (mặc định: 5, tối đa: 10)"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "get_least_selling_products",
                "description": "Lấy danh sách sản phẩm bán ít nhất tại cửa hàng. Sử dụng khi người dùng hỏi về sản phẩm bán chậm, ít được mua.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Số lượng sản phẩm muốn hiển thị (mặc định: 5, tối đa: 10)"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "get_product_by_name_or_id",
                "description": "Tìm kiếm thông tin chi tiết về một sản phẩm cụ thể. QUAN TRỌNG: Sử dụng function này khi người dùng hỏi về thông tin, giá cả, thông số kỹ thuật của một sản phẩm cụ thể.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "product_identifier": {
                            "type": "string",
                            "description": "Tên hoặc mã sản phẩm cần tìm (bắt buộc). Nhập đúng tên/mã sản phẩm mà người dùng đang hỏi."
                        }
                    },
                    "required": ["product_identifier"]
                }
            },
            {
                "name": "compare_products",
                "description": "So sánh hai sản phẩm với nhau. Sử dụng function này khi người dùng muốn so sánh, phân biệt, hoặc chọn lựa giữa các sản phẩm.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "product1_identifier": {
                            "type": "string",
                            "description": "Tên hoặc mã sản phẩm thứ nhất (bắt buộc)"
                        },
                        "product2_identifier": {
                            "type": "string",
                            "description": "Tên hoặc mã sản phẩm thứ hai (bắt buộc)"
                        }
                    },
                    "required": ["product1_identifier", "product2_identifier"]
                }
            },
            {
                "name": "get_all_brands",
                "description": "Lấy danh sách tất cả các thương hiệu có tại cửa hàng. Sử dụng khi người dùng hỏi về các thương hiệu, hãng sản xuất mà cửa hàng phân phối.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Số lượng thương hiệu muốn hiển thị (mặc định: 20, tối đa: 50)"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "get_all_categories",
                "description": "Lấy danh sách tất cả các danh mục sản phẩm",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Số lượng danh mục muốn hiển thị (mặc định: 20, tối đa: 50)"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "get_products_by_brand",
                "description": "Lấy danh sách sản phẩm theo thương hiệu",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "brand_identifier": {
                            "type": "string",
                            "description": "Tên hoặc mã thương hiệu"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Số lượng sản phẩm muốn hiển thị (mặc định: 10, tối đa: 20)"
                        }
                    },
                    "required": ["brand_identifier"]
                }
            },
            {
                "name": "get_products_by_category",
                "description": "Lấy danh sách sản phẩm theo danh mục",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "category_identifier": {
                            "type": "string",
                            "description": "Tên hoặc mã danh mục"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Số lượng sản phẩm muốn hiển thị (mặc định: 10, tối đa: 20)"
                        }
                    },
                    "required": ["category_identifier"]
                }
            }
        ]

    def _estimate_tokens(self, text):
        """
        Ước tính số token trong văn bản. Đây là ước tính đơn giản dựa trên số ký tự.
        Cách chính xác nhất là sử dụng tokenizer của model nhưng điều đó tạo thêm phụ thuộc.
        """
        if not text:
            return 0
            
        # Tiếng Việt và Unicode thường cần nhiều token hơn
        return int(len(text) / self.token_estimator_ratio)
    
    def extract_content(self, response):
        """Trích xuất nội dung từ thẻ <answer></answer>"""
        if not response:
            return ""
            
        # Nếu không có thẻ <answer>, trả về nguyên văn
        if "<answer>" not in response:
            return response
            
        # Loại bỏ phần thinking trước khi lấy <answer>
        if "<think>" in response and "</think>" in response and "<answer>" in response:
            think_pattern = re.compile(r'<think>.*?</think>', re.DOTALL)
            response = think_pattern.sub('', response)
            
        # Trích xuất nội dung trong thẻ <answer>
        answer_pattern = re.compile(r'<answer>(.*?)</answer>', re.DOTALL)
        answer_match = answer_pattern.search(response)
        
        if answer_match:
            return answer_match.group(1).strip()
            
        return response

    def function_calling(self, query):
        """Xử lý truy vấn người dùng kết hợp RAG và function calling"""
        # Giới hạn độ dài query 
        if len(query) > self.max_query_length:
            query = query[:self.max_query_length - 3] + "..."
        
        # Đảm bảo query là chữ thường
        query_lower = query.lower()
        
        # Danh sách câu hỏi thông thường về cửa hàng
        simple_questions = [
            "bạn là ai", "cho mình hỏi", "bạn là gì", "bạn làm được gì", 
            "bạn có thể làm gì", "bạn giúp được gì", "giới thiệu về cửa hàng",
            "cửa hàng bán gì", "thông tin cửa hàng", "liên hệ", "địa chỉ",
            "số điện thoại", "sđt", "phone", "sdt", "đt", "điện thoại", "hotline",
            "email", "giờ làm việc", "nghĩa thơm audio là gì", "cho tôi số",
            "gọi điện", "số của", "gọi cho", "liên lạc", "website", "web"
        ]
        
        # Xử lý các trường hợp câu hỏi thông tin cụ thể về cửa hàng
        if "địa chỉ" in query_lower or "ở đâu" in query_lower or "chỗ nào" in query_lower:
            if 'address' in self.store_info_cache:
                return f"<answer>Địa chỉ của Nghĩa Thơm Audio là: {self.store_info_cache['address']}</answer>"
        
        if any(term in query_lower for term in ["số điện thoại", "sđt", "phone", "sdt", "đt", "điện thoại", "hotline", "cho tôi số", "gọi điện"]):
            if 'phone' in self.store_info_cache:
                return f"<answer>Số điện thoại của Nghĩa Thơm Audio là: {self.store_info_cache['phone']}</answer>"
        
        if "email" in query_lower or "thư điện tử" in query_lower or "mail" in query_lower:
            if 'email' in self.store_info_cache:
                return f"<answer>Email liên hệ của Nghĩa Thơm Audio là: {self.store_info_cache['email']}</answer>"
        
        if "giờ làm việc" in query_lower or "mở cửa" in query_lower or "đóng cửa" in query_lower or "thời gian" in query_lower:
            if 'hours' in self.store_info_cache:
                return f"<answer>Giờ làm việc của Nghĩa Thơm Audio là: {self.store_info_cache['hours']}</answer>"
        
        if "website" in query_lower or "trang web" in query_lower or "web" in query_lower or "online" in query_lower:
            if 'website' in self.store_info_cache:
                return f"<answer>Website của Nghĩa Thơm Audio là: {self.store_info_cache['website']}</answer>"
        
        # Xác định nếu là câu hỏi thông thường khác
        is_simple_query = any(sq in query_lower for sq in simple_questions)
        
        if is_simple_query:
            # Sử dụng RAG đơn giản không cần function calling
            return self._handle_simple_query(query)
        
        # Xử lý câu hỏi phức tạp với RAG + function calling
        return self._handle_complex_query(query)
        
    def _handle_simple_query(self, query):
        """Xử lý câu hỏi đơn giản về cửa hàng sử dụng RAG"""
        # Sử dụng cache thông tin cửa hàng để đảm bảo tốc độ phản hồi
        store_info = self.store_info_cache['medium_desc']
        
        system_prompt = f"""<<SYS>>
Bạn là trợ lý ảo của Nghĩa Thơm Audio - cửa hàng âm thanh.

THÔNG TIN:
{store_info}

QUY TẮC:
- Trả lời ngắn gọn, bằng tiếng Việt
- Chỉ dùng thông tin đã cung cấp
- Không thêm thông tin không có trong dữ liệu
- KHÔNG hiển thị quá trình suy nghĩ, chỉ đưa ra câu trả lời cuối cùng
- Chỉ đặt câu trả lời trong thẻ <answer></answer>
<</SYS>>"""

        user_prompt = f"[INST]{query}[/INST]"
        
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        # Gửi yêu cầu đến API
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "max_tokens": self.max_output_tokens,
            "temperature": 0.3,
            "top_p": 0.95,
            "repetition_penalty": 1.2,
            # Đảm bảo không sử dụng tool cho câu hỏi đơn giản
            "tool_choice": "none"
        }
        
        try:
            # Ghi log truy vấn
            if self.debug:
                logger.debug(f"Xử lý câu hỏi đơn giản: {query}")
                
            # Gửi request và lấy phản hồi
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=20)
            response_json = response.json()
            
            if "choices" in response_json and len(response_json["choices"]) > 0:
                answer = response_json["choices"][0].get("text", "")
                if answer:
                    # Ghi log phản hồi thành công
                    if self.debug:
                        logger.debug(f"Phản hồi câu hỏi đơn giản thành công: {len(answer)} ký tự")
                    
                    # Đảm bảo phản hồi nằm trong thẻ answer
                    if not answer.startswith("<answer>"):
                        answer = f"<answer>{answer.strip()}</answer>"
                    if not answer.endswith("</answer>"):
                        answer = f"{answer}</answer>"
                        
                    return answer
            
            # Xử lý lỗi không có phản hồi hợp lệ
            logger.warning("Không thể lấy phản hồi từ API cho câu hỏi đơn giản")
            return "<answer>Xin lỗi, tôi không thể xử lý yêu cầu của bạn lúc này. Vui lòng thử lại sau.</answer>"
            
        except Exception as e:
            logger.error(f"Lỗi khi xử lý câu hỏi đơn giản: {e}")
            return "<answer>Xin lỗi, đã xảy ra lỗi khi xử lý yêu cầu của bạn.</answer>"
    
    def _handle_complex_query(self, query):
        """Xử lý câu hỏi phức tạp kết hợp RAG và function calling"""
        # Phân loại truy vấn để quyết định cách xử lý phù hợp
        query_type, info_needed = self._classify_query(query)
        
        # Thử với các context size khác nhau
        for context_size in self.context_sizes:
            try:
                # Lấy context với kích thước phù hợp
                context = self.get_context_from_files(max_length=context_size) if context_size > 0 else ""
                
                # Tạo system prompt dựa trên loại truy vấn
                if context:
                    system_prompt = f"""<<SYS>>
Bạn là trợ lý ảo của Nghĩa Thơm Audio.

THÔNG TIN: {context}

QUY TẮC:
- Câu hỏi về cửa hàng: Trả lời từ THÔNG TIN (địa chỉ, SĐT, giờ làm việc)
- Câu hỏi về sản phẩm: Dùng FUNCTION phù hợp
- Trả lời ngắn gọn, bằng tiếng Việt
- KHÔNG hiển thị quá trình suy nghĩ (<think>), chỉ đưa ra câu trả lời cuối cùng
- Chỉ đặt câu trả lời trong thẻ <answer></answer>
<</SYS>>"""
                else:
                    system_prompt = """<<SYS>>
Bạn là trợ lý ảo của Nghĩa Thơm Audio.

QUY TẮC:
- Sử dụng FUNCTION cho mọi câu hỏi về sản phẩm/danh mục/thương hiệu
- Trả lời ngắn gọn, bằng tiếng Việt
- KHÔNG hiển thị quá trình suy nghĩ (<think>), chỉ đưa ra câu trả lời cuối cùng
- Chỉ đặt câu trả lời trong thẻ <answer></answer>
<</SYS>>"""

                # Thêm hướng dẫn cụ thể cho loại truy vấn trong user prompt
                instruction = ""
                forced_tool_choice = None
                
                if query_type == "store_info":
                    instruction = "Đây là câu hỏi về thông tin cửa hàng. Trả lời từ thông tin, không dùng function."
                
                elif query_type == "product_specific":
                    instruction = "Sử dụng function để lấy thông tin chính xác."
                    
                    if info_needed == "product_detail":
                        instruction = "Sử dụng get_product_by_name_or_id"
                        forced_tool_choice = "get_product_by_name_or_id"
                    
                    elif info_needed == "top_selling":
                        instruction = "Sử dụng get_top_selling_products"
                        forced_tool_choice = "get_top_selling_products"
                    
                    elif info_needed == "top_liked":
                        instruction = "Sử dụng get_top_liked_products"
                        forced_tool_choice = "get_top_liked_products"
                    
                    elif info_needed == "compare_products":
                        instruction = "Sử dụng compare_products"
                        forced_tool_choice = "compare_products"
                
                elif query_type == "product_list":
                    instruction = "Sử dụng function để lấy danh sách."
                    
                    if info_needed == "brand_products" or info_needed == "brand_products_general":
                        instruction = "Sử dụng get_products_by_brand"
                        forced_tool_choice = "get_products_by_brand"
                    
                    elif info_needed == "category_products" or info_needed == "category_products_general":
                        instruction = "Sử dụng get_products_by_category"
                        forced_tool_choice = "get_products_by_category"
                    
                    elif info_needed == "brand":
                        instruction = "Sử dụng get_all_brands"
                        forced_tool_choice = "get_all_brands"
                    
                    elif info_needed == "category":
                        instruction = "Sử dụng get_all_categories"
                        forced_tool_choice = "get_all_categories"
                
                # Tạo user prompt đơn giản hơn
                user_prompt = f"[INST]{query}\n\n{instruction}[/INST]"
                
                full_prompt = f"{system_prompt}\n\n{user_prompt}"
                
                # Kiểm tra xem prompt có vượt quá giới hạn token không
                estimated_tokens = self._estimate_tokens(full_prompt)
                if estimated_tokens > (self.max_total_tokens - self.max_output_tokens - 100) and context_size > 0:
                    continue  # Thử với context nhỏ hơn
                
                # Chuẩn bị request
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": self.model,
                    "prompt": full_prompt,
                    "max_tokens": self.max_output_tokens,
                    "temperature": 0.3,
                    "top_p": 0.95,
                    "tools": self._get_optimized_functions(),
                    "repetition_penalty": 1.2
                }
                
                # Điều chỉnh tool_choice dựa trên loại truy vấn và info_needed
                if query_type == "store_info":
                    # KHÔNG sử dụng tool cho thông tin cửa hàng
                    payload["tool_choice"] = "none"
                elif query_type == "product_specific" or query_type == "product_list":
                    # BUỘC sử dụng tool cho truy vấn về sản phẩm
                    if forced_tool_choice:
                        payload["tool_choice"] = {"type": "function", "function": {"name": forced_tool_choice}}
                    else:
                        payload["tool_choice"] = {"type": "function"}
                else:
                    # Cho model tự quyết định
                    payload["tool_choice"] = "auto"
                    
                # Gửi request
                response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
                response_json = response.json()
                
                # Xử lý lỗi token limit
                if 'error' in response_json:
                    error_msg = response_json['error'].get('message', '').lower()
                    if any(err in error_msg for err in self.token_limit_errors) and context_size > 0:
                        continue  # Thử với context nhỏ hơn
                
                # Xử lý kết quả
                if "choices" in response_json and len(response_json["choices"]) > 0:
                    choice = response_json["choices"][0]
                    
                    # Trường hợp có text trực tiếp (không sử dụng tool)
                    if "text" in choice and (not choice.get("tool_calls") or len(choice.get("tool_calls", [])) == 0):
                        # Nếu query_type yêu cầu sử dụng tool nhưng model không sử dụng
                        if (query_type == "product_specific" or query_type == "product_list") and forced_tool_choice and context_size > 0:
                            # Thử lại với tool_choice mạnh hơn và loại bỏ context
                            try:
                                # Loại bỏ context để buộc model sử dụng tool
                                new_system_prompt = """<<SYS>>
Bạn là trợ lý ảo của Nghĩa Thơm Audio.
Bạn PHẢI SỬ DỤNG FUNCTION để lấy thông tin sản phẩm chính xác.
<</SYS>>"""

                                new_user_prompt = f"[INST]{query}\n\nSử dụng FUNCTION {forced_tool_choice}[/INST]"

                                new_full_prompt = f"{new_system_prompt}\n\n{new_user_prompt}"
                                
                                payload["prompt"] = new_full_prompt
                                payload["tool_choice"] = {"type": "function", "function": {"name": forced_tool_choice}}
                                
                                response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
                                response_json = response.json()
                                
                                if "choices" in response_json and len(response_json["choices"]) > 0:
                                    choice = response_json["choices"][0]
                                    
                                    # Nếu lần này dùng tool, xử lý tool call
                                    if "tool_calls" in choice and len(choice["tool_calls"]) > 0:
                                        return self._process_tool_call(choice["tool_calls"][0])
                                    # Nếu vẫn không dùng tool, sử dụng text response
                                    else:
                                        text_response = choice.get("text", "").strip()
                                        if not text_response:
                                            # Thất bại, sử dụng câu trả lời ban đầu
                                            text_response = response_json["choices"][0].get("text", "").strip()
                            except Exception as e:
                                logger.error(f"Lỗi khi thử buộc sử dụng tool: {e}")
                                # Sử dụng text response ban đầu nếu có lỗi
                                text_response = choice["text"].strip()
                        else:
                            # Sử dụng text response trực tiếp cho các loại truy vấn khác
                            text_response = choice["text"].strip()
                        
                        # Đảm bảo response được bọc trong thẻ answer
                        if not text_response.startswith("<answer>"):
                            text_response = f"<answer>{text_response}</answer>"
                        if not text_response.endswith("</answer>"):
                            text_response = f"{text_response}</answer>"
                            
                        return text_response
                    
                    # Trường hợp có tool calls
                    if "tool_calls" in choice and len(choice["tool_calls"]) > 0:
                        return self._process_tool_call(choice["tool_calls"][0])
                
                # Nếu không có kết quả phù hợp, thử với context nhỏ hơn
                if context_size > 0:
                    continue
                
                # Trả lời mặc định nếu không thành công
                return "<answer>Xin lỗi, tôi không thể tìm thấy thông tin phù hợp với yêu cầu của bạn.</answer>"
                
            except Exception as e:
                logger.error(f"Lỗi trong _handle_complex_query: {str(e)}")
                if context_size > 0:
                    continue  # Thử với context nhỏ hơn
        
        # Trả lời mặc định nếu tất cả các nỗ lực đều thất bại
        return "<answer>Xin lỗi, tôi không thể xử lý yêu cầu của bạn lúc này. Vui lòng thử lại sau.</answer>"

    def _classify_query(self, query):
        """
        Phân loại truy vấn để quyết định cách xử lý phù hợp
        
        Args:
            query (str): Truy vấn của người dùng
        
        Returns:
            tuple: (query_type, info_needed)
                query_type: 
                    - "store_info": Thông tin cửa hàng (địa chỉ, liên hệ, giờ làm việc...)
                    - "product_specific": Thông tin về sản phẩm cụ thể (giá, thông số...)
                    - "product_list": Danh sách sản phẩm (theo danh mục, thương hiệu...)
                    - "general_info": Thông tin chung (không thuộc các loại trên)
                info_needed: Loại thông tin cụ thể cần lấy
        """
        query = query.lower()
        
        # Tối ưu danh sách từ khóa cho mỗi loại truy vấn
        store_info_keywords = [
            "địa chỉ", "sđt", "số điện thoại", "liên hệ", "email", "giờ làm việc", 
            "cửa hàng", "ở đâu", "website", "mở cửa", "đóng cửa", "nghĩa thơm",
            "chỉ đường", "bản đồ", "địa điểm", "chính sách", "bảo hành", "đổi trả",
            "phương thức thanh toán", "thanh toán", "giao hàng", "vận chuyển"
        ]
        
        product_specific_keywords = [
            "giá", "thông số", "chi tiết", "cấu hình", "đặc điểm", 
            "mô tả", "tính năng", "chức năng", "bảo hành", "khuyến mãi",
            "sản phẩm", "thiết bị", "đánh giá", "review", "còn hàng", "tồn kho",
            "xuất xứ", "nhập khẩu", "chính hãng", "hàng chính hãng", "so sánh"
        ]
        
        product_list_keywords = [
            "danh sách", "liệt kê", "có những", "tất cả", "toàn bộ", 
            "các loại", "các sản phẩm", "những sản phẩm", "các thiết bị", 
            "những thiết bị", "sản phẩm nào", "thiết bị nào",
            "sản phẩm gì", "thiết bị gì", "cho xem", "giới thiệu"
        ]
        
        brand_keywords = [
            "thương hiệu", "hãng", "nhà sản xuất", "brand", "hiệu", "công ty",
            "sản xuất", "của", "nhãn hiệu", "tập đoàn", "hãng sản xuất"
        ]
        
        category_keywords = [
            "loại", "danh mục", "phân loại", "category", "chủng loại", 
            "kiểu", "dòng", "nhóm", "phân nhóm", "phân khúc"
        ]
        
        # Từ khóa về sản phẩm bán chạy và được yêu thích
        top_selling_keywords = [
            "bán chạy", "hot", "phổ biến", "nhiều người mua", "bán nhiều nhất",
            "bán tốt nhất", "bán chạy nhất", "xu hướng", "thịnh hành", "được ưa chuộng",
            "được mua nhiều"
        ]
        
        top_liked_keywords = [
            "yêu thích", "ưa chuộng", "đánh giá cao", "nhiều người thích", "lượt thích cao",
            "review tốt", "được ưa thích", "review cao", "đánh giá tốt", "yêu thích nhất"
        ]
        
        compare_keywords = [
            "so sánh", "phân biệt", "khác nhau", "khác biệt", "khác gì", "tốt hơn",
            "nên mua", "nên chọn", "chọn cái nào", "đắt hơn", "rẻ hơn", "tốt hay",
            "hơn kém", "ưu điểm", "nhược điểm", "hơn"
        ]
        
        # Kiểm tra xem trong câu hỏi có tên sản phẩm cụ thể không
        has_specific_product = False
        conn = self.get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT name FROM frontend_product")
                products = cursor.fetchall()
                
                # Tách các từ trong câu hỏi
                query_tokens = query.split()
                
                # Kiểm tra sự xuất hiện của tên sản phẩm trong câu hỏi
                for product in products:
                    product_name = product[0].lower()
                    if product_name in query:
                        has_specific_product = True
                        break
                        
                    # Kiểm tra sự xuất hiện một phần của tên sản phẩm
                    # Chỉ xét các tên sản phẩm có ít nhất 2 từ
                    product_tokens = product_name.split()
                    if len(product_tokens) >= 2:
                        for i in range(len(product_tokens) - 1):
                            partial_name = " ".join(product_tokens[i:i+2])
                            if partial_name in query and len(partial_name) > 5:  # Tránh trùng các từ chung như "the", "và", ...
                                has_specific_product = True
                                break
                
            except Exception as e:
                logger.error(f"Lỗi khi kiểm tra tên sản phẩm cụ thể: {e}")
            finally:
                conn.close()
        
        # Phát hiện loại truy vấn
        is_store_info = any(keyword in query for keyword in store_info_keywords)
        is_product_specific = any(keyword in query for keyword in product_specific_keywords) or has_specific_product
        is_product_list = any(keyword in query for keyword in product_list_keywords)
        is_compare = any(keyword in query for keyword in compare_keywords)
        
        # Phát hiện loại thông tin cần lấy
        info_needed = None
        
        # Kiểm tra so sánh sản phẩm (ưu tiên cao nhất)
        if is_compare:
            info_needed = "compare_products"
            return "product_specific", info_needed
            
        # Kiểm tra các loại thông tin khác
        if any(keyword in query for keyword in brand_keywords):
            if is_product_list:
                brand = self.extract_specific_brand(query)
                info_needed = "brand_products" if brand else "brand_products_general"
            else:
                info_needed = "brand"
        elif any(keyword in query for keyword in category_keywords):
            if is_product_list:
                category = self.extract_specific_category(query)
                info_needed = "category_products" if category else "category_products_general"
            else:
                info_needed = "category"
        elif any(keyword in query for keyword in top_selling_keywords):
            info_needed = "top_selling"
        elif any(keyword in query for keyword in top_liked_keywords):
            info_needed = "top_liked"
            
        # Quyết định loại truy vấn dựa trên các đặc điểm đã phát hiện
        
        # Nếu có tên sản phẩm cụ thể, ưu tiên phân loại là product_specific
        if has_specific_product:
            # Nếu là so sánh, đã xử lý ở trên
            if not info_needed:
                info_needed = "product_detail"
            return "product_specific", info_needed
            
        # Xử lý theo thứ tự ưu tiên
        if is_store_info and not is_product_specific and not is_product_list:
            return "store_info", info_needed
        elif is_product_specific or info_needed in ["top_selling", "top_liked", "compare_products", "product_detail"]:
            return "product_specific", info_needed
        elif is_product_list or info_needed in ["brand_products", "category_products", "brand_products_general", "category_products_general"]:
            return "product_list", info_needed
        else:
            return "general_info", info_needed

    def _process_tool_call(self, tool_call):
        """Xử lý tool call từ response của model"""
        try:
            function_name = tool_call["function"]["name"]
            
            try:
                function_args = json.loads(tool_call["function"]["arguments"])
            except json.JSONDecodeError:
                logger.error(f"Không thể xử lý tham số hàm: {tool_call['function']['arguments']}")
                return "<answer>Lỗi: Không thể xử lý tham số hàm.</answer>"
            
            # Ghi log tool call
            if self.debug:
                logger.debug(f"Tool call: {function_name} với tham số {function_args}")
            
            # Thực hiện function call
            if function_name == "get_top_selling_products":
                limit = min(max(1, function_args.get("limit", 5)), 10)
                result = self.get_top_selling_products(limit)
                return f"<answer>{result}</answer>"
            
            elif function_name == "get_top_liked_products":
                limit = min(max(1, function_args.get("limit", 5)), 10)
                result = self.get_top_liked_products(limit)
                return f"<answer>{result}</answer>"
            
            elif function_name == "get_least_selling_products":
                limit = min(max(1, function_args.get("limit", 5)), 10)
                result = self.get_least_selling_products(limit)
                return f"<answer>{result}</answer>"
            
            elif function_name == "get_product_by_name_or_id":
                product_identifier = function_args.get("product_identifier", "")
                if not product_identifier:
                    return "<answer>Vui lòng cung cấp tên hoặc ID sản phẩm cần tìm.</answer>"
                
                # Chuẩn hóa tham số
                if isinstance(product_identifier, (list, tuple)):
                    # Nếu model trả về list, lấy phần tử đầu tiên
                    product_identifier = product_identifier[0] if product_identifier else ""
                
                # Xử lý trường hợp đặc biệt: model truyền tham số trong format sai
                if not product_identifier and len(function_args) > 0:
                    # Thử tìm tham số có giá trị là string
                    for key, value in function_args.items():
                        if isinstance(value, str) and len(value) > 0:
                            product_identifier = value
                            break
                
                if not product_identifier:
                    return "<answer>Vui lòng cung cấp tên hoặc ID sản phẩm cần tìm.</answer>"
                
                result = self.get_product_by_name_or_id(product_identifier)
                return f"<answer>{result}</answer>"
            
            elif function_name == "compare_products":
                product1_identifier = function_args.get("product1_identifier", "")
                product2_identifier = function_args.get("product2_identifier", "")
                
                # Kiểm tra tham số trống
                if not product1_identifier or not product2_identifier:
                    # Thử tìm kiếm tham số trong các format khác
                    if "products" in function_args and isinstance(function_args["products"], list):
                        products = function_args["products"]
                        if len(products) >= 2:
                            product1_identifier = products[0]
                            product2_identifier = products[1]
                    elif "product1" in function_args and "product2" in function_args:
                        product1_identifier = function_args["product1"]
                        product2_identifier = function_args["product2"]
                
                if not product1_identifier or not product2_identifier:
                    return "<answer>Vui lòng cung cấp đủ hai sản phẩm để so sánh.</answer>"
                
                result = self.compare_products(product1_identifier, product2_identifier)
                return f"<answer>{result}</answer>"
            
            elif function_name == "get_all_brands":
                limit = min(max(1, function_args.get("limit", 20)), 50)
                result = self.get_all_brands(limit)
                return f"<answer>{result}</answer>"
            
            elif function_name == "get_all_categories":
                limit = min(max(1, function_args.get("limit", 20)), 50)
                result = self.get_all_categories(limit)
                return f"<answer>{result}</answer>"
            
            elif function_name == "get_products_by_brand":
                brand_identifier = function_args.get("brand_identifier", "")
                limit = min(max(1, function_args.get("limit", 10)), 20)
                
                # Xử lý trường hợp đặc biệt: model truyền tham số trong format sai
                if not brand_identifier:
                    if "brand" in function_args:
                        brand_identifier = function_args["brand"]
                    elif "brand_name" in function_args:
                        brand_identifier = function_args["brand_name"]
                    elif "name" in function_args:
                        brand_identifier = function_args["name"]
                
                if not brand_identifier:
                    return "<answer>Vui lòng cung cấp tên hoặc ID thương hiệu cần tìm.</answer>"
                
                result = self.get_products_by_brand(brand_identifier, limit)
                return f"<answer>{result}</answer>"
            
            elif function_name == "get_products_by_category":
                category_identifier = function_args.get("category_identifier", "")
                limit = min(max(1, function_args.get("limit", 10)), 20)
                
                # Xử lý trường hợp đặc biệt: model truyền tham số trong format sai
                if not category_identifier:
                    if "category" in function_args:
                        category_identifier = function_args["category"]
                    elif "category_name" in function_args:
                        category_identifier = function_args["category_name"]
                    elif "name" in function_args:
                        category_identifier = function_args["name"]
                
                if not category_identifier:
                    return "<answer>Vui lòng cung cấp tên hoặc ID danh mục cần tìm.</answer>"
                
                result = self.get_products_by_category(category_identifier, limit)
                return f"<answer>{result}</answer>"
            
            else:
                logger.warning(f"Không hỗ trợ hàm {function_name}")
                return f"<answer>Không hỗ trợ hàm {function_name}</answer>"
                
        except Exception as e:
            logger.error(f"Lỗi khi xử lý tool call: {str(e)}")
            return "<answer>Đã xảy ra lỗi khi xử lý yêu cầu. Vui lòng thử lại.</answer>"

    def extract_specific_brand(self, query):
        """
        Trích xuất tên thương hiệu cụ thể từ truy vấn của người dùng
        
        Args:
            query (str): Truy vấn của người dùng
            
        Returns:
            str: Tên thương hiệu nếu tìm thấy, None nếu không tìm thấy
        """
        conn = self.get_db_connection()
        if not conn:
            logger.error("Không thể kết nối đến cơ sở dữ liệu để trích xuất thương hiệu")
            return None
            
        try:
            cursor = conn.cursor()
            # Lấy danh sách tất cả các thương hiệu
            cursor.execute("SELECT name FROM frontend_brand")
            brands = [brand[0].lower() for brand in cursor.fetchall()]
            
            # Kiểm tra xem có thương hiệu nào xuất hiện trong truy vấn không
            query_lower = query.lower()
            
            # Sắp xếp thương hiệu theo độ dài giảm dần để ưu tiên tên dài hơn
            brands.sort(key=len, reverse=True)
            
            for brand in brands:
                if brand in query_lower:
                    logger.debug(f"Tìm thấy thương hiệu '{brand}' trong truy vấn")
                    return brand
                    
            # Phân tích cú pháp phức tạp hơn
            brand_patterns = [
                r'sản phẩm (?:của|từ|thuộc|hãng|thương hiệu) (.+?)(?: |$|\.|,|\?)',
                r'(.+?) (?:có|sản xuất) (?:sản phẩm|thiết bị)',
                r'thương hiệu (.+?)(?: |$|\.|,|\?)',
                r'hãng (.+?)(?: |$|\.|,|\?)'
            ]
            
            for pattern in brand_patterns:
                matches = re.search(pattern, query_lower)
                if matches:
                    potential_brand = matches.group(1).strip()
                    # Kiểm tra xem potential_brand có gần giống với thương hiệu nào không
                    for brand in brands:
                        # Kiểm tra xem brand có là một phần của potential_brand không
                        if brand in potential_brand or potential_brand in brand:
                            logger.debug(f"Tìm thấy thương hiệu gần đúng '{brand}' trong truy vấn")
                            return brand
                            
            return None
        except sqlite3.Error as e:
            logger.error(f"Lỗi khi trích xuất thương hiệu: {e}")
            return None
        finally:
            conn.close()
    
    def extract_specific_category(self, query):
        """
        Trích xuất tên loại sản phẩm cụ thể từ truy vấn của người dùng
        
        Args:
            query (str): Truy vấn của người dùng
            
        Returns:
            str: Tên loại sản phẩm nếu tìm thấy, None nếu không tìm thấy
        """
        conn = self.get_db_connection()
        if not conn:
            logger.error("Không thể kết nối đến cơ sở dữ liệu để trích xuất loại sản phẩm")
            return None
            
        try:
            cursor = conn.cursor()
            # Lấy danh sách tất cả các loại sản phẩm
            cursor.execute("SELECT name FROM frontend_category")
            categories = [category[0].lower() for category in cursor.fetchall()]
            
            # Kiểm tra xem có loại sản phẩm nào xuất hiện trong truy vấn không
            query_lower = query.lower()
            
            # Sắp xếp loại sản phẩm theo độ dài giảm dần để ưu tiên tên dài hơn
            categories.sort(key=len, reverse=True)
            
            for category in categories:
                if category in query_lower:
                    logger.debug(f"Tìm thấy loại sản phẩm '{category}' trong truy vấn")
                    return category
                    
            # Phân tích cú pháp phức tạp hơn
            category_patterns = [
                r'loại (?:sản phẩm|thiết bị) (.+?)(?: |$|\.|,|\?)',
                r'danh mục (.+?)(?: |$|\.|,|\?)',
                r'phân loại (.+?)(?: |$|\.|,|\?)',
                r'nhóm (?:sản phẩm|thiết bị) (.+?)(?: |$|\.|,|\?)'
            ]
            
            for pattern in category_patterns:
                matches = re.search(pattern, query_lower)
                if matches:
                    potential_category = matches.group(1).strip()
                    # Kiểm tra xem potential_category có gần giống với loại sản phẩm nào không
                    for category in categories:
                        # Kiểm tra xem category có là một phần của potential_category không
                        if category in potential_category or potential_category in category:
                            logger.debug(f"Tìm thấy loại sản phẩm gần đúng '{category}' trong truy vấn")
                            return category
                            
            return None
        except sqlite3.Error as e:
            logger.error(f"Lỗi khi trích xuất loại sản phẩm: {e}")
            return None
        finally:
            conn.close()

    def process_user_query(self, query):
        """
        Xử lý truy vấn của người dùng và trả về kết quả
        
        Args:
            query (str): Câu hỏi của người dùng
        
        Returns:
            str: Câu trả lời đã được trích xuất từ thẻ <answer></answer>
        """
        # Gọi function_calling để xử lý truy vấn
        response = self.function_calling(query)
        
        # Đảm bảo kết quả nằm trong thẻ <answer>
        if not response.startswith("<answer>"):
            response = f"<answer>{response}</answer>"
        if not response.endswith("</answer>"):
            response = f"{response}</answer>"
        
        # Trích xuất nội dung từ thẻ <answer></answer>
        return self.extract_content(response)

    def get_all_brands(self, limit=20):
        """Lấy danh sách tất cả các thương hiệu (hãng sản xuất)
        
        Args:
            limit (int, optional): Số lượng thương hiệu tối đa muốn hiển thị. Mặc định là 20.
            
        Returns:
            str: Danh sách các thương hiệu
        """
        conn = self.get_db_connection()
        if not conn:
            logger.error("Không thể kết nối đến cơ sở dữ liệu để lấy danh sách thương hiệu")
            return "Không thể kết nối đến cơ sở dữ liệu."
        
        try:
            cursor = conn.cursor()
            # Giới hạn số lượng kết quả hợp lý
            limit = min(max(1, limit), 50)
            
            query = """
            SELECT 
                b.id,
                b.name,
                COUNT(p.id) as product_count
            FROM frontend_brand b
            LEFT JOIN frontend_product p ON b.id = p.brand_id
            GROUP BY b.id, b.name
            ORDER BY product_count DESC, b.name
            LIMIT ?
            """
            cursor.execute(query, (limit,))
            brands = cursor.fetchall()
            
            if not brands:
                logger.warning("Không tìm thấy thương hiệu nào")
                return "Hiện tại không có thông tin về thương hiệu."
                
            # Ghi log số lượng thương hiệu tìm được
            if self.debug:
                logger.debug(f"Đã tìm thấy {len(brands)} thương hiệu")
                
            result = "Danh sách các thương hiệu:\n"
            for i, brand in enumerate(brands, 1):
                result += f"{i}. {brand['name']} (Có {brand['product_count']} sản phẩm)\n"
                
            return result
        except sqlite3.Error as e:
            logger.error(f"Lỗi khi truy vấn thương hiệu: {e}")
            return f"Lỗi khi truy vấn thương hiệu: {e}"
        finally:
            conn.close()
    
    def get_all_categories(self, limit=20):
        """Lấy danh sách tất cả các loại sản phẩm (danh mục)
        
        Args:
            limit (int, optional): Số lượng danh mục tối đa muốn hiển thị. Mặc định là 20.
            
        Returns:
            str: Danh sách các loại sản phẩm
        """
        conn = self.get_db_connection()
        if not conn:
            logger.error("Không thể kết nối đến cơ sở dữ liệu để lấy danh sách loại sản phẩm")
            return "Không thể kết nối đến cơ sở dữ liệu."
        
        try:
            cursor = conn.cursor()
            # Giới hạn số lượng kết quả hợp lý
            limit = min(max(1, limit), 50)
            
            query = """
            SELECT 
                c.id,
                c.name,
                COUNT(p.id) as product_count
            FROM frontend_category c
            LEFT JOIN frontend_product p ON c.id = p.category_id
            GROUP BY c.id, c.name
            ORDER BY product_count DESC, c.name
            LIMIT ?
            """
            cursor.execute(query, (limit,))
            categories = cursor.fetchall()
            
            if not categories:
                logger.warning("Không tìm thấy loại sản phẩm nào")
                return "Hiện tại không có thông tin về loại sản phẩm."
                
            # Ghi log số lượng loại sản phẩm tìm được
            if self.debug:
                logger.debug(f"Đã tìm thấy {len(categories)} loại sản phẩm")
                
            result = "Danh sách các loại sản phẩm:\n"
            for i, category in enumerate(categories, 1):
                result += f"{i}. {category['name']} (Có {category['product_count']} sản phẩm)\n"
                
            return result
        except sqlite3.Error as e:
            logger.error(f"Lỗi khi truy vấn loại sản phẩm: {e}")
            return f"Lỗi khi truy vấn loại sản phẩm: {e}"
        finally:
            conn.close()
    
    def get_products_by_brand(self, brand_identifier, limit=10):
        """Lấy danh sách sản phẩm theo thương hiệu (hãng)
        
        Args:
            brand_identifier (str): Tên hoặc ID của thương hiệu
            limit (int, optional): Số lượng sản phẩm tối đa muốn hiển thị. Mặc định là 10.
            
        Returns:
            str: Danh sách sản phẩm của thương hiệu
        """
        conn = self.get_db_connection()
        if not conn:
            logger.error("Không thể kết nối đến cơ sở dữ liệu để lấy sản phẩm theo thương hiệu")
            return "Không thể kết nối đến cơ sở dữ liệu."
        
        try:
            cursor = conn.cursor()
            # Giới hạn số lượng kết quả hợp lý
            limit = min(max(1, limit), 20)
            
            # Tìm brand_id dựa trên tên hoặc ID
            brand_id = None
            brand_name = None
            
            if isinstance(brand_identifier, (int, str)) and str(brand_identifier).isdigit():
                # Tìm theo ID
                cursor.execute("SELECT id, name FROM frontend_brand WHERE id = ?", (int(brand_identifier),))
                brand = cursor.fetchone()
                if brand:
                    brand_id = brand['id']
                    brand_name = brand['name']
            else:
                # Tìm theo tên (tìm kiếm gần đúng)
                cursor.execute("SELECT id, name FROM frontend_brand WHERE name LIKE ?", (f"%{brand_identifier}%",))
                brand = cursor.fetchone()
                if brand:
                    brand_id = brand['id']
                    brand_name = brand['name']
            
            if not brand_id:
                logger.warning(f"Không tìm thấy thương hiệu: {brand_identifier}")
                return f"Không tìm thấy thương hiệu với thông tin: {brand_identifier}"
            
            # Truy vấn sản phẩm theo brand_id
            query = """
            SELECT 
                p.id,
                p.name,
                p.price,
                p.number_of_sell,
                p.number_of_like,
                c.name as category_name
            FROM frontend_product p
            LEFT JOIN frontend_category c ON p.category_id = c.id
            WHERE p.brand_id = ?
            ORDER BY p.number_of_sell DESC
            LIMIT ?
            """
            cursor.execute(query, (brand_id, limit))
            products = cursor.fetchall()
            
            if not products:
                logger.warning(f"Không tìm thấy sản phẩm nào của thương hiệu: {brand_name}")
                return f"Hiện tại không có sản phẩm nào của thương hiệu {brand_name}."
                
            # Ghi log số lượng sản phẩm tìm được
            if self.debug:
                logger.debug(f"Đã tìm thấy {len(products)} sản phẩm của thương hiệu {brand_name}")
                
            result = f"Các sản phẩm của thương hiệu {brand_name}:\n"
            for i, product in enumerate(products, 1):
                result += f"{i}. {product['name']} - Loại: {product['category_name']} - Giá: {product['price']:,.0f} VNĐ - Đã bán: {product['number_of_sell']} - Lượt thích: {product['number_of_like']}\n"
                
            return result
        except sqlite3.Error as e:
            logger.error(f"Lỗi khi truy vấn sản phẩm theo thương hiệu: {e}")
            return f"Lỗi khi truy vấn sản phẩm theo thương hiệu: {e}"
        finally:
            conn.close()
    
    def get_products_by_category(self, category_identifier, limit=10):
        """Lấy danh sách sản phẩm theo loại sản phẩm (danh mục)
        
        Args:
            category_identifier (str): Tên hoặc ID của loại sản phẩm
            limit (int, optional): Số lượng sản phẩm tối đa muốn hiển thị. Mặc định là 10.
            
        Returns:
            str: Danh sách sản phẩm của loại
        """
        conn = self.get_db_connection()
        if not conn:
            logger.error("Không thể kết nối đến cơ sở dữ liệu để lấy sản phẩm theo loại")
            return "Không thể kết nối đến cơ sở dữ liệu."
        
        try:
            cursor = conn.cursor()
            # Giới hạn số lượng kết quả hợp lý
            limit = min(max(1, limit), 20)
            
            # Tìm category_id dựa trên tên hoặc ID
            category_id = None
            category_name = None
            
            if isinstance(category_identifier, (int, str)) and str(category_identifier).isdigit():
                # Tìm theo ID
                cursor.execute("SELECT id, name FROM frontend_category WHERE id = ?", (int(category_identifier),))
                category = cursor.fetchone()
                if category:
                    category_id = category['id']
                    category_name = category['name']
            else:
                # Tìm theo tên (tìm kiếm gần đúng)
                cursor.execute("SELECT id, name FROM frontend_category WHERE name LIKE ?", (f"%{category_identifier}%",))
                category = cursor.fetchone()
                if category:
                    category_id = category['id']
                    category_name = category['name']
            
            if not category_id:
                logger.warning(f"Không tìm thấy loại sản phẩm: {category_identifier}")
                return f"Không tìm thấy loại sản phẩm với thông tin: {category_identifier}"
            
            # Truy vấn sản phẩm theo category_id
            query = """
            SELECT 
                p.id,
                p.name,
                p.price,
                p.number_of_sell,
                p.number_of_like,
                b.name as brand_name
            FROM frontend_product p
            LEFT JOIN frontend_brand b ON p.brand_id = b.id
            WHERE p.category_id = ?
            ORDER BY p.number_of_sell DESC
            LIMIT ?
            """
            cursor.execute(query, (category_id, limit))
            products = cursor.fetchall()
            
            if not products:
                logger.warning(f"Không tìm thấy sản phẩm nào thuộc loại: {category_name}")
                return f"Hiện tại không có sản phẩm nào thuộc loại {category_name}."
                
            # Ghi log số lượng sản phẩm tìm được
            if self.debug:
                logger.debug(f"Đã tìm thấy {len(products)} sản phẩm thuộc loại {category_name}")
                
            result = f"Các sản phẩm thuộc loại {category_name}:\n"
            for i, product in enumerate(products, 1):
                result += f"{i}. {product['name']} - Thương hiệu: {product['brand_name']} - Giá: {product['price']:,.0f} VNĐ - Đã bán: {product['number_of_sell']} - Lượt thích: {product['number_of_like']}\n"
                
            return result
        except sqlite3.Error as e:
            logger.error(f"Lỗi khi truy vấn sản phẩm theo loại: {e}")
            return f"Lỗi khi truy vấn sản phẩm theo loại: {e}"
        finally:
            conn.close()