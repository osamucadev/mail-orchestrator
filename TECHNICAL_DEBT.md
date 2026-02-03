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

## Windows Dev Environment: Backend Reload Kills Frontend

**Issue:**  
On Windows, when running backend and frontend in the same terminal (for example via a single root `npm run dev`), restarting the backend with `uvicorn --reload` can cause the frontend dev server (Vite) to exit unexpectedly.

This usually manifests as a console prompt like:
> “Deseja finalizar o arquivo em lotes (S/N)?”

**Cause:**  
The Uvicorn reload mechanism (both `WatchFiles` and `StatReload`) sends a console-level signal when restarting the process.  
On Windows, this signal can propagate to other processes running in the same console group, including `npm.cmd`, causing the frontend process to terminate.

**Impact:**  
- Frontend dev server stops when backend reloads
- No impact in production
- Windows-only issue

**Workaround (Recommended):**
Run backend and frontend in **separate terminals**.

Both projects already provide their own dev scripts:

```bash
# Terminal 1
npm run dev:frontend

# Terminal 2
npm run dev:backend
