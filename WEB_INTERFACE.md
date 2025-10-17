# Web Interface Guide

The LED Video Player includes a built-in web interface for remote control and management.

## Features

### 📊 Status Dashboard
- Real-time status monitoring
- Current mode (Day/Night)
- Playback status (Playing/Paused)
- Current image display
- Image count for both folders
- Interval settings

### 🎮 Playback Control
- **Play/Pause** - Toggle playback
- **Previous** - Go to previous image
- **Next** - Skip to next image
- **Day Mode** - Switch to day images
- **Night Mode** - Switch to night images

### ⚙️ Settings Management
- Adjust interval between images
- Enable/disable shuffle
- Change day/night folder paths
- Save configuration (requires restart for some changes)

### 🖼️ Image Management
- **View Images** - Browse images in day/night folders
- **Upload Images** - Drag and drop or click to upload
- **Delete Images** - Remove unwanted images
- Organized tabs for day and night images

## Access

### Local Access
When the application is running, access the web interface at:
```
http://localhost:5000
```

### Remote Access
From other devices on the same network:
```
http://YOUR_COMPUTER_IP:5000
```

To find your computer's IP address:
- **Windows**: `ipconfig` in Command Prompt
- **macOS**: `ifconfig` in Terminal
- **Linux**: `ip addr` in Terminal

### Access from Anywhere
If you want to access from outside your network:
1. Set up port forwarding on your router (forward port 5000)
2. Use your public IP address or set up dynamic DNS
3. Consider security implications (add authentication if needed)

## Installation

The web interface requires Flask. Install dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

The web server runs automatically when you start the application. Default settings:
- **Host**: `0.0.0.0` (accessible from all network interfaces)
- **Port**: `5000`

To change these settings, modify [main.py](main.py):

```python
web_server = WebServer(carousel_manager, config_manager, host='127.0.0.1', port=8080)
```

## Security Notes

⚠️ **Important**: The web interface has no authentication by default. Anyone who can access the URL can control the player.

For production use, consider:
- Restricting host to `127.0.0.1` for local-only access
- Using a firewall to limit network access
- Adding authentication middleware
- Using HTTPS with SSL certificates

## Troubleshooting

### Can't access from other devices
- Check firewall settings allow port 5000
- Verify devices are on the same network
- Try using the computer's IP address instead of localhost

### Upload fails
- Check folder permissions
- Ensure disk space is available
- Verify image format is supported (JPG, PNG, GIF, BMP)
- Check file size is under 50MB

### Changes not taking effect
- Some settings require application restart
- Try refreshing the browser page
- Check console/logs for errors

## API Endpoints

The web interface uses a REST API. You can also access it programmatically:

### Status
- `GET /api/status` - Get current player status

### Configuration
- `GET /api/config` - Get configuration
- `POST /api/config` - Update configuration

### Control
- `POST /api/control/pause` - Toggle pause
- `POST /api/control/next` - Next image
- `POST /api/control/previous` - Previous image
- `POST /api/control/mode` - Switch mode (body: `{"mode": "day"}`)

### Images
- `GET /api/images/<mode>` - List images (mode: day/night)
- `POST /api/images/<mode>/upload` - Upload image
- `DELETE /api/images/<mode>/<filename>` - Delete image
- `GET /api/images/<mode>/<filename>` - Get image file

## Example API Usage

### Using curl
```bash
# Get status
curl http://localhost:5000/api/status

# Toggle pause
curl -X POST http://localhost:5000/api/control/pause

# Switch to day mode
curl -X POST http://localhost:5000/api/control/mode \
  -H "Content-Type: application/json" \
  -d '{"mode": "day"}'

# Update interval
curl -X POST http://localhost:5000/api/config \
  -H "Content-Type: application/json" \
  -d '{"playback": {"interval_seconds": 10}}'
```

### Using Python
```python
import requests

# Get status
response = requests.get('http://localhost:5000/api/status')
print(response.json())

# Toggle pause
requests.post('http://localhost:5000/api/control/pause')

# Switch to night mode
requests.post('http://localhost:5000/api/control/mode',
              json={'mode': 'night'})
```
