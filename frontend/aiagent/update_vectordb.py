import os
import subprocess
import sys

def update_vectordb():
    """
    Cập nhật vector database sử dụng các tệp script có sẵn trong thư mục chatbot_langchain
    """
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Đường dẫn đến file preprogess_data.py
        preprogess_data_path = os.path.join(base_dir, 'chatbot_langchain', 'preprogess_data.py')
        
        # Đường dẫn đến file prepair_vector_db.py
        prepair_vector_db_path = os.path.join(base_dir, 'chatbot_langchain', 'prepair_vector_db.py')
        
        # Kiểm tra xem các file tồn tại không
        if not os.path.exists(preprogess_data_path):
            return f"Không tìm thấy file {preprogess_data_path}"
            
        if not os.path.exists(prepair_vector_db_path):
            return f"Không tìm thấy file {prepair_vector_db_path}"
        
        # Thực thi file preprogess_data.py để tạo dữ liệu
        print("Đang cập nhật dữ liệu...")
        result_preprocess = subprocess.run([sys.executable, preprogess_data_path], 
                                capture_output=True, text=True)
        
        if result_preprocess.returncode != 0:
            return f"Lỗi khi cập nhật dữ liệu: {result_preprocess.stderr}"
            
        # Thực thi file prepair_vector_db.py để tạo vector database
        print("Đang cập nhật vector database...")
        result_vectordb = subprocess.run([sys.executable, prepair_vector_db_path],
                                capture_output=True, text=True)
        
        if result_vectordb.returncode != 0:
            return f"Lỗi khi cập nhật vector database: {result_vectordb.stderr}"
            
        return "Cập nhật vector database thành công!"
    
    except Exception as e:
        return f"Lỗi khi cập nhật vector database: {str(e)}"

if __name__ == "__main__":
    print(update_vectordb()) 