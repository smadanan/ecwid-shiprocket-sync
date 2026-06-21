"""
Web UI for Ecwid-Shiprocket Integration
Flask-based dashboard
"""

from flask import Flask, render_template, jsonify, request
import json
from datetime import datetime, timedelta
import logging
import os

logger = logging.getLogger(__name__)


def create_app(integrator):
    """Create Flask application"""
    app = Flask(__name__, static_folder='static', template_folder='templates')
    
    # Store integrator instance
    app.integrator = integrator
    
    @app.route('/')
    def index():
        """Dashboard page"""
        status = integrator.get_sync_status()
        return render_template('dashboard.html', status=status)
    
    @app.route('/api/status')
    def api_status():
        """Get current status"""
        status = integrator.get_sync_status()
        return jsonify(status)
    
    @app.route('/api/sync', methods=['POST'])
    def api_sync():
        """Start sync operation"""
        data = request.get_json()
        hours = data.get('hours', 24)
        force = data.get('force', False)
        
        try:
            result = integrator.sync_orders(hours=hours, force=force)
            return jsonify({'success': True, 'data': result})
        except Exception as e:
            logger.error(f"Sync error: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/retry', methods=['POST'])
    def api_retry():
        """Retry failed orders"""
        try:
            result = integrator.retry_failed_orders()
            return jsonify({'success': True, 'data': result})
        except Exception as e:
            logger.error(f"Retry error: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/test-connection', methods=['POST'])
    def api_test_connection():
        """Test API connections"""
        ecwid_ok = integrator.ecwid.test_connection()
        shiprocket_ok = integrator.shiprocket.test_connection()
        
        return jsonify({
            'ecwid': ecwid_ok,
            'shiprocket': shiprocket_ok,
            'all_ok': ecwid_ok and shiprocket_ok
        })
    
    return app


def run_app(integrator, port=5000):
    """Run Flask app with correct host binding"""
    app = create_app(integrator)
    
    # Bind to 0.0.0.0 for Render, localhost for local development
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    debug = os.getenv('FLASK_DEBUG', 'False') == 'True'
    
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    app.run(debug=True)
