"""
Enhanced Web UI for Ecwid-Shiprocket Integration
Shows real-time sync status, order details, and detailed error messages
"""

import os
import json
import logging
from flask import Flask, render_template, jsonify, request
from datetime import datetime
from scheduler import SyncScheduler

logger = logging.getLogger(__name__)


def run_app(integrator, port=5000):
    """Run the Flask web UI"""
    # Get the directory where this file is located
    base_dir = os.path.dirname(os.path.abspath(__file__))
    template_dir = os.path.join(base_dir, 'templates')
    
    # dashboard_enhanced.html is in templates/ folder
    app = Flask(__name__, template_folder=template_dir)
    
    # Store integration instance
    app.integrator = integrator
    
    # Initialize and start the automatic scheduler
    logger.info("🔄 Initializing automatic sync scheduler...")
    scheduler = SyncScheduler(integrator)
    app.scheduler = scheduler
    app.auto_sync_enabled = True
    app.auto_sync_interval = 6  # Default 6 hours
    
    # Start scheduler with default interval
    scheduler.schedule_interval_sync(hours=app.auto_sync_interval)
    logger.info(f"✅ Scheduler started - will sync every {app.auto_sync_interval} hours")
    
    # Track last sync time
    app.last_sync_time = None
    app.last_sync_status = None
    
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
            
            # Update last sync time and status
            app.last_sync_time = datetime.now()
            app.last_sync_status = result
            
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
    
    @app.route('/api/scheduler-status')
    def scheduler_status():
        """Get scheduler status"""
        try:
            jobs = app.scheduler.get_jobs()
            return jsonify({
                'success': True,
                'auto_sync_enabled': app.auto_sync_enabled,
                'auto_sync_interval': app.auto_sync_interval,
                'last_sync_time': app.last_sync_time.isoformat() if app.last_sync_time else None,
                'last_sync_status': app.last_sync_status,
                'jobs': [
                    {
                        'id': job.id,
                        'name': job.name,
                        'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None
                    }
                    for job in jobs
                ]
            })
        except Exception as e:
            logger.error(f"Error getting scheduler status: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e),
                'auto_sync_enabled': app.auto_sync_enabled
            }), 500
    
    @app.route('/api/scheduler/toggle', methods=['POST'])
    def toggle_scheduler():
        """Toggle auto-sync on/off"""
        try:
            enabled = request.json.get('enabled', True) if request.json else True
            
            if enabled:
                app.scheduler.resume()
                app.auto_sync_enabled = True
                logger.info(f"✅ Auto-sync ENABLED (every {app.auto_sync_interval} hours)")
                message = f"Auto-sync enabled (every {app.auto_sync_interval} hours)"
            else:
                app.scheduler.pause()
                app.auto_sync_enabled = False
                logger.info("⏸️ Auto-sync PAUSED")
                message = "Auto-sync disabled"
            
            return jsonify({
                'success': True,
                'enabled': app.auto_sync_enabled,
                'message': message
            })
        except Exception as e:
            logger.error(f"Error toggling scheduler: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/scheduler/interval', methods=['POST'])
    def set_scheduler_interval():
        """Set scheduler interval"""
        try:
            interval = request.json.get('interval', 6) if request.json else 6
            
            # Validate interval
            if interval < 1 or interval > 168:  # 1 hour to 7 days
                return jsonify({
                    'success': False,
                    'error': 'Interval must be between 1 and 168 hours'
                }), 400
            
            app.auto_sync_interval = interval
            
            # Reschedule with new interval
            app.scheduler.schedule_interval_sync(hours=interval)
            
            logger.info(f"✅ Auto-sync interval updated to {interval} hours")
            
            return jsonify({
                'success': True,
                'interval': app.auto_sync_interval,
                'message': f"Auto-sync interval set to {interval} hours"
            })
        except Exception as e:
            logger.error(f"Error setting interval: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
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
