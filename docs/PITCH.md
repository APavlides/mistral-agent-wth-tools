# Pitch: Order Support Agent

**One-liner:** An assistant that answers "where is my order?" from your order records, in seconds, around the clock.

**Opening question:** "How many support contacts a day are just 'where is my order?'"

1. **Problem:** A team handling around 300 order questions a day loses hours to the same lookups.
2. **Solution:** Customers ask in plain English; it checks the records and replies instantly.
3. **What I built:** Let me show you. *(switch to the app)*
4. **Next steps:** Today it uses sample orders and doesn't verify the customer. A 3-week pilot connects your order system.
5. **Thank you:** Instant, accurate order answers, so your team handles the hard cases.

**Demo:**
1. Type the first question and press **Send**.
2. Point at the 🔧 lines: "it found Ben's orders, then looked each one up."
3. Show the reply matches the record: desk lamp and bulb, arriving 14 November.
4. Type the second question: it says the order isn't found instead of inventing one.

```
What orders does ben@example.com have and when does each arrive?
```

```
Where is order ZZZ?
```

**Likely questions:**
- *Is our data safe?* Today only looked-up order details go to Mistral's hosted API; Mistral's open-weight models can run on your own infrastructure.
- *How accurate is it?* Facts come only from your records, every lookup is shown, and missing orders are reported. The pilot scores answers against real tickets.
- *Why Mistral?* Mistral Small with function calling: fast and low-cost for short questions, from a European provider.

**Close:** "Can we start a 3-week pilot next month?"
