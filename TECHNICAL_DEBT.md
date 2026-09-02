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
```

## Account Switching and Unsaved Drafts

Account selection is per browser tab. Switching reloads the workspace after
confirmation, so unsaved messages and form edits are discarded. Persistent
per-account drafts are not implemented.

## Local Data and Public Hosting

Multiple Gmail accounts have backend-enforced ownership, but this is not a
hardened public hosting setup. The default Compose ports bind to host interfaces;
network isolation, HTTPS and abuse controls need review before public exposure.

Only Google credentials are encrypted by the application. Email bodies,
attachments and backup archives are not encrypted. Protect the host files and
back up the encryption key with the database.

## Upload Lifecycle and Send Consistency

Deleting an email removes its database attachment rows but does not remove
physical uploads. Failed sends can also leave uploaded files behind; there is no
automatic orphan-file cleanup.

Gmail sending and local database commits are separate operations. If Gmail
accepts a message but local persistence fails, the message may be sent without
a matching history record. Retrying blindly can send it again. A durable outbox
or reconciliation workflow is future work.

## Connection Lifecycle

Disconnecting a Gmail clears local credentials and session membership across
browsers while preserving data. It does not revoke the app's grant at Google.
The status endpoint reports a local connection, not guaranteed current validity
of Google access. Reauthorization may still be needed.

The migration rehearsal/verification helpers specifically target the original
single-account database. They are not general integrity tools for an active
multi-account installation. See [backup scope](backend/ACCOUNTS.md).
