from langchain_community.llms import CTransformers
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
import re
import os

# Cấu hình
model_file = "chatbot_langchain/models/vinallama-7b-chat_q5_0.gguf"
vector_db_path = "chatbot_langchain/vectorstores/db_faiss"

# Load LLM
def load_llm():
    """
    Tải mô hình ngôn ngữ lớn
    """
    if not os.path.exists(model_file):
        print(f"CẢNH BÁO: File model {model_file} không tồn tại!")
        raise FileNotFoundError(f"Model file not found: {model_file}")
        
    print(f"Đang tải model {os.path.basename(model_file)}...")
    llm = CTransformers(
        model=model_file,
        model_type="llama",
        max_new_tokens=512,
        temperature=0.1
    )
    print("Đã tải model thành công!")
    return llm

# Đọc vector database
def read_vectors_db():
    """
    Tải vector database đã tạo trước đó
    """
    if not os.path.exists(vector_db_path):
        print(f"CẢNH BÁO: Vector database {vector_db_path} không tồn tại!")
        raise FileNotFoundError(f"Vector database not found: {vector_db_path}")
        
    print("Đang tải vector database...")
    embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    db = FAISS.load_local(vector_db_path, embedding_model, allow_dangerous_deserialization=True)
    print("Đã tải vector database thành công!")
    return db

# Làm sạch và định dạng câu trả lời
def clean_response(response):
    """Làm sạch câu trả lời để loại bỏ token và định dạng không mong muốn"""
    # Loại bỏ các tokens mô hình
    response = re.sub(r'<\|im_[^>]*\|>', '', response)
    # Loại bỏ khoảng trắng thừa
    response = re.sub(r'\s+', ' ', response).strip()
    return response

# Hàm truy vấn đơn giản
def simple_qa(question, db, llm):
    """Truy vấn đơn giản sử dụng RetrievalQA"""
    # Tạo prompt template
    prompt = PromptTemplate.from_template("""<|im_start|>system
Bạn là trợ lý AI chuyên về thiết bị âm thanh. Dựa trên thông tin được cung cấp, 
hãy trả lời câu hỏi một cách chính xác và ngắn gọn.

THÔNG TIN THAM KHẢO:
{context}

NHIỆM VỤ:
- Trả lời câu hỏi dựa trên thông tin được cung cấp
- Nếu câu trả lời không có trong thông tin, hãy nói "Không có thông tin về điều này"
- Không thêm thông tin hoặc ý kiến cá nhân
<|im_end|>

<|im_start|>user
{question}
<|im_end|>

<|im_start|>assistant
""")

    # Tạo chain
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm, 
        chain_type="stuff", 
        retriever=db.as_retriever(search_kwargs={"k": 3}),
        chain_type_kwargs={"prompt": prompt}
    )
    
    # Thực hiện truy vấn
    try:
        response = qa_chain.invoke({"query": question})
        return clean_response(response.get("result", ""))
    except Exception as e:
        print(f"Lỗi khi truy vấn: {e}")
        return "Không thể xử lý câu hỏi này. Vui lòng thử lại."

# Hàm truy vấn thông tin sản phẩm
def query_product_info(question):
    """Truy vấn thông tin sản phẩm"""
    db = read_vectors_db()
    llm = load_llm()
    
    # Thực hiện truy vấn đơn giản
    result = simple_qa(question, db, llm)
    return result

# Hàm tạo truy vấn cụ thể
def create_specific_query(question):
    """Chuyển đổi câu hỏi thành truy vấn cụ thể"""
    # Trích xuất từ khóa từ câu hỏi
    product_match = re.search(r'(?i)(amply|loa|tai nghe|microphone|mixer|đầu đĩa|dàn âm thanh)\s+([A-Za-z0-9\s\-]+)', question)
    brand_match = re.search(r'(?i)(JBL|Sony|Denon|Yamaha|Bose|Sennheiser|Audio-Technica|KEF|Klipsch|Polk Audio|Cambridge Audio)(?:\s|$)', question)
    price_match = re.search(r'(?i)(?:từ|giá)\s+(\d+)(?:\s+triệu|\s+nghìn|\s+tr|\s+k)?\s+(?:đến|tới|và)\s+(\d+)(?:\s+triệu|\s+nghìn|\s+tr|\s+k)?', question)
    
    # Tạo truy vấn theo mẫu tìm thấy
    if product_match:
        product_type = product_match.group(1)
        product_name = product_match.group(2).strip()
        return f"Tên sản phẩm: {product_type} {product_name}"
    elif brand_match:
        brand = brand_match.group(1)
        return f"Tên hãng: {brand}"
    elif price_match:
        min_price = price_match.group(1)
        max_price = price_match.group(2)
        return f"sản phẩm có giá từ {min_price} đến {max_price}"
    elif "cao nhất" in question.lower() or "đắt nhất" in question.lower():
        return "sản phẩm có giá cao nhất"
    elif "thấp nhất" in question.lower() or "rẻ nhất" in question.lower():
        return "sản phẩm có giá thấp nhất"
    elif "bán chạy" in question.lower() or "mua nhiều" in question.lower():
        return "sản phẩm có số lượng mua nhiều nhất"
    elif "yêu thích" in question.lower() or "lượt thích" in question.lower():
        return "sản phẩm có số lượng like nhiều nhất"
    else:
        return question

# Hàm truy vấn thông tin sản phẩm nâng cao
def query_product_info_advanced(question):
    """Truy vấn thông tin sản phẩm với xử lý truy vấn nâng cao"""
    db = read_vectors_db()
    llm = load_llm()
    
    # Tạo truy vấn cụ thể
    specific_query = create_specific_query(question)
    print(f"\nTruy vấn cụ thể: {specific_query}")
    
    # Thực hiện tìm kiếm
    docs = db.similarity_search(specific_query, k=3)
    
    # Tạo context từ documents
    context = "\n\n".join([doc.page_content for doc in docs])
    
    # Tạo prompt template cho tóm tắt
    summary_prompt = PromptTemplate.from_template("""<|im_start|>system
Dưới đây là thông tin về sản phẩm âm thanh:
{context}

Dựa trên thông tin trên, hãy trả lời câu hỏi sau một cách ngắn gọn và đầy đủ:
{question}

Nếu không tìm thấy thông tin liên quan trong dữ liệu, hãy trả lời "Không có thông tin về điều này".
<|im_end|>

<|im_start|>assistant
""")
    
    # Gọi LLM để tóm tắt kết quả
    try:
        result = llm.invoke(summary_prompt.format(context=context, question=question))
        return clean_response(result)
    except Exception as e:
        print(f"Lỗi khi tóm tắt: {e}")
        return "Không thể xử lý câu hỏi này. Vui lòng thử lại."

# Thử nghiệm với một số câu hỏi
def test_product_questions():
    """Thử nghiệm các câu hỏi về sản phẩm"""
    questions = [
        "Tìm thông tin về Amply Denon PMA-900HNE",
        "Sản phẩm nào của JBL bán chạy nhất?",
        "Những sản phẩm nào có giá từ 10 triệu đến 15 triệu?",
        "So sánh loa Klipsch The Sixes với loa KEF LS50 Wireless II",
        "Top 3 sản phẩm có giá cao nhất là gì?"
    ]
    
    for question in questions:
        print(f"\n>>> Câu hỏi: {question}")
        answer = query_product_info_advanced(question)
        print(f"<<< Trả lời: {answer}")
        print("="*50)

if __name__ == "__main__":
    print("Bắt đầu truy vấn thông tin sản phẩm...")
    
    try:
        test_product_questions()
        print("\nHoàn thành!")
    except Exception as e:
        print(f"\nLỖI: {str(e)}")
        print("\nHướng dẫn khắc phục:")
        print("1. Đảm bảo các file model đã được tải về đúng vị trí")
        print("2. Chạy file prepair_vector_db.py trước khi chạy main.py")
        print("3. Kiểm tra các thư viện đã được cài đặt đầy đủ")
        print("   pip install langchain langchain_community ctransformers faiss-cpu sentence-transformers")