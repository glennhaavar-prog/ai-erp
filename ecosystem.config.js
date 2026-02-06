module.exports = {
  apps: [
    {
      name: 'kontali-backend',
      cwd: '/home/ubuntu/.openclaw/workspace/ai-erp/backend',
      script: 'venv/bin/uvicorn',
      args: 'app.main:app --host 0.0.0.0 --port 8000',
      interpreter: 'none',
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      env: {
        PYTHONPATH: '/home/ubuntu/.openclaw/workspace/ai-erp/backend'
      }
    },
    {
      name: 'kontali-frontend',
      cwd: '/home/ubuntu/.openclaw/workspace/ai-erp/frontend',
      script: 'npm',
      args: 'start',
      interpreter: 'none',
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      env: {
        PORT: 3000,
        NODE_ENV: 'production'
      }
    },
    {
      name: 'kontali-missionboard',
      cwd: '/home/ubuntu/.openclaw/workspace/ai-erp/roadmap',
      script: 'npm',
      args: 'start',
      interpreter: 'none',
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      env: {
        PORT: 3001,
        NODE_ENV: 'production'
      }
    }
  ]
};
