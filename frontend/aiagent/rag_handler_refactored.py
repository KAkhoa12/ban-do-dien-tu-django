import os
import logging
import sqlite3
from typing import List, Dict, Optional, Tuple, Any
import json
import re
import requests
import random

logger = logging.getLogger('RAGHandler')

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
    def __init__(self, api_key: str = None, model: str = None, debug: bool = False):
        """Khởi tạo RAG Handler"""
        # API config
        self.api_key = api_key or "75c9027a4aeca8e6415b7818ece22762cd806a3b7620e28f93c630e548d536b8"
        self.model = model or "deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free"
        self.api_url = "https://api.together.xyz/v1/completions"
        
        # Token limits
        self.max_query_length = 500
        self.max_total_tokens = 7168
        self.max_output_tokens = 1024
        self.token_estimator_ratio = 3.5
        
        # Debug mode
        self.debug = debug
        if self.debug:
            logger.setLevel(logging.DEBUG)
        
        # Thiết lập đường dẫn
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.db_path = os.path.join(self.base_dir, 'db.sqlite3')
        
        # Kiểm tra file database
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Không tìm thấy database tại: {self.db_path}")
            
        # Load store info
        self.store_info = self._load_store_info()

    def _load_store_info(self) -> Dict[str, Any]:
        """Tải thông tin cửa hàng từ custom_data.txt"""
        store_info = {
            'name': "Nghĩa Thơm Audio",
            'description': "Chuyên cung cấp thiết bị âm thanh cao cấp",
            'custom_data': "",
            'categories': [],
            'brands': []
        }
        
        try:
            custom_data_path = os.path.join(self.base_dir, 'chatbot_langchain', 'docs', 'custom_data.txt')
            if os.path.exists(custom_data_path):
                with open(custom_data_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    content_lines = [line.strip() for line in content.split('\n') if line.strip()]
                    store_info['custom_data'] = '\n'.join(content_lines)
                    
                    for line in content_lines:
                        if "Địa chỉ:" in line:
                            store_info['address'] = line.replace("Địa chỉ:", "").strip()
                        elif any(x in line.lower() for x in ["số điện thoại:", "sđt:", "điện thoại:"]):
                            store_info['phone'] = line.split(":", 1)[1].strip()
                        elif "Email" in line:
                            store_info['email'] = line.split(":", 1)[1].strip().rstrip('.')
                        elif "Website:" in line:
                            store_info['website'] = line.split(":", 1)[1].strip().rstrip('.')
                        elif "Giờ làm việc:" in line:
                            store_info['hours'] = line.split(":", 1)[1].strip()
        except Exception as e:
            logger.error(f"Lỗi khi đọc custom_data.txt: {e}")
            
        return store_info

    def get_db_connection(self) -> Optional[sqlite3.Connection]:
        """Tạo kết nối đến cơ sở dữ liệu SQLite"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            logger.error(f"Lỗi khi kết nối database: {e}")
            return None

    def process_query(self, query: str) -> str:
        """Xử lý câu hỏi từ người dùng"""
        query = query.lower().strip()
        
        # Xử lý câu chào và giới thiệu
        if self._is_greeting_query(query):
            return self._handle_greeting_query(query)
            
        # Kiểm tra xem có phải câu hỏi đơn giản về thông tin cửa hàng
        if self._is_store_info_query(query):
            return self._handle_store_info_query(query)
            
        # Xử lý các câu hỏi về sản phẩm
        return self._handle_product_query(query)

    def _is_greeting_query(self, query: str) -> bool:
        """Kiểm tra xem có phải câu chào hoặc hỏi về chức năng"""
        greeting_keywords = [
            "xin chào", "chào", "hi", "hello", "hey",
            "bạn có thể làm gì", "bạn giúp được gì", 
            "chức năng", "khả năng", "giới thiệu",
            "hướng dẫn", "trợ giúp", "help"
        ]
        return any(keyword in query for keyword in greeting_keywords)

    def _handle_greeting_query(self, query: str) -> str:
        """Xử lý câu chào và giới thiệu chức năng"""
        if any(x in query for x in ["bạn có thể làm gì", "chức năng", "khả năng", "giới thiệu", "hướng dẫn", "trợ giúp", "help"]):
            capabilities = """
Tôi có thể giúp bạn với các chức năng sau:

1. Thông tin cửa hàng:
   - Địa chỉ, số điện thoại, email, giờ làm việc
   - Thông tin liên hệ và giới thiệu

2. Tìm kiếm sản phẩm:
   - Theo danh mục
   - Theo thương hiệu
   - Theo mức giá
   - Sản phẩm bán chạy/ít
   
3. So sánh sản phẩm:
   - So sánh giá, tính năng giữa hai sản phẩm

4. Đề xuất sản phẩm:
   - Theo ngân sách và danh mục
   - Theo ngân sách và thương hiệu
   - Sản phẩm tốt nhất theo danh mục
   - Sản phẩm tốt nhất theo thương hiệu

Bạn có thể hỏi tôi bất kỳ câu hỏi nào về các chủ đề trên!
"""
            return f"<answer>{capabilities}</answer>"
            
        # Xử lý câu chào thông thường
        greetings = [
            "Xin chào! Tôi có thể giúp gì cho bạn?",
            "Chào bạn! Tôi là trợ lý của Nghĩa Thơm Audio, bạn cần tư vấn gì ạ?",
            "Hi! Rất vui được giúp đỡ bạn. Bạn quan tâm đến sản phẩm nào?"
        ]
        return f"<answer>{random.choice(greetings)}</answer>"

    def _is_store_info_query(self, query: str) -> bool:
        """Kiểm tra xem có phải câu hỏi về thông tin cửa hàng"""
        query = query.lower()
        store_keywords = [
            "địa chỉ", "số điện thoại", "sđt", "email", "website",
            "giờ làm việc", "cửa hàng", "liên hệ", "nghĩa thơm"
        ]
        return any(keyword in query for keyword in store_keywords)

    def _handle_store_info_query(self, query: str) -> str:
        """Xử lý câu hỏi về thông tin cửa hàng sử dụng RAG"""
        query = query.lower()
        
        # Trả lời trực tiếp các câu hỏi cụ thể
        if "địa chỉ" in query:
            return f"<answer>Địa chỉ: {self.store_info.get('address', 'Không có thông tin')}</answer>"
            
        if any(x in query for x in ["số điện thoại", "sđt", "liên hệ"]):
            return f"<answer>Số điện thoại: {self.store_info.get('phone', 'Không có thông tin')}</answer>"
            
        if "email" in query:
            return f"<answer>Email: {self.store_info.get('email', 'Không có thông tin')}</answer>"
            
        if "giờ làm việc" in query:
            return f"<answer>Giờ làm việc: {self.store_info.get('hours', 'Không có thông tin')}</answer>"
            
        if "website" in query:
            return f"<answer>Website: {self.store_info.get('website', 'Không có thông tin')}</answer>"
            
        # Trả về thông tin tổng quát nếu không có câu hỏi cụ thể
        return f"<answer>{self.store_info['custom_data']}</answer>"

    def _handle_product_query(self, query: str) -> str:
        """Xử lý câu hỏi về sản phẩm sử dụng function calling"""
        query = query.lower()
        
        # Pattern cho câu hỏi về giá và sản phẩm
        price_patterns = [
            # Mẫu cho "có số tiền X muốn mua Y"
            r'(?:có|với|khoảng|tầm|trong tầm|khoảng tầm|tầm khoảng)?\s*(?:số tiền|ngân sách|tiền|giá)?\s*(\d+)\s*(triệu|tr|trieu|m|nghìn|nghin|k|đồng|dong|vnd|đ)\s*(?:thì|để|muốn|nên|có thể)?\s*(?:mua|chọn|lựa|tư vấn|gợi ý)?\s*(?:sản phẩm|thiết bị|sp|tb)?\s*(?:gì|nào|như thế nào|ra sao|thế nào)?\s*(?:của|thuộc|trong|về|loại)?\s*(.+?)(?:\s|$|\?|\.)',
            
            # Mẫu cho "muốn mua Y với giá X"
            r'(?:muốn|cần|định|dự định)?\s*(?:mua|chọn|lựa|tìm)\s*(?:sản phẩm|thiết bị|sp|tb)?\s*(?:về|thuộc|của|trong)?\s*(.+?)\s*(?:với|khoảng|tầm|giá|có giá|giá khoảng|giá tầm)?\s*(\d+)\s*(triệu|tr|trieu|m|nghìn|nghin|k|đồng|dong|vnd|đ)',
            
            # Mẫu cho "tư vấn Y giá X"
            r'(?:tư vấn|gợi ý|cho hỏi|cho mình hỏi|cho mình xin|xin tư vấn)?\s*(?:về|thuộc)?\s*(.+?)\s*(?:với|khoảng|tầm|giá|có giá|giá khoảng|giá tầm)?\s*(\d+)\s*(triệu|tr|trieu|m|nghìn|nghin|k|đồng|dong|vnd|đ)'
        ]
        
        # Kiểm tra từng pattern
        for pattern in price_patterns:
            match = re.search(pattern, query)
            if match:
                groups = match.groups()
                if len(groups) == 3:  # Pattern 1
                    amount, unit, category_or_brand = groups
                    price = self._convert_price_to_number(amount, unit)
                elif len(groups) == 3:  # Pattern 2 & 3
                    category_or_brand, amount, unit = groups
                    price = self._convert_price_to_number(amount, unit)
                else:
                    continue
                
                # Kiểm tra xem là danh mục hay thương hiệu
                category = self._extract_category(category_or_brand)
                brand = self._extract_brand(category_or_brand)
                
                if category:
                    return self._recommend_products_by_price_and_category(price, category)
                elif brand:
                    return self._recommend_products_by_price_and_brand(price, brand)
                else:
                    # Nếu không xác định được, thử tìm kiếm cả hai
                    category_results = self._recommend_products_by_price_and_category(price, category_or_brand)
                    brand_results = self._recommend_products_by_price_and_brand(price, category_or_brand)
                    
                    # Kết hợp kết quả
                    if "Không tìm thấy" not in category_results and "Không tìm thấy" not in brand_results:
                        return f"<answer>Tôi tìm thấy một số sản phẩm phù hợp với ngân sách {price:,.0f} VNĐ của bạn:\n\n{category_results}\n\n{brand_results}</answer>"
                    elif "Không tìm thấy" not in category_results:
                        return category_results
                    elif "Không tìm thấy" not in brand_results:
                        return brand_results
                    else:
                        return f"<answer>Xin lỗi, tôi không tìm thấy sản phẩm nào phù hợp với ngân sách {price:,.0f} VNĐ trong danh mục hoặc thương hiệu '{category_or_brand}'.</answer>"
        
        # Xử lý các trường hợp khác...
        if any(x in query for x in ["so sánh", "đối chiếu", "khác nhau"]):
            products = self._extract_product_names(query)
            if len(products) == 2:
                return self._compare_products(products[0], products[1])
            return "<answer>Vui lòng cung cấp đủ hai sản phẩm để so sánh.</answer>"
            
        if any(x in query for x in ["bán chạy", "phổ biến", "hot"]):
            return self._get_top_selling_products()
            
        if any(x in query for x in ["bán ít", "bán chậm"]):
            return self._get_least_selling_products()
            
        if any(x in query for x in ["danh mục", "loại", "category", "loại sản phẩm",'loại sp']):
            category = self._extract_category(query)
            if category:
                return self._get_products_by_category(category)
            return self._get_all_categories()
            
        if any(x in query for x in ["hãng", "thương hiệu", "brand"]):
            brand = self._extract_brand(query)
            if brand:
                return self._get_products_by_brand(brand)
            return self._get_all_brands()
            
        product = self._extract_product_names(query)
        if product:
            return self._get_product_details(product[0])
            
        return "<answer>Xin lỗi, tôi không hiểu câu hỏi của bạn. Vui lòng hỏi rõ hơn về thông tin bạn cần.</answer>"

    def _convert_price_to_number(self, amount: str, unit: str) -> float:
        """Chuyển đổi giá từ text sang số"""
        try:
            amount = float(amount)
            unit = unit.lower()
            
            if unit in ['triệu', 'tr', 'trieu', 'm']:
                return amount * 1000000
            elif unit in ['nghìn', 'nghin', 'k']:
                return amount * 1000
            elif unit in ['đồng', 'dong', 'vnd', 'đ', '']:
                return amount
            else:
                return amount
        except ValueError:
            return 0

    def _recommend_products_by_price_and_category(self, price: float, category: str) -> str:
        """Đề xuất sản phẩm theo giá và danh mục"""
        conn = self.get_db_connection()
        if not conn:
            return "<answer>Không thể kết nối đến cơ sở dữ liệu.</answer>"
            
        try:
            cursor = conn.cursor()
            # Tìm sản phẩm với giá trong khoảng ±20% của giá đề xuất
            price_min = price * 0.8
            price_max = price * 1.2
            
            query = """
            SELECT p.*, c.name as category_name, b.name as brand_name,
                   (p.number_of_sell * 0.5 + p.number_of_like * 0.3) as score
            FROM frontend_product p
            LEFT JOIN frontend_category c ON p.category_id = c.id
            LEFT JOIN frontend_brand b ON p.brand_id = b.id
            WHERE c.name LIKE ? AND p.price BETWEEN ? AND ?
            ORDER BY score DESC, ABS(p.price - ?) ASC
            LIMIT 5
            """
            
            cursor.execute(query, (f"%{category}%", price_min, price_max, price))
            products = cursor.fetchall()
            
            if not products:
                # Thử tìm với khoảng giá rộng hơn (±30%)
                price_min = price * 0.7
                price_max = price * 1.3
                cursor.execute(query, (f"%{category}%", price_min, price_max, price))
                products = cursor.fetchall()
                
                if not products:
                    return f"<answer>Xin lỗi, tôi không tìm thấy sản phẩm nào trong danh mục '{category}' phù hợp với ngân sách {price:,.0f} VNĐ của bạn.</answer>"
            
            # Format kết quả với LLM
            return self._format_products_as_html(
                products,
                f"Đề xuất sản phẩm trong danh mục '{category}' với ngân sách {price:,.0f} VNĐ"
            )
            
        except Exception as e:
            logger.error(f"Lỗi khi đề xuất sản phẩm theo giá và danh mục: {e}")
            return "<answer>Có lỗi xảy ra khi tìm kiếm sản phẩm.</answer>"
        finally:
            conn.close()

    def _recommend_products_by_price_and_brand(self, price: float, brand: str) -> str:
        """Đề xuất sản phẩm theo giá và thương hiệu"""
        conn = self.get_db_connection()
        if not conn:
            return "<answer>Không thể kết nối đến cơ sở dữ liệu.</answer>"
            
        try:
            cursor = conn.cursor()
            # Tìm sản phẩm với giá trong khoảng ±20% của giá đề xuất
            price_min = price * 0.8
            price_max = price * 1.2
            
            query = """
            SELECT p.*, c.name as category_name, b.name as brand_name,
                   (p.number_of_sell * 0.5 + p.number_of_like * 0.3) as score
            FROM frontend_product p
            LEFT JOIN frontend_category c ON p.category_id = c.id
            LEFT JOIN frontend_brand b ON p.brand_id = b.id
            WHERE b.name LIKE ? AND p.price BETWEEN ? AND ?
            ORDER BY score DESC, ABS(p.price - ?) ASC
            LIMIT 5
            """
            
            cursor.execute(query, (f"%{brand}%", price_min, price_max, price))
            products = cursor.fetchall()
            
            if not products:
                # Thử tìm với khoảng giá rộng hơn (±30%)
                price_min = price * 0.7
                price_max = price * 1.3
                cursor.execute(query, (f"%{brand}%", price_min, price_max, price))
                products = cursor.fetchall()
                
                if not products:
                    return f"<answer>Xin lỗi, tôi không tìm thấy sản phẩm nào của thương hiệu '{brand}' phù hợp với ngân sách {price:,.0f} VNĐ của bạn.</answer>"
            
            # Format kết quả với LLM
            return self._format_products_as_html(
                products,
                f"Đề xuất sản phẩm của thương hiệu '{brand}' với ngân sách {price:,.0f} VNĐ"
            )
            
        except Exception as e:
            logger.error(f"Lỗi khi đề xuất sản phẩm theo giá và thương hiệu: {e}")
            return "<answer>Có lỗi xảy ra khi tìm kiếm sản phẩm.</answer>"
        finally:
            conn.close()

    def _extract_product_names(self, query: str) -> List[str]:
        """Trích xuất tên sản phẩm từ câu hỏi"""
        conn = self.get_db_connection()
        if not conn:
            return []
            
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM frontend_product")
            products = cursor.fetchall()
            
            found_products = []
            for product in products:
                if product['name'].lower() in query:
                    found_products.append(product['name'])
                    
            return found_products
        except Exception as e:
            logger.error(f"Lỗi khi trích xuất tên sản phẩm: {e}")
            return []
        finally:
            conn.close()

    def _extract_category(self, query: str) -> Optional[str]:
        """Trích xuất tên danh mục từ câu hỏi"""
        conn = self.get_db_connection()
        if not conn:
            return None
            
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM frontend_category")
            categories = cursor.fetchall()
            
            for category in categories:
                if category['name'].lower() in query:
                    return category['name']
            return None
        except Exception as e:
            logger.error(f"Lỗi khi trích xuất danh mục: {e}")
            return None
        finally:
            conn.close()

    def _extract_brand(self, query: str) -> Optional[str]:
        """Trích xuất tên thương hiệu từ câu hỏi"""
        conn = self.get_db_connection()
        if not conn:
            return None
            
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM frontend_brand")
            brands = cursor.fetchall()
            
            for brand in brands:
                if brand['name'].lower() in query:
                    return brand['name']
            return None
        except Exception as e:
            logger.error(f"Lỗi khi trích xuất thương hiệu: {e}")
            return None
        finally:
            conn.close()

    def _compare_products(self, product1: str, product2: str) -> str:
        """So sánh hai sản phẩm"""
        conn = self.get_db_connection()
        if not conn:
            return "<answer>Không thể kết nối đến cơ sở dữ liệu.</answer>"
            
        try:
            cursor = conn.cursor()
            query = """
            SELECT p.*, c.name as category_name, b.name as brand_name
            FROM frontend_product p
            LEFT JOIN frontend_category c ON p.category_id = c.id
            LEFT JOIN frontend_brand b ON p.brand_id = b.id
            WHERE p.name IN (?, ?)
            """
            cursor.execute(query, (product1, product2))
            products = cursor.fetchall()
            
            if len(products) != 2:
                return "<answer>Không tìm thấy đủ thông tin của hai sản phẩm để so sánh.</answer>"
                
            p1, p2 = products
            
            # Tạo dữ liệu cho LLM
            raw_data = f"So sánh {p1['name']} và {p2['name']}:\n\n"
            raw_data += f"1. {p1['name']}:\n"
            raw_data += f"- Giá: {p1['price']:,.0f} VNĐ\n"
            raw_data += f"- Thương hiệu: {p1['brand_name']}\n"
            raw_data += f"- Danh mục: {p1['category_name']}\n"
            raw_data += f"- Đã bán: {p1['number_of_sell']}\n"
            raw_data += f"- Lượt thích: {p1['number_of_like']}\n\n"
            
            raw_data += f"2. {p2['name']}:\n"
            raw_data += f"- Giá: {p2['price']:,.0f} VNĐ\n"
            raw_data += f"- Thương hiệu: {p2['brand_name']}\n"
            raw_data += f"- Danh mục: {p2['category_name']}\n"
            raw_data += f"- Đã bán: {p2['number_of_sell']}\n"
            raw_data += f"- Lượt thích: {p2['number_of_like']}\n\n"
            
            # Thêm một số thông tin so sánh
            price_diff = abs(p1['price'] - p2['price'])
            price_diff_percent = (price_diff / max(p1['price'], p2['price'])) * 100
            raw_data += f"Chênh lệch giá: {price_diff:,.0f} VNĐ (~{price_diff_percent:.1f}%)\n"
            
            # Format câu trả lời tự nhiên với LLM
            return self._format_llm_response(raw_data, "product_compare")
            
        except Exception as e:
            logger.error(f"Lỗi khi so sánh sản phẩm: {e}")
            return "<answer>Có lỗi xảy ra khi so sánh sản phẩm.</answer>"
        finally:
            conn.close()

    def _format_llm_response(self, raw_data: str, query_type: str = None) -> str:
        """Format dữ liệu thô thành câu trả lời tự nhiên sử dụng LLM"""
        try:
            # Tạo system prompt dựa trên loại truy vấn
            if query_type == "product_list":
                system_prompt = """<<SYS>>
Bạn là trợ lý ảo của Nghĩa Thơm Audio. Nhiệm vụ của bạn là chuyển đổi danh sách sản phẩm thành câu trả lời tự nhiên.

QUY TẮC:
- Viết ngắn gọn, súc tích nhưng đầy đủ thông tin
- Sử dụng ngôn ngữ thân thiện, dễ hiểu
- Thêm các từ ngữ gợi ý, tư vấn phù hợp
- Đảm bảo giữ nguyên các thông tin quan trọng (tên, giá, thương hiệu)
- Chỉ đặt câu trả lời trong thẻ <answer></answer>
<</SYS>>"""

            elif query_type == "product_compare":
                system_prompt = """<<SYS>>
Bạn là trợ lý ảo của Nghĩa Thơm Audio. Nhiệm vụ của bạn là chuyển đổi bảng so sánh sản phẩm thành câu trả lời tự nhiên.

QUY TẮC:
- Phân tích và so sánh các thông số một cách khách quan
- Đưa ra nhận xét, đánh giá dựa trên dữ liệu
- Đề xuất lựa chọn phù hợp (nếu có)
- Sử dụng ngôn ngữ chuyên nghiệp nhưng dễ hiểu
- Chỉ đặt câu trả lời trong thẻ <answer></answer>
<</SYS>>"""

            else:
                system_prompt = """<<SYS>>
Bạn là trợ lý ảo của Nghĩa Thơm Audio. Nhiệm vụ của bạn là chuyển đổi dữ liệu thành câu trả lời tự nhiên.

QUY TẮC:
- Viết ngắn gọn, rõ ràng, dễ hiểu
- Sử dụng ngôn ngữ thân thiện
- Giữ nguyên các thông tin quan trọng
- Chỉ đặt câu trả lời trong thẻ <answer></answer>
<</SYS>>"""

            user_prompt = f"[INST]Hãy chuyển đổi dữ liệu sau thành câu trả lời tự nhiên:\n\n{raw_data}[/INST]"
            
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
                "temperature": 0.5,
                "top_p": 0.95,
                "repetition_penalty": 1.2,
                "tool_choice": "none"
            }
            
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=20)
            response_json = response.json()
            
            if "choices" in response_json and len(response_json["choices"]) > 0:
                answer = response_json["choices"][0].get("text", "").strip()
                if answer:
                    # Đảm bảo phản hồi nằm trong thẻ answer
                    if not answer.startswith("<answer>"):
                        answer = f"<answer>{answer}</answer>"
                    if not answer.endswith("</answer>"):
                        answer = f"{answer}</answer>"
                    return answer
            
            # Nếu có lỗi, trả về dữ liệu gốc trong thẻ answer
            return f"<answer>{raw_data}</answer>"
            
        except Exception as e:
            logger.error(f"Lỗi khi format câu trả lời với LLM: {e}")
            return f"<answer>{raw_data}</answer>"

    def _format_products_as_html(self, products: List[Dict], title: str) -> str:
        """Format danh sách sản phẩm thành HTML cho chatbot"""
        if not products:
            return f"<answer>Không tìm thấy sản phẩm nào.</answer>"
            
        # Giới hạn số lượng sản phẩm
        products = products[:10]
        
        # Tạo dữ liệu cho LLM
        raw_data = f"{title}:\n\n"
        for p in products:
            # Convert sqlite3.Row to dict if needed
            product = dict(p) if hasattr(p, 'keys') else p
            raw_data += f"- {product['name']}\n"
            raw_data += f"  Thương hiệu: {product.get('brand_name', 'N/A')}\n"
            raw_data += f"  Danh mục: {product.get('category_name', 'N/A')}\n"
            raw_data += f"  Giá: {float(product['price']):,.0f} VNĐ\n"
            raw_data += f"  Đã bán: {product.get('number_of_sell', 0)}\n"
            raw_data += f"  Lượt thích: {product.get('number_of_like', 0)}\n\n"
            
        # Format câu trả lời tự nhiên với LLM
        llm_response = self._format_llm_response(raw_data, "product_list")
        
        # Tạo HTML cho sản phẩm
        html = f"""
<answer>
<div class="chat-response">
    {llm_response}
</div>
<div class="product-list">
    <div class="products-grid">
"""
        
        for p in products:
            product = dict(p) if hasattr(p, 'keys') else p
            image_url = f"/static/{product['image_url']}" if product.get('image_url') else "/static/img/default-product.png"
            price = "{:,.0f}".format(float(product['price']))
            
            html += f"""
        <div class="product-item">
            <img src="{image_url}" alt="{product['name']}" style="width: 100%; height: 100%; object-fit: cover; aspect-ratio: 1/1;">
            <div class="product-info">
                <h4>{product['name']}</h4>
                <p class="price">{price} VNĐ</p>
                <p class="brand">Thương hiệu: {product.get('brand_name', 'N/A')}</p>
                <p class="category">Danh mục: {product.get('category_name', 'N/A')}</p>
                <a href="/product/{product['id']}" class="view-detail">Xem chi tiết</a>
            </div>
        </div>
"""
        
        html += """
    </div>
</div>
</answer>
"""
        return html

    def _get_top_selling_products(self, limit: int = 5) -> str:
        """Lấy danh sách sản phẩm bán chạy nhất"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return "<answer>Không thể kết nối đến cơ sở dữ liệu.</answer>"

            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    p.id,
                    p.name,
                    p.price,
                    p.image_url,
                    p.description,
                    b.name as brand_name,
                    c.name as category_name,
                    COUNT(od.id) as number_of_sell
                FROM frontend_product p
                LEFT JOIN frontend_brand b ON p.brand_id = b.id
                LEFT JOIN frontend_category c ON p.category_id = c.id
                LEFT JOIN frontend_orderdetail od ON p.id = od.product_id
                GROUP BY p.id
                ORDER BY number_of_sell DESC
                LIMIT ?
            """, (limit,))
            
            products = cursor.fetchall()
            return self._format_products_as_html(products, "Sản phẩm bán chạy nhất")
            
        except Exception as e:
            logger.error(f"Lỗi khi lấy sản phẩm bán chạy: {e}")
            return "<answer>Có lỗi xảy ra khi lấy danh sách sản phẩm bán chạy.</answer>"
        finally:
            if conn:
                conn.close()

    def _get_least_selling_products(self, limit: int = 5) -> str:
        """Lấy danh sách sản phẩm bán ít"""
        conn = self.get_db_connection()
        if not conn:
            return "<answer>Không thể kết nối đến cơ sở dữ liệu.</answer>"
            
        try:
            cursor = conn.cursor()
            query = """
            SELECT p.*, c.name as category_name, b.name as brand_name
            FROM frontend_product p
            LEFT JOIN frontend_category c ON p.category_id = c.id
            LEFT JOIN frontend_brand b ON p.brand_id = b.id
            ORDER BY p.number_of_sell ASC
            LIMIT ?
            """
            cursor.execute(query, (limit,))
            products = cursor.fetchall()
            
            return self._format_products_as_html(products, "Sản phẩm bán ít nhất")
        except Exception as e:
            logger.error(f"Lỗi khi lấy sản phẩm bán ít: {e}")
            return "<answer>Có lỗi xảy ra khi lấy danh sách sản phẩm bán ít.</answer>"
        finally:
            conn.close()

    def _get_all_categories(self) -> str:
        """Lấy danh sách tất cả các danh mục"""
        conn = self.get_db_connection()
        if not conn:
            return "<answer>Không thể kết nối đến cơ sở dữ liệu.</answer>"
            
        try:
            cursor = conn.cursor()
            query = """
            SELECT c.*, COUNT(p.id) as product_count
            FROM frontend_category c
            LEFT JOIN frontend_product p ON c.id = p.category_id
            GROUP BY c.id
            ORDER BY product_count DESC
            """
            cursor.execute(query)
            categories = cursor.fetchall()
            
            if not categories:
                return "<answer>Không có thông tin về danh mục sản phẩm.</answer>"
                
            result = "Danh sách các danh mục sản phẩm:\n\n"
            for i, c in enumerate(categories, 1):
                result += f"{i}. {c['name']} ({c['product_count']} sản phẩm)\n"
                
            return f"<answer>{result}</answer>"
        except Exception as e:
            logger.error(f"Lỗi khi lấy danh mục: {e}")
            return "<answer>Có lỗi xảy ra khi lấy danh sách danh mục.</answer>"
        finally:
            conn.close()

    def _get_all_brands(self) -> str:
        """Lấy danh sách tất cả các thương hiệu"""
        conn = self.get_db_connection()
        if not conn:
            return "<answer>Không thể kết nối đến cơ sở dữ liệu.</answer>"
            
        try:
            cursor = conn.cursor()
            query = """
            SELECT b.*, COUNT(p.id) as product_count
            FROM frontend_brand b
            LEFT JOIN frontend_product p ON b.id = p.brand_id
            GROUP BY b.id
            ORDER BY product_count DESC
            """
            cursor.execute(query)
            brands = cursor.fetchall()
            
            if not brands:
                return "<answer>Không có thông tin về thương hiệu.</answer>"
                
            result = "Danh sách các thương hiệu:\n\n"
            for i, b in enumerate(brands, 1):
                result += f"{i}. {b['name']} ({b['product_count']} sản phẩm)\n"
                
            return f"<answer>{result}</answer>"
        except Exception as e:
            logger.error(f"Lỗi khi lấy thương hiệu: {e}")
            return "<answer>Có lỗi xảy ra khi lấy danh sách thương hiệu.</answer>"
        finally:
            conn.close()

    def _get_products_by_category(self, category: str) -> str:
        """Lấy danh sách sản phẩm theo danh mục"""
        conn = self.get_db_connection()
        if not conn:
            return "<answer>Không thể kết nối đến cơ sở dữ liệu.</answer>"
            
        try:
            cursor = conn.cursor()
            query = """
            SELECT p.*, b.name as brand_name, c.name as category_name
            FROM frontend_product p
            LEFT JOIN frontend_brand b ON p.brand_id = b.id
            LEFT JOIN frontend_category c ON p.category_id = c.id
            WHERE c.name = ?
            ORDER BY p.number_of_sell DESC
            LIMIT 10
            """
            cursor.execute(query, (category,))
            products = cursor.fetchall()
            
            return self._format_products_as_html(products, f"Sản phẩm trong danh mục {category}")
        except Exception as e:
            logger.error(f"Lỗi khi lấy sản phẩm theo danh mục: {e}")
            return "<answer>Có lỗi xảy ra khi lấy danh sách sản phẩm.</answer>"
        finally:
            conn.close()

    def _get_products_by_brand(self, brand: str) -> str:
        """Lấy danh sách sản phẩm theo thương hiệu"""
        conn = self.get_db_connection()
        if not conn:
            return "<answer>Không thể kết nối đến cơ sở dữ liệu.</answer>"
            
        try:
            cursor = conn.cursor()
            query = """
            SELECT p.*, c.name as category_name, b.name as brand_name
            FROM frontend_product p
            LEFT JOIN frontend_category c ON p.category_id = c.id
            LEFT JOIN frontend_brand b ON p.brand_id = b.id
            WHERE b.name = ?
            ORDER BY p.number_of_sell DESC
            LIMIT 10
            """
            cursor.execute(query, (brand,))
            products = cursor.fetchall()
            
            return self._format_products_as_html(products, f"Sản phẩm của thương hiệu {brand}")
        except Exception as e:
            logger.error(f"Lỗi khi lấy sản phẩm theo thương hiệu: {e}")
            return "<answer>Có lỗi xảy ra khi lấy danh sách sản phẩm.</answer>"
        finally:
            conn.close()

    def _get_product_details(self, product: str) -> str:
        """Lấy thông tin chi tiết của một sản phẩm"""
        conn = self.get_db_connection()
        if not conn:
            return "<answer>Không thể kết nối đến cơ sở dữ liệu.</answer>"
            
        try:
            cursor = conn.cursor()
            query = """
            SELECT p.*, c.name as category_name, b.name as brand_name
            FROM frontend_product p
            LEFT JOIN frontend_category c ON p.category_id = c.id
            LEFT JOIN frontend_brand b ON p.brand_id = b.id
            WHERE p.name = ?
            """
            cursor.execute(query, (product,))
            p = cursor.fetchone()
            
            if not p:
                return f"<answer>Không tìm thấy thông tin về sản phẩm {product}.</answer>"
                
            # Lấy ảnh sản phẩm
            image_url = f"/static/products/{p['image']}" if p.get('image') else "/static/img/default-product.png"
            
            html = f"""
<answer>
<div class="product-detail">
    <h3>Thông tin chi tiết sản phẩm</h3>
    <div class="product-content">
        <div class="product-image">
            <img src="{image_url}" alt="{p['name']}">
        </div>
        <div class="product-info">
            <h4>{p['name']}</h4>
            <p class="brand">Thương hiệu: {p['brand_name']}</p>
            <p class="category">Danh mục: {p['category_name']}</p>
            <p class="price">Giá: {p['price']:,.0f} VNĐ</p>
            <p class="stats">Đã bán: {p['number_of_sell']} | Lượt thích: {p['number_of_like']}</p>
            {f'<p class="description">{p["description"]}</p>' if p.get('description') else ''}
            <a href="/product/{p['id']}" class="view-detail">Xem chi tiết</a>
        </div>
    </div>
</div>
</answer>
"""
            return html
        except Exception as e:
            logger.error(f"Lỗi khi lấy thông tin sản phẩm: {e}")
            return "<answer>Có lỗi xảy ra khi lấy thông tin sản phẩm.</answer>"
        finally:
            conn.close() 