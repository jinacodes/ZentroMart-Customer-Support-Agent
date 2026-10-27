# ZentroMart Capstone — Testing Log

**Project:** ZentroMart AI Customer Support Assistant
**Course:** From Tokens to Transformers: GenAI × LLM Mastery
**Testing period:** 23 October 2026

## Test 1: Order Verification — Incorrect Verification Value

**Objective:** Check whether the agent protects customer order information when verification fails.

**Test performed:**

- Entered order ID `41763040`.
- Entered an incorrect verification value (`1111`) twice.

**Expected behaviour:**

- Reject incorrect verification values.
- Allow one retry.
- Refuse to reveal order details after two failed attempts.

**Actual result:** PASS

The agent rejected the first incorrect value, requested another attempt, and refused to share order information after the second failure. It then reset the order ID.

**Conclusion:** The basic verification failure flow worked as expected.

---

## Test 2: Recovery After Failed Verification

**Objective:** Check whether the agent can start a new order lookup after verification fails twice.

**Test performed:**

- After two failed verification attempts for the previous order, requested order information again.
- Entered a new order ID: `71577152`.
- Provided the matching verification value (`1684`).

**Expected behaviour:**

- Ask for a new order ID.
- Verify the new order independently.
- Use the newly verified order's details when answering subsequent questions.

**Actual result:** PASS

The agent accepted the new order ID, verified it successfully, and continued the conversation.

**Conclusion:** The agent recovered successfully after the failed verification flow.

---

## Test 3: Tracking an Overdue Order

**Objective:** Check whether the agent can identify an order whose promised delivery date has passed.

**Test performed:**

- Verified order `41763040`.
- Asked: "When will my order arrive?"
- The stored status was `delivery_attempted`.
- The promised delivery date was `2026-10-20`.

**Issue identified:** The original tracking handler returned the order status and promised date but did not recognize that the date had already passed.

**Improvement implemented:** Added date comparison logic to detect a passed promised date for orders that are neither delivered nor cancelled.

**Actual result:** PASS

The agent identified the order as apparently overdue, avoided inventing a new delivery date, and advised the customer to contact support for an update.

**Conclusion:** The tracking response became more useful and handled overdue orders more appropriately.

---

## Test 4: Tracking an Order with Status "Packed"

**Objective:** Check whether the tracking handler works with different customer phrasings and order statuses.

**Test performed:**

- Verified order `71577152`.
- The stored status was `packed`.
- The promised delivery date was `2026-10-27`.
- Asked: "where is it?"

**Issue observed during initial testing:** The same question was initially sent to the RAG system, which returned a generic answer saying it could not find the information in the company documents.

**Retest:** Restarted the agent and repeated the conversation without making another code change.

**Actual result:** PASS on retest

The agent returned the stored status, `packed`, and the promised delivery date, `2026-10-27`.

**Conclusion:** The tracking handler worked on the retest. The reason for the initial inconsistent result has not been confirmed, so it should not be recorded as a definitively resolved code bug.

## Test 5: Tracking an Already-Delivered Order

**Objective:** Check whether the agent correctly handles an order that has already been delivered.

**Test performed:**
- Verified order `46637226`.
- The stored status was `delivered`.
- The promised delivery date was `2026-10-08`.
- Asked: "where is it?"

**Expected behaviour:**
- Confirm that the order has already been delivered.
- Refer to the promised delivery date in the past tense.
- Avoid describing the order as overdue.

**Actual result:** PARTIAL PASS

The agent correctly retrieved the delivered status and promised date. However, its response was grammatically awkward: "Your order status is: delivered. The promised delivery date is 2026-10-08."

**Improvement identified:** Use a more natural response for delivered orders, such as: "Your order has already been delivered. The promised delivery date was October 8, 2026."

**Conclusion:** The order data was retrieved correctly, but the response wording needs improvement.

## Test 6: Cancellation of an Order That Has Not Shipped

**Objective:** Check whether the agent gives appropriate cancellation guidance for an order that has not shipped.

**Test performed:**
- Verified order `71577152`.
- The stored status was `packed`.
- Asked to cancel the order.

**Expected behaviour:**
- Require successful verification before giving order-specific guidance.
- Explain that the order may be eligible for cancellation.
- Direct the customer to the appropriate cancellation process.
- Never claim to cancel the order without an actual cancellation tool.

**Actual result:** PASS

The agent explained that the order may be eligible for free cancellation, directed the customer to My Orders in the ZentroMart app, and clarified that it cannot cancel the order directly.

**Conclusion:** The cancellation guidance for a packed order worked as expected. Actual cancellation was not performed or verified.


## Test 7: Cancellation of an Already-Shipped Order

**Objective:** Check whether the agent correctly handles cancellation requests for shipped orders.

**Test performed:**
- Verified order `69520867`.
- The stored status was a shipped state.
- Asked to cancel the order.

**Expected behaviour:**
- Explain that a shipped order cannot be cancelled through the normal cancellation process.
- Offer refusing the parcel at delivery or accepting it and returning it if eligible.
- Avoid claiming that the order was cancelled.

**Actual result:** PASS

The agent explained that the order could no longer be cancelled and offered both alternatives: refusing the parcel at the door or accepting delivery and returning it if eligible.

**Conclusion:** The shipped-order cancellation response worked as expected. Neither cancellation nor return was actually performed.

### Test 8: Damaged grocery policy — Step 2 RAG — PASS

**Component tested:** Step 2 — Retrieval-Augmented Generation (RAG)

**Question:** What should I do if my groceries arrive damaged?

**Expected behaviour:** Retrieve the relevant damaged/wrong/missing items policy sections and explain the reporting deadline, required evidence, and available resolutions.

**Initial result:** The retriever selected less relevant sections and omitted important policy details, particularly DWM-1 (Reporting window) and DWM-2 (Resolution). As a result, the initial answer did not fully explain what the customer should do.

**Changes made:**
- Increased the minimum number of retrieved sections from 4 to 6.
- Added a scoring boost for relevant sections from `POL-DWM` when the question mentions damaged, defective, expired, wrong, or missing items.
- Updated the prompt to request direct, actionable answers based on the retrieved evidence.

**Final result:** The agent correctly stated that the issue must be reported within 48 hours of delivery, photos of the item and packaging are required, and a free replacement or full refund (including delivery fees) is available after verification. It also correctly stated that no reverse pickup fee applies.

**Evidence retrieved:** POL-DWM sections DWM-1 (Reporting window) and DWM-2 (Resolution), along with related policy sections.

**Result:** PASS. The retrieval changes improved the evidence selected for this question and produced a complete policy-based answer.

---

### Test 9: Damaged grocery policy — Step 3 Conversation Agent — PASS

**Component tested:** Step 3 — Conversation Agent, using the updated Step 2 RAG system.

**Conversation:**
1. Customer: `hi`
2. Customer: `What should I do if my groceries arrive damaged?`

**Expected behaviour:** The conversation agent should answer the general policy question without unnecessarily requesting an order ID or order verification. It should provide the correct deadline, required evidence, and available resolutions.

**Actual result:** The agent answered the question directly. It correctly explained the 48-hour reporting deadline, the requirement for photos of the item and packaging, and the availability of a free replacement or full refund (including delivery fees) after verification. It also stated that no reverse pickup fee applies.

**Result:** PASS. The improved RAG behaviour carried through to the Step 3 conversation flow, and the agent answered this general policy question without requiring order verification.

**Note:** This test confirms the behaviour for this specific question. Additional testing is needed to establish consistency across other policy questions and conversation scenarios.

### Test 10: General Missing-Item Policy — Step 3 Conversation Agent
**Input:** “I received my grocery order, but one item is missing. What should I do?”

**Expected behavior:** Answer using the relevant policy without requiring an order ID.

**Actual behavior:** The agent retrieved policy evidence and explained the 48-hour reporting deadline, photo evidence, free replacement or full refund including delivery fees, and no reverse-pickup fee.

**Result:** PASS

**Fix applied:** Replaced the broad order-keyword check with specific personal-order phrases, allowing general policy questions to reach RAG.

### Test 11: Personal Order Tracking — Step 3 Conversation Agent
**Input:** “Where is my order?”

**Expected behavior:** Request an order ID before attempting to provide personal tracking information.

**Actual behavior:** The agent asked, “I can help check that for you. What's your order ID?”

**Result:** PASS

---

## Current Status

The following behaviours have been tested successfully:

- Incorrect order verification is rejected.
- Repeated verification failure prevents order details from being shared.
- The agent can recover and verify a different order.
- Overdue orders receive an appropriate delay warning.
- Tracking questions can return stored order status and promised delivery dates.

**Important limitation:** These tests use synthetic project data. The assistant reports stored order information; it does not have live courier tracking.

## Remaining Tests

- [ ] Tracking an already-delivered order
- [ ] Tracking other order statuses
- [ ] Cancellation of an order that has not shipped
- [ ] Cancellation request for a shipped order
- [ ] Damaged, wrong, or missing items
- [ ] Human handover and ticket-file verification
- [ ] Incorrect order ID and verification edge cases
- [ ] Broader testing with the supplied practice questions
