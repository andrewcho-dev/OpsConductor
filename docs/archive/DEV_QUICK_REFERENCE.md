# 🚀 ENABLEDRM Development Quick Reference

## Essential Commands

```bash
# Start development environment
./dev-start.sh

# Check all services status
./dev-status.sh

# Stop development environment  
./dev-stop.sh
```

## Access Points

- **🌟 Main App (Login)**: https://localhost
- **React Dev**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Login Credentials

- **Username**: admin
- **Password**: admin123

## Service Status Indicators

✅ All services should show green checkmarks:
- ✅ React dev server running
- ✅ Backend API responding  
- ✅ Nginx proxy working
- ✅ Database ready
- ✅ Redis responding
- ✅ Login endpoint working

## Troubleshooting

```bash
# View React logs
tail -f frontend-dev.log

# View React in real-time
screen -r react-dev

# View backend logs
docker compose logs -f backend

# Emergency restart
./dev-stop.sh && sleep 5 && ./dev-start.sh
```

## 📖 Full Documentation

See [DEVELOPMENT_ENVIRONMENT_GUIDE.md](./DEVELOPMENT_ENVIRONMENT_GUIDE.md) for complete procedures.

---
*Always use the official scripts - never start services manually!*