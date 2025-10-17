"""
Web server for remote control and configuration of the LED video player.
"""
import os
import logging
import threading
from pathlib import Path
from typing import Optional, Dict, Any
from flask import Flask, render_template, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename
import yaml

logger = logging.getLogger(__name__)


class WebServer:
    """Web server for remote control interface."""

    def __init__(self, carousel_manager, config_manager, ui_system=None, host='0.0.0.0', port=5000):
        """
        Initialize web server.

        Args:
            carousel_manager: CarouselManager instance
            config_manager: ConfigManager instance
            ui_system: UIIntegrationManager instance (optional, for control features)
            host: Host address to bind to (default: 0.0.0.0 for all interfaces)
            port: Port to listen on (default: 5000)
        """
        self.carousel_manager = carousel_manager
        self.config_manager = config_manager
        self.ui_system = ui_system
        self.host = host
        self.port = port
        self.app = Flask(__name__,
                        template_folder=str(Path(__file__).parent / 'templates'),
                        static_folder=str(Path(__file__).parent / 'static'))
        self.server_thread: Optional[threading.Thread] = None
        self.is_running = False

        # Configure upload settings
        self.app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
        self.app.config['UPLOAD_FOLDER'] = './images'

        self._setup_routes()

    def _setup_routes(self):
        """Set up Flask routes."""

        @self.app.route('/')
        def index():
            """Main page."""
            try:
                return render_template('index.html')
            except Exception as e:
                logger.error(f"Error rendering index: {e}")
                return f"Error: {e}", 500

        @self.app.route('/test')
        def test():
            """Test endpoint."""
            return "Web server is working!", 200

        @self.app.route('/api/status')
        def get_status():
            """Get current player status."""
            try:
                config = self.config_manager.config
                current_mode = self.carousel_manager.current_mode.value
                current_carousel = (self.carousel_manager.day_carousel
                                  if current_mode == "day"
                                  else self.carousel_manager.night_carousel)

                current_image = None
                if current_carousel.image_paths:
                    idx = current_carousel.current_index
                    if 0 <= idx < len(current_carousel.image_paths):
                        current_image = os.path.basename(current_carousel.image_paths[idx])

                # Get status from UI system if available
                is_paused = False
                if self.ui_system and self.ui_system.ui_controller:
                    ui_status = self.ui_system.ui_controller.get_status()
                    is_paused = ui_status.get('is_paused', False)
                    if ui_status.get('current_image_path'):
                        current_image = os.path.basename(ui_status['current_image_path'])

                # Check if playlists are active
                day_playlist_active = self.carousel_manager.day_carousel._has_playlist()
                night_playlist_active = self.carousel_manager.night_carousel._has_playlist()

                return jsonify({
                    'mode': current_mode,
                    'is_paused': is_paused,
                    'current_image': current_image,
                    'day_images_count': len(self.carousel_manager.day_carousel.image_paths),
                    'night_images_count': len(self.carousel_manager.night_carousel.image_paths),
                    'shuffle': config.playback.shuffle,
                    'interval': config.playback.interval_seconds,
                    'day_playlist_active': day_playlist_active,
                    'night_playlist_active': night_playlist_active
                })
            except Exception as e:
                logger.error(f"Error getting status: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/config')
        def get_config():
            """Get current configuration."""
            try:
                config = self.config_manager.config
                return jsonify({
                    'display': {
                        'monitor_index': config.display.monitor_index,
                        'always_on_top': config.display.always_on_top,
                        'background_color': config.display.background_color
                    },
                    'playback': {
                        'interval_seconds': config.playback.interval_seconds,
                        'shuffle': config.playback.shuffle,
                        'fit_mode': config.playback.fit_mode,
                        'transition_ms': config.playback.transition_ms
                    },
                    'folders': {
                        'day': config.folders.day,
                        'night': config.folders.night
                    },
                    'schedule': {
                        'mode': config.schedule.mode,
                        'fixed_schedule': {
                            'day_start': config.schedule.fixed_schedule.day_start,
                            'night_start': config.schedule.fixed_schedule.night_start
                        }
                    }
                })
            except Exception as e:
                logger.error(f"Error getting config: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/config', methods=['POST'])
        def update_config():
            """Update configuration."""
            try:
                data = request.json
                config_path = Path('config.yaml')

                # Load existing config
                if config_path.exists():
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config_data = yaml.safe_load(f) or {}
                else:
                    config_data = {}

                # Update with new values
                if 'playback' in data:
                    if 'playback' not in config_data:
                        config_data['playback'] = {}
                    config_data['playback'].update(data['playback'])

                if 'folders' in data:
                    if 'folders' not in config_data:
                        config_data['folders'] = {}
                    config_data['folders'].update(data['folders'])

                if 'schedule' in data:
                    if 'schedule' not in config_data:
                        config_data['schedule'] = {}
                    config_data['schedule'].update(data['schedule'])

                # Save config
                with open(config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)

                logger.info("Configuration updated via web interface")

                # Apply changes that can be updated without restart
                restart_needed = False
                updated_items = []

                # Update interval in real-time
                if 'playback' in data and 'interval_seconds' in data['playback']:
                    new_interval = data['playback']['interval_seconds']
                    self.config_manager.config.playback.interval_seconds = new_interval
                    updated_items.append(f"Interval changed to {new_interval}s")
                    logger.info(f"Applied interval change: {new_interval}s")

                # Update shuffle in real-time
                if 'playback' in data and 'shuffle' in data['playback']:
                    new_shuffle = data['playback']['shuffle']
                    self.config_manager.config.playback.shuffle = new_shuffle
                    self.carousel_manager.set_shuffle(new_shuffle)
                    updated_items.append(f"Shuffle {'enabled' if new_shuffle else 'disabled'}")
                    logger.info(f"Applied shuffle change: {new_shuffle}")

                # Folders require restart
                if 'folders' in data:
                    restart_needed = True
                    updated_items.append("Folder changes (restart required)")

                # Build response message
                if restart_needed:
                    message = "Settings saved! " + ", ".join(updated_items) + ". Restart required for folder changes."
                else:
                    message = "Settings applied immediately! " + ", ".join(updated_items) if updated_items else "Settings saved!"

                return jsonify({'success': True, 'message': message, 'restart_needed': restart_needed})

            except Exception as e:
                logger.error(f"Error updating config: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/control/pause', methods=['POST'])
        def pause():
            """Pause/unpause playback."""
            try:
                if not self.ui_system or not self.ui_system.ui_controller:
                    return jsonify({'error': 'UI system not available'}), 503

                self.ui_system.ui_controller.toggle_pause()
                status = self.ui_system.ui_controller.get_status()
                return jsonify({'success': True, 'is_paused': status['is_paused']})
            except Exception as e:
                logger.error(f"Error pausing: {e}", exc_info=True)
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/control/next', methods=['POST'])
        def next_image():
            """Skip to next image."""
            try:
                if not self.ui_system or not self.ui_system.ui_controller:
                    return jsonify({'error': 'UI system not available'}), 503

                # Call the private method directly since there's no public API
                self.ui_system.ui_controller._advance_to_next_image()
                return jsonify({'success': True})
            except Exception as e:
                logger.error(f"Error skipping to next: {e}", exc_info=True)
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/control/previous', methods=['POST'])
        def previous_image():
            """Go to previous image."""
            try:
                if not self.ui_system or not self.ui_system.ui_controller:
                    return jsonify({'error': 'UI system not available'}), 503

                # Call the private method directly since there's no public API
                self.ui_system.ui_controller._go_to_previous_image()
                return jsonify({'success': True})
            except Exception as e:
                logger.error(f"Error going to previous: {e}", exc_info=True)
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/control/mode', methods=['POST'])
        def switch_mode():
            """Switch between day/night mode."""
            try:
                if not self.ui_system or not self.ui_system.ui_controller:
                    return jsonify({'error': 'UI system not available'}), 503

                data = request.json
                mode = data.get('mode', 'day')

                from src.config.models import CarouselMode
                new_mode = CarouselMode.DAY if mode == 'day' else CarouselMode.NIGHT
                self.ui_system.ui_controller.switch_carousel_mode(new_mode)

                return jsonify({'success': True, 'mode': mode})
            except Exception as e:
                logger.error(f"Error switching mode: {e}", exc_info=True)
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/images/<mode>')
        def list_images(mode):
            """List images in day or night folder."""
            try:
                config = self.config_manager.config
                folder = config.folders.day if mode == 'day' else config.folders.night
                folder_path = Path(folder)

                if not folder_path.exists():
                    return jsonify({'images': []})

                images = []
                for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                    images.extend([f.name for f in folder_path.glob(f'*{ext}')])
                    images.extend([f.name for f in folder_path.glob(f'*{ext.upper()}')])

                # Check if custom order exists
                order_file = Path(f'./image_order_{mode}.json')
                if order_file.exists():
                    try:
                        with open(order_file, 'r') as f:
                            import json
                            order_data = json.load(f)
                            saved_order = order_data.get('order', [])

                            # Filter to only include files that still exist
                            ordered_images = [img for img in saved_order if img in images]

                            # Add any new images that aren't in the saved order
                            new_images = [img for img in images if img not in ordered_images]
                            new_images.sort()

                            images = ordered_images + new_images
                            logger.debug(f"Loaded custom order for {mode}: {len(ordered_images)} ordered, {len(new_images)} new")
                    except Exception as e:
                        logger.warning(f"Failed to load custom order for {mode}: {e}")
                        images.sort()
                else:
                    images.sort()

                return jsonify({'images': images})

            except Exception as e:
                logger.error(f"Error listing images: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/images/<mode>/upload', methods=['POST'])
        def upload_image(mode):
            """Upload an image to day or night folder."""
            try:
                if 'file' not in request.files:
                    return jsonify({'error': 'No file provided'}), 400

                file = request.files['file']
                if file.filename == '':
                    return jsonify({'error': 'No file selected'}), 400

                # Validate file extension
                allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}
                filename = secure_filename(file.filename)
                ext = Path(filename).suffix.lower()

                if ext not in allowed_extensions:
                    return jsonify({'error': 'Invalid file type'}), 400

                # Get target folder
                config = self.config_manager.config
                folder = config.folders.day if mode == 'day' else config.folders.night
                folder_path = Path(folder)
                folder_path.mkdir(parents=True, exist_ok=True)

                # Save file
                file_path = folder_path / filename
                file.save(str(file_path))

                logger.info(f"Image uploaded: {filename} to {mode} folder")
                return jsonify({'success': True, 'filename': filename})

            except Exception as e:
                logger.error(f"Error uploading image: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/images/<mode>/<filename>', methods=['DELETE'])
        def delete_image(mode, filename):
            """Delete an image from day or night folder."""
            try:
                # Security: ensure filename doesn't contain path traversal
                filename = secure_filename(filename)

                config = self.config_manager.config
                folder = config.folders.day if mode == 'day' else config.folders.night
                file_path = Path(folder) / filename

                if file_path.exists():
                    file_path.unlink()
                    logger.info(f"Image deleted: {filename} from {mode} folder")
                    return jsonify({'success': True})
                else:
                    return jsonify({'error': 'File not found'}), 404

            except Exception as e:
                logger.error(f"Error deleting image: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/images/<mode>/order', methods=['POST'])
        def save_image_order(mode):
            """Save custom image order for a mode."""
            try:
                data = request.json
                order = data.get('order', [])

                if not order:
                    return jsonify({'error': 'No order provided'}), 400

                # Save order to a JSON file
                order_file = Path(f'./image_order_{mode}.json')
                with open(order_file, 'w') as f:
                    import json
                    json.dump({'order': order, 'mode': mode}, f, indent=2)

                logger.info(f"Saved custom order for {mode} mode: {len(order)} images")

                # Reload images in carousel with new order
                if self.carousel_manager:
                    try:
                        # Reload the carousel to pick up new order
                        from src.images.image_manager import ImageManager
                        image_manager = ImageManager()
                        config = self.config_manager.config
                        folder = config.folders.day if mode == 'day' else config.folders.night

                        # Get carousel
                        carousel = (self.carousel_manager.day_carousel
                                  if mode == 'day'
                                  else self.carousel_manager.night_carousel)

                        # Update image paths with custom order
                        folder_path = Path(folder).resolve()
                        carousel.image_paths = [str(folder_path / filename) for filename in order
                                               if (folder_path / filename).exists()]

                        # Reset shuffle order to match custom order
                        carousel.shuffle_order = list(range(len(carousel.image_paths)))

                        logger.info(f"Applied custom order to {mode} carousel")
                    except Exception as e:
                        logger.warning(f"Failed to apply order to carousel: {e}")

                return jsonify({'success': True, 'count': len(order)})

            except Exception as e:
                logger.error(f"Error saving image order: {e}", exc_info=True)
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/playlist/<mode>', methods=['GET'])
        def get_playlist(mode):
            """Get playlist for a mode."""
            try:
                playlist_file = Path(f'./playlist_{mode}.json')
                if playlist_file.exists():
                    with open(playlist_file, 'r') as f:
                        import json
                        data = json.load(f)
                        return jsonify(data)
                else:
                    return jsonify({'playlist': []})
            except Exception as e:
                logger.error(f"Error getting playlist: {e}", exc_info=True)
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/playlist/<mode>', methods=['POST'])
        def save_playlist_endpoint(mode):
            """Save playlist for a mode."""
            try:
                data = request.json
                playlist = data.get('playlist', [])

                if not isinstance(playlist, list):
                    return jsonify({'error': 'Invalid playlist format'}), 400

                # Save playlist to JSON file
                playlist_file = Path(f'./playlist_{mode}.json')
                with open(playlist_file, 'w') as f:
                    import json
                    json.dump({'playlist': playlist, 'mode': mode}, f, indent=2)

                logger.info(f"Saved playlist for {mode}: {len(playlist)} items")

                # Apply playlist to carousel
                if self.carousel_manager:
                    try:
                        config = self.config_manager.config
                        folder = config.folders.day if mode == 'day' else config.folders.night
                        folder_path = Path(folder).resolve()

                        # Get carousel
                        carousel = (self.carousel_manager.day_carousel
                                  if mode == 'day'
                                  else self.carousel_manager.night_carousel)

                        # Build full paths for playlist items
                        carousel.image_paths = [str(folder_path / filename) for filename in playlist
                                               if (folder_path / filename).exists()]

                        # Reset shuffle order to sequential for playlist
                        carousel.shuffle_order = list(range(len(carousel.image_paths)))
                        carousel.current_index = 0

                        logger.info(f"Applied playlist to {mode} carousel: {len(carousel.image_paths)} items")
                    except Exception as e:
                        logger.warning(f"Failed to apply playlist to carousel: {e}")

                return jsonify({'success': True, 'count': len(playlist)})

            except Exception as e:
                logger.error(f"Error saving playlist: {e}", exc_info=True)
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/images/<mode>/<filename>')
        def get_image(mode, filename):
            """Get an image file."""
            try:
                filename = secure_filename(filename)
                config = self.config_manager.config
                folder = config.folders.day if mode == 'day' else config.folders.night

                # Convert to absolute path
                from pathlib import Path
                folder_path = Path(folder).resolve()

                logger.debug(f"Serving image: {filename} from {folder_path}")
                return send_from_directory(str(folder_path), filename)
            except Exception as e:
                logger.error(f"Error getting image: {e}", exc_info=True)
                return jsonify({'error': str(e)}), 500

    def start(self):
        """Start the web server in a background thread."""
        if self.is_running:
            logger.warning("Web server is already running")
            return

        def run_server():
            try:
                logger.info(f"Starting web server on {self.host}:{self.port}")
                # Disable Flask werkzeug logger spam
                import logging as flask_logging
                flask_log = flask_logging.getLogger('werkzeug')
                flask_log.setLevel(flask_logging.ERROR)

                self.app.run(host=self.host, port=self.port, debug=False, use_reloader=False, threaded=True)
            except Exception as e:
                logger.error(f"Web server error: {e}", exc_info=True)

        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        self.is_running = True

        # Give server time to start
        import time
        time.sleep(0.5)

        actual_host = "localhost" if self.host == "0.0.0.0" else self.host
        logger.info(f"Web interface available at http://{actual_host}:{self.port}")
        print(f"\n🌐 Web Interface: http://{actual_host}:{self.port}\n")

    def stop(self):
        """Stop the web server."""
        if not self.is_running:
            return

        # Flask doesn't provide a clean shutdown mechanism when running in a thread
        # The daemon thread will be terminated when the main program exits
        self.is_running = False
        logger.info("Web server shutdown initiated")
