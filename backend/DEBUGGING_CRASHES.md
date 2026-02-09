# 🔍 Debugging Backend Crashes

**Problem:** Backend prosess dør uventet uten klar feilmelding.

**Date discovered:** 2026-02-08 21:42 UTC  
**Context:** Glenn testet frontend → "Laster klienter..." spinner indefinitely → Backend var død

---

## Root Cause Analysis Process

### 1. Check if backend is running

```bash
ps aux | grep uvicorn
# or
lsof -i :8000
```

**If no process:** Backend has crashed or was killed.

### 2. Check backend logs

```bash
tail -100 /tmp/backend.log
# or (if using systemd)
journalctl -u kontali-backend -n 100
```

**Look for:**
- `ERROR`, `CRITICAL`, `Exception`, `Traceback`
- `killed`, `terminated`, `signal`
- Last log entry timestamp (when did it die?)

### 3. Check system logs for OOM killer

```bash
sudo dmesg | grep -i "out of memory\|oom\|killed process"
# or
sudo journalctl --since "1 hour ago" | grep -i "oom\|killed"
```

**Common pattern:**
```
Out of memory: Killed process 12345 (python3) total-vm:2048000kB
```

This means **system ran out of memory** and killed the process to protect itself.

### 4. Check system resources

```bash
free -h        # Current memory usage
df -h          # Disk space
top -b -n 1    # CPU/memory per process
```

**Red flags:**
- Available memory < 500MB
- No swap space configured
- Disk > 90% full

### 5. Check for memory leaks

```bash
# Start backend with memory monitoring
python3 -m memory_profiler app/main.py

# or use tracemalloc (built-in)
python3 -X tracemalloc=5 -m uvicorn app.main:app
```

---

## Common Causes & Fixes

### Cause 1: OOM Killer (Out of Memory)

**Symptoms:**
- Process dies suddenly
- No error in application logs
- dmesg shows "Out of memory: Killed process"

**Root cause:**
- No swap space configured
- Memory leak in application
- Too many workers spawned

**Fix:**
```bash
# 1. Add swap space (2GB)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# 2. Limit uvicorn workers
uvicorn app.main:app --workers 2  # instead of auto

# 3. Set memory limits in systemd (see kontali-backend.service)
MemoryMax=2G
MemoryHigh=1.5G
```

### Cause 2: Unhandled Exception

**Symptoms:**
- Traceback in logs
- Specific error message

**Fix:**
- Read the traceback
- Fix the bug in code
- Add proper error handling
- Restart backend

### Cause 3: Database Connection Lost

**Symptoms:**
- Logs show "connection refused" or "connection closed"
- Happens after period of inactivity

**Fix:**
```python
# Add connection pool recycling in database.py
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Check connections before use
    pool_recycle=3600,   # Recycle connections after 1 hour
)
```

### Cause 4: Port Already in Use

**Symptoms:**
- Backend fails to start
- Error: "Address already in use"

**Fix:**
```bash
# Find process using port 8000
lsof -i :8000

# Kill it
kill <PID>

# Or kill all uvicorn processes
pkill -f uvicorn
```

---

## Robust Solution: Systemd Service

**Why systemd?**
- Auto-restart on crash
- Automatic start on boot
- Resource limits (memory, CPU)
- Proper logging with rotation
- Watchdog (kills if process hangs)

**Setup:**
```bash
# 1. Create log directory
sudo mkdir -p /var/log/kontali
sudo chown ubuntu:ubuntu /var/log/kontali

# 2. Copy service file
sudo cp kontali-backend.service /etc/systemd/system/

# 3. Reload systemd
sudo systemctl daemon-reload

# 4. Enable auto-start
sudo systemctl enable kontali-backend

# 5. Start service
sudo systemctl start kontali-backend

# 6. Check status
sudo systemctl status kontali-backend
```

**View logs:**
```bash
# Real-time
sudo journalctl -u kontali-backend -f

# Last 100 lines
sudo journalctl -u kontali-backend -n 100

# Since boot
sudo journalctl -u kontali-backend -b
```

**Restart if needed:**
```bash
sudo systemctl restart kontali-backend
```

---

## Prevention: Monitoring & Alerts

### 1. Healthcheck Cron Job

```bash
# Add to crontab (every 5 minutes)
*/5 * * * * /home/ubuntu/.openclaw/workspace/ai-erp/backend/healthcheck.py --quiet || (systemctl restart kontali-backend && echo "Backend crashed, restarted at $(date)" | mail -s "Kontali Backend Restart" admin@example.com)
```

### 2. Log Rotation

```bash
# Create /etc/logrotate.d/kontali
sudo tee /etc/logrotate.d/kontali <<EOF
/var/log/kontali/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 ubuntu ubuntu
    sharedscripts
    postrotate
        systemctl reload kontali-backend > /dev/null 2>&1 || true
    endscript
}
EOF
```

### 3. Memory Usage Monitoring

```bash
# Add to crontab (every hour)
0 * * * * ps aux | awk '/uvicorn/{print $6/1024" MB - "$11" "$12}' >> /var/log/kontali/memory-usage.log
```

---

## Emergency Recovery

**If backend is down and you need to restore service NOW:**

```bash
# 1. Kill any stuck processes
pkill -9 -f uvicorn

# 2. Check database is running
sudo systemctl status postgresql

# 3. Check Redis is running
sudo systemctl status redis-server

# 4. Start backend manually (temporary)
cd /home/ubuntu/.openclaw/workspace/ai-erp/backend
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2 > /tmp/backend.log 2>&1 &

# 5. Verify it's working
curl http://localhost:8000/health

# 6. Check logs
tail -f /tmp/backend.log
```

---

## Lessons Learned (2026-02-08)

**What we did wrong:**
1. No systemd service → Manual restart required
2. No swap space → OOM killer strikes without warning
3. No healthcheck monitoring → Didn't know it was down
4. Logs to /tmp → Overwritten on restart
5. No documentation → Had to guess what happened

**What we did right:**
1. Investigated root cause (this document)
2. Created systemd service with auto-restart
3. Added healthcheck script
4. Documented debugging process
5. Set up monitoring plan

**Key principle:** 
> "We do things properly upfront, test EVERYTHING, always try to understand WHY something fails, then fix it properly afterwards to create a robust system." - Glenn

---

**Status:** 
- ✅ systemd service created
- ✅ Healthcheck script created  
- ✅ Debugging guide documented
- 🔄 TODO: Install as systemd service (requires sudo)
- 🔄 TODO: Set up swap space (requires sudo)
- 🔄 TODO: Set up cron monitoring (requires crontab)
