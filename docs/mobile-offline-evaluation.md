# Mobile / Offline Evaluation (GA-037)

## Assessment: Ugavi 0.1.0

### Frappe v16 Mobile Capabilities

| Feature | Frappe v16 Support | Assessment |
|---------|-------------------|------------|
| Responsive Desk UI | ✅ Native Frappe UI v2 (Bootstrap 5) | Works on tablets, small screens |
| PWA (offline) | ⚠️ Frappe does not natively support offline PWA | Not in scope for MVP |
| Mobile app | ✅ Frappe framework supports custom field | Requires Frappe Ionic app build (not MVP) |

### MVP Decision
- **Desktop-first**: All operations assume stable internet connection
- **Mobile-responsive**: UI adapts to tablet/mobile for read-only views (bid status check, stock queries)
- **No offline mode**: Bid submission, stock updates require live server connection
- **Future**: Consider Frappe Ionic mobile app for field stock verification / asset verification with offline sync in v1.0

### Risk Acceptance
- Field users without internet access cannot submit bid confirmations or stock movements
- Mitigation: Documented as known limitation in user guides (GA-083)