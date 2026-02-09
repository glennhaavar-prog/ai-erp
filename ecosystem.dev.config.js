module.exports = {
  apps: [
    {
      name: 'kontali-backend-dev',
      cwd: '/home/ubuntu/.openclaw/workspace/ai-erp/backend',
      script: 'venv/bin/uvicorn',
      args: 'app.main:app --host 0.0.0.0 --port 8000 --reload',
      interpreter: 'none',
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        PYTHONPATH: '/home/ubuntu/.openclaw/workspace/ai-erp/backend'
      }
    },
    {
      name: 'kontali-frontend-dev',
      cwd: '/home/ubuntu/.openclaw/workspace/ai-erp/frontend',
      script: 'npm',
      args: 'run dev',
      interpreter: 'none',
      autorestart: true,
      watch: false,
      max_memory_restart: '1G'
    }
  ]
};
