import os
from google import genai

client = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"]
)

def ask_zentromart_support(question: str):
    system_instruction = (
        "You are ZentroMart's customer support AI assistant. "
        "Your first reply to any customer must clearly state that you are an AI assistant. "
        "Answer customer queries politely."
    )
    
    # Using the official recommended model
    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=f"{system_instruction}\n\nCustomer Question: {question}"
    )
    return response.text

if __name__ == "__main__":
    test_question = "I opened the Neelam Eau de Parfum 50 ml and tried it once. Can I still return it?"
    print(f"Asking: {test_question}\n")
    answer = ask_zentromart_support(test_question)
    print(f"Agent Reply:\n{answer}")