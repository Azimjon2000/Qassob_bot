# Server Optimization Guide (Oracle E2 Micro 1GB RAM)

## 1. Create 1GB Swap
To prevent OOM (Out Of Memory) kills on a 1GB RAM server, creating a swap file is mandatory.

```bash
# 1. Create a 1GB file for swap
sudo fallocate -l 1G /swapfile

# 2. Set correct permissions
sudo chmod 600 /swapfile

# 3. Set up the swap area
sudo mkswap /swapfile

# 4. Enable the swap
sudo swapon /swapfile

# 5. Make the swap permanent (persist after reboot)
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# 6. Verify
free -h
```

## 2. Systemd Service Configuration
Create a service file at `/etc/systemd/system/barberbot.service`:

```ini
[Unit]
Description=Telegram Barber Bot (Aiogram 3 + SQLite)
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/SARTAROSHXONALAR
# Use the absolute path to your virtualenv python
ExecStart=/home/ubuntu/SARTAROSHXONALAR/.venv/bin/python -m app.main
Restart=always
RestartSec=2
KillSignal=SIGINT
TimeoutStopSec=30
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Commands to manage the service:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable barberbot
sudo systemctl start barberbot
sudo systemctl status barberbot
# View logs:
journalctl -u barberbot -f
```
