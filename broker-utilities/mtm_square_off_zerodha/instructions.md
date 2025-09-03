# Zerodha Trading System - Complete Setup Instructions

## 📋 **Quick Start (TL;DR)**

1. **Setup files and dependencies**
2. **Update config.yaml with your API credentials**
3. **Run:** `python zerodha_runner.py`
4. **Done!** System handles everything automatically

---

## 🛠️ **Detailed Setup Instructions**

### **Step 1: Create Directory Structure**

```bash
# Create main directory
mkdir -p /home/ubuntu/utilities/zerodha_trading_system
cd /home/ubuntu/utilities/zerodha_trading_system

# Create access token directory
mkdir -p /home/ubuntu/utilities/kite_connect_data/tickjournal/key_files/
```

### **Step 2: Install Dependencies**

```bash
# Install required Python packages
pip install kiteconnect PyYAML pandas requests colorlog
```

### **Step 3: Create Required Files**

Copy these files to your trading directory:

```
zerodha_trading_system/
├── zerodha_runner.py          # Main runner script
├── zerodha_ltp_subscriber.py  # LTP WebSocket subscriber
├── zerodha_mtm_monitor.py     # MTM monitor & auto square-off
├── config.yaml               # Configuration file
└── requirements.txt          # Dependencies list
```

### **Step 4: Configure API Credentials**

#### **A. Update config.yaml**

```yaml
zerodha:
  api_key: "your_api_key_here"        # Replace with your API key
  api_secret: "your_api_secret_here"  # Replace with your API secret

trading:
  mtm_loss_threshold: -10000  # Adjust based on your risk tolerance
  monitor_interval: 5

websocket:
  position_check_interval: 5  # Check for new positions every 5 seconds

# Update instrument freeze quantities as needed
instruments:
  BANKNIFTY:
    volume_freeze_quantity: 900
  NIFTY:
    volume_freeze_quantity: 1800
  # Add more instruments based on your trading
```

#### **B. Add Access Token**

```bash
# Get your access token from Kite Connect dashboard
# Then save it to the token file:
echo "your_access_token_here" > /home/ubuntu/utilities/kite_connect_data/tickjournal/key_files/access_token.txt
```

### **Step 5: Verify Setup**

```bash
# Check if all prerequisites are met
python zerodha_runner.py check
```

**Expected output:**
```
Prerequisites Check:
  config_file: ✅ PASS
  ltp_script: ✅ PASS
  mtm_script: ✅ PASS
  access_token: ✅ PASS
  python_packages: ✅ PASS
```

---

## 🚀 **Usage Instructions**

### **Start the Trading System**

```bash
# Start the complete system (this is the ONLY command you need!)
python zerodha_runner.py
```

**What happens:**
1. ✅ Checks all prerequisites
2. ✅ Starts LTP Subscriber (WebSocket data feed)
3. ✅ Starts MTM Monitor (risk management)
4. ✅ Begins continuous monitoring
5. ✅ Auto-restarts any failed components

### **Monitor System Status**

```bash
# Check current system status
python zerodha_runner.py status
```

### **Stop the System**

```bash
# Method 1: Stop command
python zerodha_runner.py stop

# Method 2: Ctrl+C in the running terminal
# Press Ctrl+C in the terminal where system is running
```

---

## 📊 **System Monitoring**

### **Log Files Location**

```bash
# System runner logs
tail -f system_runner.log

# LTP subscriber logs  
tail -f ltp_subscriber.log

# MTM monitor logs
tail -f mtm_monitor.log
```

### **Database Files**

```bash
# LTP data (real-time prices)
zerodha_ltp.db

# Position tracking and MTM history
zerodha_positions.db
```

### **Key Metrics to Monitor**

1. **LTP Data Freshness**: Should be < 5 seconds old
2. **Position Count**: Should match your actual open positions
3. **MTM Values**: Current profit/loss vs threshold
4. **Process Health**: Both LTP and MTM processes running

---

## ⚡ **System Behavior**

### **Normal Operation Flow**

```
1. System starts → Checks prerequisites
2. LTP Subscriber → Connects to Zerodha WebSocket
3. Fetches positions → Subscribes to live price feeds
4. MTM Monitor → Calculates P&L every 5 seconds
5. Risk Management → Monitors threshold continuously
6. Auto Square-off → Triggers if loss threshold breached
```

### **Automatic Features**

- ✅ **Auto-subscription**: Subscribes to new positions within 5 seconds
- ✅ **Auto-unsubscription**: Removes closed positions within 5 seconds
- ✅ **Auto-restart**: Restarts crashed processes within 10 seconds
- ✅ **Auto-square-off**: Emergency exit when MTM threshold breached
- ✅ **Auto-recovery**: Handles network/API failures gracefully

### **Emergency Square-off Behavior**

**When MTM ≤ threshold:**
1. 🚨 **Alert logged**: "MTM THRESHOLD BREACHED!"
2. 🔄 **Square-off initiated**: All positions squared off with market orders
3. 📊 **Volume freeze handled**: Large orders split automatically
4. ✅ **Status reported**: Final MTM and remaining positions logged

---

## 🔧 **Configuration Options**

### **Risk Management Settings**

```yaml
trading:
  mtm_loss_threshold: -10000    # Loss limit in rupees
  monitor_interval: 5           # MTM calculation frequency (seconds)

risk_management:
  auto_square_off_enabled: true # Enable/disable auto square-off
```

### **Performance Tuning**

```yaml
websocket:
  position_check_interval: 5    # How often to check for new positions
  batch_size: 100              # LTP data batch size
  batch_timeout: 1.0           # Batch timeout in seconds

system_monitoring:
  health_check_interval: 10    # Process health check frequency
```

### **Instrument Configuration**

```yaml
instruments:
  BANKNIFTY:
    volume_freeze_quantity: 900
  NIFTY:
    volume_freeze_quantity: 1800
  FINNIFTY:
    volume_freeze_quantity: 1800
  MIDCPNIFTY:
    volume_freeze_quantity: 4200
  # Add more instruments as needed
```

---

## 🛡️ **Troubleshooting**

### **Common Issues & Solutions**

#### **1. "Access Token Invalid" Error**
```bash
# Solution: Update access token
echo "new_access_token" > /home/ubuntu/utilities/kite_connect_data/tickjournal/key_files/access_token.txt
# Restart system
```

#### **2. "Database is locked" Error**
```bash
# Solution: Ensure only one instance is running
pkill -f zerodha_runner
# Wait 5 seconds, then restart
python zerodha_runner.py
```

#### **3. WebSocket Connection Issues**
```bash
# Check logs for details
tail -f ltp_subscriber.log
# System will auto-reconnect, but you can restart if needed
```

#### **4. No LTP Data Received**
```bash
# Check if you have open positions
python zerodha_runner.py status
# Verify API credentials in config.yaml
# Check network connectivity
```

#### **5. MTM Calculations Wrong**
```bash
# Verify LTP data is fresh
tail -f mtm_monitor.log
# Check position data in database
# Restart system if needed
```

### **Emergency Procedures**

#### **If Auto Square-off Fails**
1. Check `mtm_monitor.log` for error details
2. Manually square-off positions via Kite web/app
3. Check order status in Kite
4. Restart system after manual intervention

#### **If System Becomes Unresponsive**
```bash
# Force stop all processes
pkill -f zerodha
# Wait 10 seconds
# Restart system
python zerodha_runner.py
```

---

## 📈 **Performance Expectations**

### **Response Times**
- **New position detection**: 5 seconds
- **MTM calculation**: 5 seconds  
- **LTP data updates**: Real-time (< 1 second)
- **Process failure recovery**: 10 seconds

### **Resource Usage**
- **CPU**: 5-10% on modern systems
- **Memory**: 50-100 MB
- **Network**: Minimal (WebSocket + periodic API calls)
- **Storage**: 10-50 MB for databases

### **API Call Frequency**
- **Position checks**: ~12 calls/minute (well within limits)
- **WebSocket**: Real-time (no REST API calls for LTP)
- **Rate limit safety**: 15x under Zerodha's limits

---

## 🔐 **Security Best Practices**

1. **Never commit credentials** to version control
2. **Regenerate access tokens** regularly
3. **Secure file permissions** on config files
4. **Monitor log files** for unauthorized access attempts
5. **Backup databases** regularly

---

## 📞 **Support & Maintenance**

### **Regular Maintenance**

```bash
# Weekly: Clean old log files
find . -name "*.log" -mtime +7 -delete

# Monthly: Backup databases
cp zerodha_*.db backups/

# As needed: Update access token
echo "new_token" > /path/to/access_token.txt
```

### **Monitoring Commands**

```bash
# Check system status
python zerodha_runner.py status

# Check log files
tail -f *.log

# Check database sizes
ls -lh *.db

# Check process health
ps aux | grep zerodha
```

---

## ✅ **Final Checklist**

Before going live:

- [ ] All files created and in correct locations
- [ ] Config.yaml updated with your API credentials  
- [ ] Access token file created and valid
- [ ] Prerequisites check passes
- [ ] Test run completed successfully
- [ ] Log files being generated
- [ ] Database files created
- [ ] MTM threshold set appropriately
- [ ] Volume freeze quantities configured for your instruments

**Once everything is ✅, simply run:**

```bash
python zerodha_runner.py
```

**Your Zerodha trading system is now live and managing your positions automatically!** 🚀