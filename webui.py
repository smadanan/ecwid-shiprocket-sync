"""
Enhanced Web UI for Ecwid-Shiprocket Integration
Shows real-time sync status, order details, and detailed error messages
"""

import os
import json
import logging
from flask import Flask, render_template, jsonify, request
from datetime import datetime

logger = logging.getLogger(__name__)


def run_app(integrator, port=5000):
    """Run the Flask web UI"""
    app = Flask(__name__, template_folder='templates')
    
    # Store integration instance
    app.integrator = integrator
    
    @app.route('/')
    def index():
        """Main dashboard page"""
        return render_template('dashboard_enhanced.html')
    
    @app.route('/api/status')
    def get_status():
        """Get current sync status"""
        try:
            status = app.integrator.get_sync_status()
            return jsonify({
                'success': True,
                'data': status,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Error getting status: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500
    
    @app.route('/api/test-connection', methods=['POST'])
    def test_connection():
        """Test both Ecwid and Shiprocket connections"""
        try:
            results = {
                'ecwid': False,
                'shiprocket': False,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info("Testing Ecwid connection...")
            results['ecwid'] = app.integrator.ecwid.test_connection()
            
            logger.info("Testing Shiprocket connection...")
            results['shiprocket'] = app.integrator.shiprocket.test_connection()
            
            return jsonify({
                'success': True,
                'data': results
            })
        except Exception as e:
            logger.error(f"Error testing connection: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e),
                'data': {
                    'ecwid': False,
                    'shiprocket': False
                }
            }), 500
    
    @app.route('/api/sync', methods=['POST'])
    def sync_orders():
        """Start manual sync"""
        try:
            logger.info("Manual sync initiated from UI")
            hours = request.json.get('hours', 24) if request.json else 24
            force = request.json.get('force', False) if request.json else False
            
            result = app.integrator.sync_orders(hours=hours, force=force)
            
            # Format response with details
            response_data = {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'summary': {
                    'fetched': result.get('fetched', 0),
                    'uploaded': result.get('uploaded', 0),
                    'failed': result.get('failed', 0),
                    'skipped': result.get('skipped', 0)
                },
                'errors': result.get('errors', [])
            }
            
            logger.info(f"Sync completed: {json.dumps(response_data['summary'])}")
            return jsonify(response_data)
            
        except Exception as e:
            logger.error(f"Error during sync: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'summary': {
                    'fetched': 0,
                    'uploaded': 0,
                    'failed': 0,
                    'skipped': 0
                }
            }), 500
    
    @app.route('/api/retry', methods=['POST'])
    def retry_failed():
        """Retry failed orders"""
        try:
            logger.info("Retry failed orders initiated from UI")
            result = app.integrator.retry_failed_orders()
            
            return jsonify({
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'data': {
                    'retried': result.get('retried', 0),
                    'fixed': result.get('fixed', 0),
                    'still_failed': result.get('still_failed', 0)
                }
            })
        except Exception as e:
            logger.error(f"Error during retry: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500
    
    @app.route('/api/logs', methods=['GET'])
    def get_logs():
        """Get recent logs from integration.log"""
        try:
            lines = request.args.get('lines', 50, type=int)
            
            if not os.path.exists('integration.log'):
                return jsonify({
                    'success': True,
                    'logs': []
                })
            
            with open('integration.log', 'r') as f:
                all_lines = f.readlines()
            
            # Get last N lines
            recent_lines = all_lines[-lines:]
            
            # Parse logs
            logs = []
            for line in recent_lines:
                try:
                    # Parse log format: TIMESTAMP - LOGGER - LEVEL - MESSAGE
                    parts = line.split(' - ', 3)
                    if len(parts) >= 4:
                        timestamp = parts[0]
                        logger_name = parts[1]
                        level = parts[2]
                        message = parts[3].strip()
                        
                        # Determine severity
                        severity = 'info'
                        if 'ERROR' in level or '❌' in message:
                            severity = 'error'
                        elif 'WARNING' in level or '⚠️' in message:
                            severity = 'warning'
                        elif 'SUCCESS' in level or '✅' in message:
                            severity = 'success'
                        
                        logs.append({
                            'timestamp': timestamp,
                            'logger': logger_name,
                            'level': level,
                            'message': message,
                            'severity': severity
                        })
                except:
                    # If parsing fails, just add raw line
                    logs.append({
                        'timestamp': '',
                        'logger': 'Unknown',
                        'level': 'INFO',
                        'message': line.strip(),
                        'severity': 'info'
                    })
            
            return jsonify({
                'success': True,
                'logs': logs
            })
        except Exception as e:
            logger.error(f"Error getting logs: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e),
                'logs': []
            }), 500
    
    # Health check
    @app.route('/health')
    def health():
        return jsonify({'status': 'ok'})
    
    logger.info(f"Starting Flask app on port {port}")
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    app.run(host=host, port=port, debug=False)


if __name__ == '__main__':
    run_app(port=5000)
