import json
from together import Together

client = Together(api_key="75c9027a4aeca8e6415b7818ece22762cd806a3b7620e28f93c630e548d536b8")

def get_weather(location):
    # giả lập dữ liệu thời tiết
    return f"The weather in {location} is sunny, 32 °C"

tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get current temperature for a given location.",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string"}
            },
            "required": ["location"]
        }
    }
}]

messages = [{"role": "user", "content": "Get current temperature in Ha Noi"}]

# --- vòng 1: model quyết định có gọi hàm hay không ---
resp = client.chat.completions.create(
    model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
    messages=messages,
    tools=tools,
    tool_choice="auto"
)

msg = resp.choices[0].message
if msg.tool_calls:
    for call in msg.tool_calls:
        fn_name = call.function.name              # "get_weather"
        args = json.loads(call.function.arguments) # {"location": "Ha Noi"}

        # thực thi hàm Python thật
        result = get_weather(**args)

        # gắn phản hồi của hàm vào lịch sử chat
        messages.append(msg)          # assistant message chứa tool_calls
        messages.append({
            "role": "tool",
            "tool_call_id": call.id,  # ID do model sinh ra
            "content": result         # kết quả hàm
        })

    # --- vòng 2: cho model “nói” với người dùng ---
    final = client.chat.completions.create(
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
        messages=messages
    )
    print(final.choices[0].message.content)
else:
    # model không gọi hàm, trả lời ngay
    print(msg.content)
