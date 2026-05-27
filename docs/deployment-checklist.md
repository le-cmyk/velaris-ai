# Deployment Validation Checklist

- [ ] Backend health endpoint works
- [ ] Frontend loads
- [ ] Login works
- [ ] JWT token stored correctly
- [ ] Chat endpoint responds
- [ ] Safe SELECT query works
- [ ] Dangerous query creates approval request
- [ ] Approval request appears in UI
- [ ] Approving executes or simulates action correctly
- [ ] Rejecting blocks action
- [ ] Audit logs are created
- [ ] Tool calls are visible
- [ ] No direct database access from agent runtime
- [ ] CORS works from Vercel domain
- [ ] Environment variables are set correctly
