# Technical Debt & Known Limitations

## Reply Detection on Resent Emails

**Issue:** When an email is resent, the `gmail_thread_id` is updated to the new message's thread ID. If the recipient replies to a previous send (not the latest resend), the reply will not be detected.

**Scenario:**
1. Email sent → `thread_id = ABC123`
2. Email resent → `thread_id = XYZ789` (overwrites)
3. Recipient replies to first email → Reply arrives in `ABC123`
4. `check_reply` only checks `XYZ789` → Reply NOT detected ❌

**Impact:** Low (uncommon user behavior)

**Solution:** Maintain a history of `thread_ids` per email instead of overwriting.

**Effort:** Medium

---

Add more items as you find them!