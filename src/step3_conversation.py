import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from step2_rag import ask_with_rag
from tools.tools import lookup_order, create_ticket



class ZentroMartAgent:
    def __init__(self):
        self.history = []
        self.order_id = None
        self.verified = False
        self.verification_attempts = 0
        self.order_details = None
        self.greeted = False
        self.last_sources = []

    def reply(self, message):
        text = message.strip()
        lower = text.lower()

                # Convert spoken order-ID digits into numbers.
        digit_words = {
            "zero": "0", "oh": "0",
            "one": "1", "two": "2", "three": "3",
            "four": "4", "five": "5", "six": "6",
            "seven": "7", "eight": "8", "nine": "9",
        }

        spoken_digits = []
        for word in lower.replace("-", " ").split():
            word = word.strip(".,?!:'\"")
            if word in digit_words:
                spoken_digits.append(digit_words[word])
            elif spoken_digits:
                break

        if len(spoken_digits) >= 4:
            text = "".join(spoken_digits)
            lower = text.lower()

        self.last_sources = []

        if not self.greeted:
            self.greeted = True

        # Reply to greeting-only messages.
        if lower.strip() in ("hi", "hello", "hey", "good morning", "good afternoon", "good evening"):
            return "Hi! I'm ZentroMart's AI support assistant. How can I help you today?"

        # Handle human handover before order verification.
        if any(term in lower for term in (
            "human", "real person", "speak to someone",
            "talk to someone", "human agent"
        )):
            summary = (
                f"Issue: {text}. Intent: escalation. "
                f"Order ID: {self.order_id or 'not provided'}. "
                "Checks: customer message reviewed. "
                "Reason: customer requested a human agent."
            )

            ticket = create_ticket(
                summary=summary,
                order_id=self.order_id,
                reason="Customer requested human handover",
                intent="escalation"
            )

            if ticket.get("created"):
                return (
                    f"I've created a support ticket "
                    f"({ticket['ticket_id']}). A human colleague "
                    "will follow up. I can't promise a specific outcome."
                )

            return (
                "I couldn't create the handover ticket just now. "
                "Please contact customer support directly."
            )

        
        # Ask for an order ID only when the customer needs help
        # with a specific order, not for general policy questions.
        personal_order_phrases = (
            "where is my order",
            "where is my package",
            "track my order",
            "track my package",
            "my order status",
            "order status",
            "when will my order arrive",
            "when will it arrive",
            "has my order shipped",
            "has it shipped",
            "cancel my order",
            "cancel this order",
            "cancel my",
            "change my delivery address",
            "change my order",
            "my delivery is late",
            "my order is late",
            "my order is delayed",
            "when is it expected to arrive",
        )

        if (
            any(phrase in lower for phrase in personal_order_phrases)
            and not self.order_id
        ):
            self.history.append(("user", text))
            return (
                "I can help check that for you. "
                "What's your order ID?"
            )


        # Capture the order ID, then request verification.
        if self.order_id is None and any(ch.isdigit() for ch in text):
            digits = "".join(ch for ch in text if ch.isdigit())
            if len(digits) >= 4:
                self.order_id = digits
                lookup_order(self.order_id)
                self.history.append(("user", text))
                return (
                    "Thanks. To verify your order, please provide "
                    "either the last 4 digits of your registered "
                    "phone number or the delivery pincode."
                )

        # Verification is required before showing order details.
        if self.order_id and not self.verified:
            result = lookup_order(self.order_id, text)

            if result.get("verified") and result.get("found"):
                self.verified = True
                self.order_details = result
                self.history.append(("user", text))
                return (
                    "Thanks, your order is verified. "
                    "What would you like help with?"
                )

            self.verification_attempts += 1
            if self.verification_attempts >= 2:
                self.order_id = None
                return (
                    "I couldn't verify the details, so I can't share "
                    "order information. Please contact support from "
                    "your registered phone number."
                )

            return (
                "That didn't match our verification requirements. "
                "Please try once more with the phone's last 4 digits "
                "or the delivery pincode."
            )

        # Escalate requests for a human or urgent safety concerns.
        urgent_terms = (
            "human", "real person", "police", "consumer court",
            "legal action", "burning smell", "sparks",
            "swelling battery", "injury"
        )

        if any(term in lower for term in urgent_terms):
            summary = (
                f"Issue: {text}. Intent: escalation. "
                f"Order ID: {self.order_id or 'not provided'}. "
                "Checks: customer message reviewed. "
                "Reason: escalation requested or safety/legal concern."
            )
            ticket = create_ticket(
                summary=summary,
                order_id=self.order_id,
                reason="Human handover or urgent concern",
                intent="escalation"
            )

            if ticket.get("created"):
                return (
                    f"I've created a support ticket "
                    f"({ticket['ticket_id']}). A human colleague "
                    "will follow up. I can't promise a specific outcome."
                )

            return (
                "I couldn't create the handover ticket just now. "
                "Please contact customer support directly."
            )

        
        # Handle standalone polite replies only.
        if lower.strip() in (
            "thank you", "thanks", "ok thanks", "okay thanks",
            "okay", "ok", "you're welcome",
            "thats helpful", "that's helpful"
        ):
            return "You're welcome! Is there anything else I can help you with?"
        
        # Handle order-tracking questions using verified order details.
        
        tracking_terms = (
            "where is my order",
            "where is it",
            "where's my order",
            "track my order",
            "track order",
            "order status",
            "delivery status",
            "when will my order arrive",
            "when will it arrive",
            "when will it be delivered",
            "has my order shipped",
            "has it shipped",
            "any update on my order",
            "any update on the order",
            "any update on my delivery",
            "where is my parcel",
            "where is my package",
            "when is it expected to arrive",
        )

        if any(term in lower for term in tracking_terms):
            if not self.verified or not self.order_details:
                return (
                    "I can help track your order. "
                    "Please provide your order ID first."
                )

            status = (
                self.order_details.get("status") or "unknown"
            ).replace("_", " ").lower()

            promised_date = (
                self.order_details.get("promised_date")
            )

            response = f"Your order status is: {status}."

            
            from datetime import date

            response = f"Your order status is: {status}."

            if promised_date:
                response += (
                    f" The promised delivery date is {promised_date}."
                )

                try:
                    delivery_date = date.fromisoformat(
                        str(promised_date)[:10]
                    )
                    today = date.today()

                    if (
                        delivery_date < today
                        and status not in ("delivered", "cancelled")
                    ):
                        response += (
                            " This date has already passed, so your "
                            "order appears to be overdue. I can't confirm "
                            "a new delivery date from the available data. "
                            "Please contact support for an update."
                        )
                except ValueError:
                    pass

            return response

        # Explain why the assistant cannot cancel an order directly.
        if "why" in lower and "cancel" in lower and (
            "you" in lower or "can't" in lower or "cannot" in lower
        ):
            return (
                "I can explain the cancellation policy, but I can't make "
                "changes to your order directly. Please use My Orders in "
                "the ZentroMart app to request cancellation."
            )

        # Handle cancellation and related follow-up questions.
        cancel_words = ("cancel", "cancellation", "why you can't", "why can't you", "why can not you")

        if any(word in lower for word in cancel_words):
            if not self.verified or not self.order_details:
                return "I can help with cancellation. What's your order ID?"

            status = (self.order_details.get("status") or "").lower()

            # Explain why the assistant cannot cancel directly.
            if "why" in lower and (
                "you" in lower or "can't" in lower or "cannot" in lower
            ):
                return (
                    "As an AI assistant, I don't have"
                    " direct access to modify your account" 
                    " or trigger backend cancellations."
                    " Cancellation requests must be submitted" 
                    " directly by you through 'My Orders' in"
                    " the ZentroMart app."
                )

            # Explain the steps when the customer asks how to cancel.
            if any(phrase in lower for phrase in (
                "how", "what do i do", "what should i do",
                "what do i have to do", "steps", "tell me"
            )):
                if status in ("placed", "packed"):
                    return (
                        f"Your order is currently marked as '{status}'. "
                        "Open the ZentroMart app, go to My Orders, select "
                        "your order, and check whether the Cancel Order "
                        "option is available. If it is, follow the prompts. "
                        "If it isn't, contact customer support."
                    )

                if status in (
                    "shipped", "out_for_delivery", "delivery_attempted"
                ):
                    return (
                        "Your order is marked as already shipped or in "
                        "delivery, so cancellation may no longer be "
                        "available. Check My Orders in the app or contact "
                        "customer support for your available options."
                    )

            # Handle the initial cancellation request using stored status.
            if status in ("placed", "packed"):
                return (
                    f"Your order is currently marked as '{status}', "
                    "so it may be eligible for cancellation. Please "
                    "check My Orders in the ZentroMart app. I can't "
                    "cancel it directly for you."
                )

            if status in (
                "shipped", "out_for_delivery", "delivery_attempted"
            ):
                return (
                    "Your order is marked as shipped or in delivery, "
                    "so it may no longer be eligible for cancellation. "
                    "Please check the app or contact customer support."
                )

            if status == "cancelled":
                return (
                    "This order is already marked as cancelled. "
                    "If you need help with your refund, I can check "
                    "the relevant refund policy."
                )

            return (
                f"Your order is currently marked as '{status}'. "
                "I can't confirm whether cancellation is available. "
                "Please contact customer support for help."
            )

        # Use RAG for other policy questions and follow-ups.
        answer, sources = ask_with_rag(text)

        self.last_sources = sources

        if not answer or not answer.strip():
            answer = (
                "I'm sorry, I couldn't find a clear answer to that. "
                "Would you like me to connect you with a human agent?"
            )

        self.history.append(("user", text))
        self.history.append(("assistant", answer))
        return answer


if __name__ == "__main__":
    agent = ZentroMartAgent()
    print("ZentroMart Step 3 — Conversation Agent")
    print("Type 'exit' to quit.\n")

    while True:
        message = input("You: ").strip()

        if message.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break

        if message:
            try:
                print("\nAgent:", agent.reply(message), "\n")
            except Exception as error:
                print(f"\nSomething went wrong: {error}\n")
