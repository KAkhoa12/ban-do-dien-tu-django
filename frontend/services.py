import json
import hashlib
import hmac
import requests
import datetime
from .momo_config import CONFIG
from .models import MomoPayment

import hmac
import hashlib
import requests
import json

def create_momo_payment(amount, order_info):
    # Tạo thông tin thanh toán mới
    order_id = MomoPayment.generate_order_id()
    request_id = MomoPayment.generate_request_id()
    
    # Lưu thông tin thanh toán vào database
    payment = MomoPayment.objects.create(
        order_id=order_id,
        amount=amount,
        order_info=order_info,
        request_id=request_id
    )
    
    # Chuẩn bị dữ liệu gửi đến MoMo
    raw_data = {
        'partnerCode': CONFIG['partner_code'],
        'accessKey': CONFIG['access_key'],
        'requestId': request_id,
        'amount': str(amount),
        'orderId': order_id,
        'orderInfo': order_info,
        'returnUrl': CONFIG['return_url'],
        'ipnUrl': CONFIG['notify_url'],
        'redirectUrl':  CONFIG['return_url'],  # Trường redirectUrl với giá trị trống
        'requestType': 'payWithMethod',
        'extraData': '',
    }
    
    # Tạo chuỗi raw data để ký
    raw_signature = (
        f"accessKey={raw_data['accessKey']}"
        f"&amount={raw_data['amount']}"
        f"&extraData={raw_data['extraData']}"
        f"&ipnUrl={raw_data['ipnUrl']}"
        f"&orderId={raw_data['orderId']}"
        f"&orderInfo={raw_data['orderInfo']}"
        f"&partnerCode={raw_data['partnerCode']}"
        f"&redirectUrl={raw_data['redirectUrl']}"
        f"&requestId={raw_data['requestId']}"
        f"&requestType={raw_data['requestType']}"
    )
    
    # Tạo chữ ký HMAC SHA256
    signature = hmac.new(
        CONFIG['secret_key'].encode('utf-8'),
        raw_signature.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    raw_data['signature'] = signature
    
    # In ra log để kiểm tra
    print("Data gửi đến MoMo:", json.dumps(raw_data, indent=2))
    print("Raw signature:", raw_signature)
    print("Generated signature:", signature)
    
    # Gửi yêu cầu đến MoMo
    response = requests.post(CONFIG['test_endpoint'], json=raw_data)
    
    # In ra response để kiểm tra
    print("Response từ MoMo:", response.status_code)
    print(response.text)
    
    try:
        result = response.json()
        
        # Cập nhật thông tin thanh toán
        if 'payUrl' in result:
            # Thành công, có URL thanh toán
            payment.message = result.get('message', '')
            payment.save()
            return {
                'status': 'success',
                'payment_url': result['payUrl'],
                'order_id': order_id
            }
        else:
            # Thất bại
            payment.status = 'failed'
            payment.message = result.get('message', 'Unknown error')
            payment.save()
            return {
                'status': 'failed',
                'message': result.get('message', 'Unknown error')
            }
    except Exception as e:
        # Xử lý lỗi khi parse JSON
        print("Lỗi khi xử lý response:", str(e))
        payment.status = 'failed'
        payment.message = str(e)
        payment.save()
        return {
            'status': 'failed',
            'message': str(e)
        }
def verify_momo_response(data):
    # Kiểm tra dữ liệu đầu vào
    required_fields = [
        'partnerCode', 'orderId', 'requestId', 'amount',
        'responseTime', 'message', 'resultCode', 'signature'
    ]
    
    for field in required_fields:
        if field not in data:
            return {
                'status': 'invalid',
                'message': f'Missing required field: {field}'
            }

    # Lấy dữ liệu từ request
    partner_code = data['partnerCode']
    order_id = data['orderId']
    request_id = data['requestId']
    amount = data['amount']
    response_time = data['responseTime']
    message = data['message']
    result_code = data['resultCode']
    transaction_id = data.get('transId', '')
    signature = data['signature']
    extra_data = data.get('extraData', '')
    order_type = data.get('orderType', '')
    pay_type = data.get('payType', '')

    # Tạo chuỗi raw signature theo đúng thứ tự MoMo yêu cầu
    # Chú ý: Thứ tự các tham số rất quan trọng và phải theo quy định của MoMo
    raw_signature = (
        f"accessKey={CONFIG['access_key']}"
        f"&amount={amount}"
        f"&extraData={extra_data}"
        f"&message={message}"
        f"&orderId={order_id}"
        f"&orderInfo={data.get('orderInfo', '')}"
        f"&orderType={order_type}"
        f"&partnerCode={partner_code}"
        f"&payType={pay_type}"
        f"&requestId={request_id}"
        f"&responseTime={response_time}"
        f"&resultCode={result_code}"
        f"&transId={transaction_id}"
    )

    # Tạo chữ ký xác thực
    verify_signature = hmac.new(
        CONFIG['secret_key'].encode('utf-8'),
        raw_signature.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    # Debug log (nên bật trong môi trường dev)
    print("MoMo callback data:", data)
    print("Raw signature for verification:", raw_signature)
    print("Generated signature:", verify_signature)
    print("Received signature:", signature)

    # Xác thực chữ ký
    if signature != verify_signature:
        return {
            'status': 'invalid',
            'message': 'Invalid signature',
            'debug': {
                'expected': verify_signature,
                'received': signature,
                'raw_signature': raw_signature
            }
        }

    # Cập nhật database
    try:
        payment = MomoPayment.objects.get(
            order_id=order_id,
            request_id=request_id
        )
        
        payment.transaction_id = transaction_id
        payment.message = message
        payment.response_time = datetime.datetime.fromtimestamp(int(response_time)/1000)
        payment.status = 'completed' if result_code == '0' else 'failed'
        payment.save()

        return {
            'status': 'verified',
            'payment': payment
        }
        
    except MomoPayment.DoesNotExist:
        return {
            'status': 'invalid',
            'message': 'Payment record not found'
        }