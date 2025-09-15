
CONFIG = {
     "partner_code": "MOMOBKUN20180529",
    "access_key": "klm05TvNBzhg7h7j",
    "secret_key": "at67qH6mk8w5Y1nAyMoYKMWACiEi2bsa",
    "card_number_test":"9704000000000018",
    "date_out_card_test":"03/07",
    "name_user_test":"NGUYEN VAN A",
    "OTP_code":"OTP",
    "phone_number":"0123456789",\
    'return_url': 'http://localhost:8000/payment/momo/result/',  # URL nhận kết quả từ MoMo
    'notify_url': 'http://localhost:8000/payment/momo/ipn/',  # URL để MoMo gửi IPN (Instant Payment Notification)
    'test_endpoint': 'https://test-payment.momo.vn/v2/gateway/api/create', # Endpoint test
}