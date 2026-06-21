# Ecwid ↔ Shiprocket Integration Tool

A powerful standalone Python tool that automatically pulls orders from Ecwid e-commerce platform and mass uploads them to Shiprocket shipping management system.

## Features

- ✅ **Automated Order Sync**: Pull orders from Ecwid and push to Shiprocket automatically
- 📊 **Web Dashboard**: Beautiful, intuitive web UI for monitoring and management
- 🔄 **Batch Processing**: Mass upload multiple orders efficiently
- 💾 **Order Tracking**: SQLite database tracks all synced orders
- 🔁 **Retry Mechanism**: Automatically retry failed orders
- 🧪 **Connection Testing**: Test API connections before syncing
- 📝 **Detailed Logging**: Comprehensive logs for debugging and audit
- 🚀 **CLI & Web UI**: Use command-line or web interface
- ⚙️ **Flexible Configuration**: JSON config + environment variables
- 🔒 **Secure**: API credentials stored securely

## Requirements

- Python 3.8+
- pip (Python package manager)
- Ecwid API token and Store ID
- Shiprocket account credentials

## Installation

### 1. Clone/Download the Tool

```bash
cd ecwid_shiprocket_tool
```

### 2. Create Virtual Environment (Recommended)

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## Configuration

### Method 1: Configuration File (Recommended)

1. Copy the example config:
```bash
cp config.example.json config.json
```

2. Edit `config.json` with your credentials:
```json
{
  "ecwid_store_id": "123456",
  "ecwid_api_token": "your_ecwid_token",
  "shiprocket_email": "your-email@shiprocket.in",
  "shiprocket_password": "your_password",
  "shiprocket_pickup_location_id": 123456,
  "shiprocket_channel_id": 1,
  "default_package_length": 10,
  "default_package_breadth": 10,
  "default_package_height": 10,
  "default_package_weight": 0.5
}
```

### Method 2: Environment Variables

Create a `.env` file:
```
ECWID_STORE_ID=123456
ECWID_API_TOKEN=your_token
SHIPROCKET_EMAIL=your-email@shiprocket.in
SHIPROCKET_PASSWORD=your_password
SHIPROCKET_PICKUP_LOCATION_ID=123456
SHIPROCKET_CHANNEL_ID=1
```

## Getting API Credentials

### Ecwid API Token
1. Log in to Ecwid dashboard
2. Go to Settings → API tokens
3. Create a new API token with "Read orders" permission
4. Copy the token

### Ecwid Store ID
- Found in Ecwid dashboard URL: `https://app.ecwid.com/cp/123456/` (123456 is your Store ID)

### Shiprocket Credentials
1. Log in to Shiprocket dashboard
2. Use your registered email and password
3. Get your Pickup Location ID:
   - Settings → Pickup Locations
   - Note the location ID you want to use
4. Get your Channel ID:
   - Settings → Sales Channels
   - Channel ID for Ecwid/Manual orders is typically 1

## Usage

### Command Line Interface

#### 1. Sync Orders (Last 24 hours)
```bash
python main.py sync
```

#### 2. Sync with Custom Time Range
```bash
python main.py sync --hours 48
```

#### 3. Force Re-upload Already Synced Orders
```bash
python main.py sync --force
```

#### 4. Check Sync Status
```bash
python main.py status
```

#### 5. Retry Failed Orders
```bash
python main.py retry
```

#### 6. Start Web Dashboard
```bash
python main.py webui
```

Then open browser: `http://localhost:5000`

### Web Dashboard

Start the web UI:
```bash
python main.py webui --port 5000
```

Features:
- 📊 Real-time statistics dashboard
- 🚀 Start sync with custom hours
- 🔁 Retry failed orders
- 🧪 Test API connections
- 📝 View sync history
- 🔄 Auto-refresh status (every 30 seconds)

### Options

```
python main.py --help

Commands:
  sync       - Sync orders from Ecwid to Shiprocket
  status     - Check current sync status
  retry      - Retry failed orders
  webui      - Start web dashboard

Options:
  --hours    - Number of hours to look back (default: 24)
  --force    - Force re-upload already processed orders
  --config   - Path to config file (default: config.json)
  --port     - Web UI port (default: 5000)
```

## How It Works

### Order Sync Process

1. **Fetch**: Get orders from Ecwid API (newer than specified hours)
2. **Transform**: Convert Ecwid order format to Shiprocket format
3. **Check**: Verify order hasn't been processed before
4. **Upload**: Create order in Shiprocket via API
5. **Track**: Save order mapping in local database
6. **Retry**: Failed orders can be retried later

### Data Mapping

Ecwid → Shiprocket field mapping:
- Order ID → order_id
- Customer Name → billing/shipping_customer_name
- Email → billing/shipping_email
- Phone → billing/shipping_phone
- Address → billing/shipping_address
- City → billing/shipping_city
- State → billing/shipping_state
- Postal Code → billing/shipping_pincode
- Products → order_items
- Order Date → order_date
- Total Amount → sub_total

## Database

Orders are tracked in `orders.db` (SQLite):

**Tables:**
- `orders` - Order mapping and sync status
- `sync_logs` - History of all sync operations

**Order Status Values:**
- `pending` - Not yet processed
- `success` - Successfully uploaded
- `failed` - Upload failed, needs retry

## Logging

Logs are written to `integration.log` and console:
- INFO: Normal operations
- WARNING: Issues that don't prevent sync
- ERROR: Failures requiring attention

View logs:
```bash
tail -f integration.log
```

## Troubleshooting

### Connection Errors

**Issue**: "Ecwid API connection failed"
- Check API token is valid and hasn't expired
- Verify Store ID is correct
- Check network connectivity

**Solution**:
```bash
python main.py webui  # Use web UI to test connection
```

### Shiprocket Authentication Failed

**Issue**: "Shiprocket authentication failed"
- Verify email and password are correct
- Check Shiprocket account is active
- Ensure account has API access

### Orders Not Syncing

**Issue**: Orders fetch but don't upload
- Check Pickup Location ID is valid
- Verify Channel ID is correct
- Check order has complete shipping info
- Review `integration.log` for specific errors

### Duplicate Orders

**Issue**: Orders appear twice in Shiprocket
- Orders are tracked by Ecwid ID, shouldn't duplicate
- Check database isn't corrupted
- Try using `--force` flag cautiously

## Advanced Configuration

### Scheduled Syncing

#### Using Cron (Linux/Mac)
```bash
# Sync every 6 hours
0 */6 * * * cd /path/to/tool && python main.py sync >> sync.log 2>&1
```

#### Using Task Scheduler (Windows)
1. Create a batch file `sync.bat`:
```batch
@echo off
cd C:\path\to\tool
python main.py sync >> sync.log 2>&1
```
2. Add to Task Scheduler, run every 6 hours

#### Using Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt

CMD ["python", "main.py", "sync"]
```

```bash
docker build -t ecwid-shiprocket .
docker run -v $(pwd)/config.json:/app/config.json ecwid-shiprocket
```

### Custom Order Transformation

Edit `main.py` `_transform_order()` method to customize field mapping.

### Webhooks

Configure webhook URL in config to get notified of sync status:
```json
{
  "webhook_url": "https://your-server.com/webhook"
}
```

## Performance

- **Sync Speed**: ~10-20 orders/minute (depending on API limits)
- **Database**: SQLite handles 10,000+ orders efficiently
- **Memory**: ~50MB for typical operation
- **Web UI**: Lightweight Flask app, suitable for local use

## Limitations

- **Rate Limits**: Respects Ecwid and Shiprocket API rate limits
- **Order Status**: Only syncs new/unprocessed orders by default
- **Images**: Product images not automatically synced
- **Customization**: Custom fields need manual mapping

## Support & Troubleshooting

1. **Check Logs**: Always review `integration.log` first
2. **Test Connections**: Use web UI test button
3. **Verify Config**: Ensure all credentials are correct
4. **API Limits**: Check if rate limits reached

## File Structure

```
ecwid_shiprocket_tool/
├── main.py                 # Main application
├── ecwid_client.py        # Ecwid API wrapper
├── shiprocket_client.py   # Shiprocket API wrapper
├── config.py              # Configuration manager
├── database.py            # SQLite database layer
├── webui.py              # Flask web application
├── templates/
│   └── dashboard.html    # Web UI template
├── config.json           # Your configuration
├── config.example.json   # Example configuration
├── requirements.txt      # Python dependencies
├── integration.log       # Log file (auto-generated)
├── orders.db            # SQLite database (auto-generated)
└── README.md            # This file
```

## License

This tool is provided as-is for personal and commercial use.

## Contributing

For improvements or fixes, modify the source code as needed for your use case.

## API Documentation References

- [Ecwid REST API](https://developers.ecwid.com/api-documentation)
- [Shiprocket API](https://shiprocket.in/api-docs)

## Security Notes

- Never commit `config.json` with real credentials to git
- Use `.env` files for sensitive data
- Rotate API tokens regularly
- Use strong passwords for Shiprocket
- Keep logs secure (they contain order data)

---

**Last Updated**: 2024
**Version**: 1.0.0
