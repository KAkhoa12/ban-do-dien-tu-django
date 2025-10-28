from django.views.decorators.csrf import csrf_exempt
from frontend.decorator import admin_required
from frontend.utils.db_helper import * 
from django.shortcuts import render, redirect
from django.contrib import messages
import json
from django.http import JsonResponse
@csrf_exempt
def chatbot_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '')
            
            # Khởi tạo RAG handler
            from frontend.aiagent.rag_handler_refactored import RAGHandler
            rag_handler = RAGHandler()
            
            # Xử lý câu hỏi
            response = rag_handler.process_query(user_message)
            
            # Phân tích response để lấy answer và sources
            import re
            answer_match = re.search(r'<answer>(.*?)</answer>', response, re.DOTALL)
            answer = answer_match.group(1) if answer_match else response
            
            # Kiểm tra xem có sources không
            sources = []
            if 'product-list' in answer:
                # Trích xuất thông tin sản phẩm từ câu trả lời
                products = Product.objects.all()[:10]  # Giới hạn 10 sản phẩm
                sources = [{
                    'metadata': {
                        'product_id': product.id,
                        'name': product.name,
                        'price': str(product.price),
                        'image_url': product.image_url,
                        'description': product.description,
                        'brand': product.brand.name if product.brand else None,
                        'category': product.category.name if product.category else None
                    }
                } for product in products]
            
            return JsonResponse({
                'status': 'success',
                'response': {
                    'answer': answer.strip(),
                    'sources': sources
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error', 
                'message': str(e)
            })
            
    return JsonResponse({
        'status': 'error',
        'message': 'Chỉ hỗ trợ phương thức POST'
    })

def handle_general_questions(question):
    """Xử lý các câu hỏi chào hỏi và câu hỏi thông thường"""
    question_lower = question.lower().strip()
    
    # Xử lý các câu chào
    greetings = ["hi", "hello", "chào", "xin chào", "hey", "hi there", "chào bạn"]
    if any(greeting == question_lower for greeting in greetings):
        return "Xin chào! Tôi là trợ lý ảo về thiết bị âm thanh, tôi có thể giúp bạn tìm kiếm thông tin về sản phẩm, giá cả, thương hiệu. Bạn cần hỏi gì về thiết bị âm thanh?"
    
    # Xử lý câu hỏi về tên
    name_questions = ["tên bạn là gì", "bạn tên gì", "tên của bạn là gì", "bạn là ai", "what is your name", "who are you"]
    if any(name_question in question_lower for name_question in name_questions):
        return "Tôi là trợ lý AI chuyên về thiết bị âm thanh của DoAn_QuanLyDoDienTu. Tôi có thể giúp bạn tìm kiếm thông tin về các sản phẩm âm thanh, giá cả, và thương hiệu. Bạn cần hỏi gì về thiết bị âm thanh?"
    
    # Xử lý cảm ơn
    thanks = ["cảm ơn", "thank", "thanks", "cám ơn"]
    if any(thank_word in question_lower for thank_word in thanks):
        return "Không có gì! Rất vui khi được giúp đỡ bạn. Bạn có câu hỏi nào khác về thiết bị âm thanh không?"
    
    # Xử lý tạm biệt
    goodbyes = ["tạm biệt", "bye", "goodbye", "gặp lại sau"]
    if any(goodbye in question_lower for goodbye in goodbyes):
        return "Tạm biệt! Rất vui được giúp đỡ bạn. Hẹn gặp lại bạn lần sau!"
    
    # Xử lý câu hỏi về khả năng của chatbot
    capabilities = ["bạn có thể làm gì", "bạn giúp được gì", "chức năng của bạn", "bạn biết gì"]
    if any(capability in question_lower for capability in capabilities):
        return "Tôi có thể giúp bạn tìm kiếm thông tin về các sản phẩm âm thanh như loa, amply, tai nghe... Tôi cũng có thể cung cấp thông tin về giá cả, thương hiệu, tính năng và so sánh các sản phẩm. Bạn có thể hỏi tôi về bất kỳ sản phẩm âm thanh nào!"
    
    # Nếu không thuộc các trường hợp trên, trả về None để xử lý như câu hỏi về sản phẩm
    return None

def handle_combined_query(question):
    """Xử lý truy vấn kết hợp giữa hãng và các tiêu chí khác"""
    question_lower = question.lower()
    
    # Kiểm tra xem có đề cập đến hãng nào không
    brands = ["JBL", "Sony", "Denon", "Yamaha", "Bose", "Sennheiser", "Audio-Technica", 
              "KEF", "Klipsch", "Polk Audio", "Cambridge Audio", "Boston Acoustics", 
              "Harman Kardon", "Marshall", "Bang & Olufsen", "Focal", "Dynaudio"]
    
    found_brand = None
    for brand in brands:
        if brand.lower() in question_lower:
            found_brand = brand
            break
    
    # Nếu không tìm thấy thương hiệu, trả về None
    if not found_brand:
        return None
    
    # Kiểm tra các tiêu chí khác
    is_top_selling = any(term in question_lower for term in ["bán chạy", "mua nhiều", "bán nhiều"])
    is_most_liked = any(term in question_lower for term in ["yêu thích", "ưa chuộng", "nhiều like", "được yêu thích"])
    is_highest_price = any(term in question_lower for term in ["đắt nhất", "cao nhất", "giá cao"])
    is_lowest_price = any(term in question_lower for term in ["rẻ nhất", "thấp nhất", "giá thấp"])
    
    # Tạo truy vấn kết hợp
    if is_top_selling:
        return f"Tên hãng: {found_brand} sản phẩm có số lượng mua nhiều nhất"
    elif is_most_liked:
        return f"Tên hãng: {found_brand} sản phẩm có số lượng like nhiều nhất"
    elif is_highest_price:
        return f"Tên hãng: {found_brand} sản phẩm có giá cao nhất"
    elif is_lowest_price:
        return f"Tên hãng: {found_brand} sản phẩm có giá thấp nhất"
    
    # Nếu chỉ có thương hiệu mà không có tiêu chí cụ thể
    return f"Tên hãng: {found_brand}"

@csrf_exempt
def get_products_by_ids(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_ids = data.get('product_ids', [])
            
            # Lấy danh sách sản phẩm từ các ID
            products = Product.objects.filter(id__in=product_ids)
            
            # Chuyển đổi queryset thành list các dictionary
            products_data = []
            for product in products:
                products_data.append({
                    'id': product.id,
                    'name': product.name,
                    'price': str(product.price),
                    'image_url': product.image_url,
                    'description': product.description,
                    'brand': product.brand.name if product.brand else None,
                    'category': product.category.name if product.category else None,
                    'url': f'/product/{product.id}'
                })
            
            return JsonResponse({
                'status': 'success',
                'products': products_data
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })
            
    return JsonResponse({
        'status': 'error',
        'message': 'Chỉ hỗ trợ phương thức POST'
    })

@csrf_exempt
def get_chat_history(request):
    if request.method == 'GET':
        if 'user_id' in request.session:
            # Lấy lịch sử chat từ session
            chat_history = request.session.get('chat_history', [])
            return JsonResponse({
                'status': 'success',
                'chat_history': chat_history
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Người dùng chưa đăng nhập',
                'chat_history': []
            })
    return JsonResponse({
        'status': 'error',
        'message': 'Phương thức không được hỗ trợ'
    })

@csrf_exempt
def save_chat_history(request):
    if request.method == 'POST':
        if 'user_id' in request.session:
            try:
                data = json.loads(request.body)
                chat_history = data.get('chat_history', [])
                
                # Lưu lịch sử chat vào session
                request.session['chat_history'] = chat_history
                request.session.modified = True
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Lịch sử chat đã được lưu'
                })
            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Người dùng chưa đăng nhập'
            })
    return JsonResponse({
        'status': 'error',
        'message': 'Phương thức không được hỗ trợ'
    })

# AI Agent views
@admin_required
def admin_aiagent(request):
    """Trang quản lý AI Agent trong admin dashboard"""
    from frontend.aiagent.data_processor import DataProcessor
    
    processor = DataProcessor()
    product_count = processor.get_product_count()
    last_update = processor.get_last_update_time()
    custom_data = processor.get_custom_data()
    
    return render(request, 'backend/pages/aiagent/index.html', {
        'title': 'AI Agent Management',
        'product_count': product_count,
        'last_update': last_update,
        'custom_data': custom_data
    })

@admin_required
def admin_aiagent_update_data(request):
    """Cập nhật dữ liệu sản phẩm cho AI Agent"""
    if request.method == 'POST':
        from frontend.aiagent.data_processor import DataProcessor
        
        processor = DataProcessor()
        message, product_count = processor.generate_product_data()
        
        if product_count > 0:
            messages.success(request, message)
        else:
            messages.error(request, message)
    
    return redirect('admin_aiagent')

@admin_required
def admin_aiagent_update_custom_data(request):
    """Cập nhật dữ liệu tùy chỉnh cho AI Agent"""
    if request.method == 'POST':
        from frontend.aiagent.data_processor import DataProcessor
        
        custom_data = request.POST.get('custom_data', '')
        processor = DataProcessor()
        message = processor.save_custom_data(custom_data)
        
        messages.success(request, message)
    
    return redirect('admin_aiagent')

@csrf_exempt
def function_calling(request):
    """API để thực hiện function calling với AI Agent"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            query = data.get('query', '')
            
            if not query:
                return JsonResponse({'error': 'Thiếu thông tin query'}, status=400)
            
            from frontend.aiagent.rag_handler_refactored import RAGHandler
            
            handler = RAGHandler()
            response = handler.process_query(query)
            
            return JsonResponse({'response': response})
        
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

