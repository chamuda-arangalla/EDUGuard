"""
Reports API Module

This module provides API endpoints for generating reports and retrieving historical data
for all monitoring types in the EDUGuard application.
"""

import logging
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from utils.database import DatabaseManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('reports-api')

# Create a blueprint for reports API
reports_bp = Blueprint('reports_api', __name__, url_prefix='/api/reports')

def get_user_id_from_request():
    """Get the user ID from the request headers or parameters"""
    # Try to get from query params first
    user_id = request.args.get('userId')
    if user_id:
        logger.debug(f"Using user ID from query params: {user_id}")
        return user_id
    
    # Try to get from headers
    user_id = request.headers.get('X-User-ID') or request.headers.get('X-User-Id') or request.headers.get('x-user-id')
    if user_id:
        logger.debug(f"Using user ID from header: {user_id}")
        return user_id
    
    logger.warning("No user ID found in request")
    return None

def parse_date_param(date_str=None):
    """Parse a date string parameter"""
    if not date_str:
        return datetime.now().date()
    
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        logger.warning(f"Invalid date format: {date_str}. Using current date.")
        return datetime.now().date()

def get_date_range(timeframe, reference_date):
    """Get start and end dates based on timeframe and reference date"""
    end_date = reference_date
    
    if timeframe == 'daily':
        start_date = reference_date
    elif timeframe == 'weekly':
        # Start from the beginning of the week (Monday)
        weekday = reference_date.weekday()
        start_date = reference_date - timedelta(days=weekday)
    elif timeframe == 'monthly':
        # Start from the first day of the month
        start_date = reference_date.replace(day=1)
    else:
        # Default to daily
        start_date = reference_date
    
    return start_date, end_date

@reports_bp.route('/posture', methods=['GET'])
def get_posture_history():
    """Get historical posture monitoring data"""
    user_id = get_user_id_from_request()
    if not user_id:
        return jsonify({
            'status': 'error',
            'message': 'User ID is required'
        }), 400

    # Get query parameters
    timeframe = request.args.get('timeframe', 'daily')
    date_str = request.args.get('date')
    reference_date = parse_date_param(date_str)
    
    # Get date range based on timeframe
    start_date, end_date = get_date_range(timeframe, reference_date)
    
    try:
        # Initialize database manager
        db_manager = DatabaseManager(user_id)
        
        # Retrieve posture data for the date range
        posture_data = db_manager.get_posture_data_range(start_date, end_date)
        
        # Process data for visualization
        processed_data = process_posture_data(posture_data, timeframe, start_date, end_date)
        
        return jsonify({
            'status': 'success',
            'data': processed_data,
            'timeframe': timeframe,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error retrieving posture history: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to retrieve posture history: {str(e)}'
        }), 500

@reports_bp.route('/stress', methods=['GET'])
def get_stress_history():
    """Get historical stress monitoring data"""
    user_id = get_user_id_from_request()
    if not user_id:
        return jsonify({
            'status': 'error',
            'message': 'User ID is required'
        }), 400

    # Get query parameters
    timeframe = request.args.get('timeframe', 'daily')
    date_str = request.args.get('date')
    reference_date = parse_date_param(date_str)
    
    # Get date range based on timeframe
    start_date, end_date = get_date_range(timeframe, reference_date)
    
    try:
        # Initialize database manager
        db_manager = DatabaseManager(user_id)
        
        # Retrieve stress data for the date range
        stress_data = db_manager.get_stress_data_range(start_date, end_date)
        
        # Process data for visualization
        processed_data = process_stress_data(stress_data, timeframe, start_date, end_date)
        
        return jsonify({
            'status': 'success',
            'data': processed_data,
            'timeframe': timeframe,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error retrieving stress history: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to retrieve stress history: {str(e)}'
        }), 500

@reports_bp.route('/cvs', methods=['GET'])
def get_cvs_history():
    """Get historical CVS (eye strain) monitoring data"""
    user_id = get_user_id_from_request()
    if not user_id:
        return jsonify({
            'status': 'error',
            'message': 'User ID is required'
        }), 400

    # Get query parameters
    timeframe = request.args.get('timeframe', 'daily')
    date_str = request.args.get('date')
    reference_date = parse_date_param(date_str)
    
    # Get date range based on timeframe
    start_date, end_date = get_date_range(timeframe, reference_date)
    
    try:
        # Initialize database manager
        db_manager = DatabaseManager(user_id)
        
        # Retrieve CVS data for the date range
        cvs_data = db_manager.get_cvs_data_range(start_date, end_date)
        
        # Process data for visualization
        processed_data = process_cvs_data(cvs_data, timeframe, start_date, end_date)
        
        return jsonify({
            'status': 'success',
            'data': processed_data,
            'timeframe': timeframe,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error retrieving CVS history: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to retrieve CVS history: {str(e)}'
        }), 500

@reports_bp.route('/hydration', methods=['GET'])
def get_hydration_history():
    """Get historical hydration monitoring data"""
    user_id = get_user_id_from_request()
    if not user_id:
        return jsonify({
            'status': 'error',
            'message': 'User ID is required'
        }), 400

    # Get query parameters
    timeframe = request.args.get('timeframe', 'daily')
    date_str = request.args.get('date')
    reference_date = parse_date_param(date_str)
    
    # Get date range based on timeframe
    start_date, end_date = get_date_range(timeframe, reference_date)
    
    try:
        # Initialize database manager
        db_manager = DatabaseManager(user_id)
        
        # Retrieve hydration data for the date range
        hydration_data = db_manager.get_hydration_data_range(start_date, end_date)
        
        # Process data for visualization
        processed_data = process_hydration_data(hydration_data, timeframe, start_date, end_date)
        
        return jsonify({
            'status': 'success',
            'data': processed_data,
            'timeframe': timeframe,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error retrieving hydration history: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to retrieve hydration history: {str(e)}'
        }), 500

@reports_bp.route('/summary', methods=['GET'])
def get_summary_data():
    """Get summary data across all monitoring types"""
    user_id = get_user_id_from_request()
    if not user_id:
        return jsonify({
            'status': 'error',
            'message': 'User ID is required'
        }), 400

    # Get query parameters
    timeframe = request.args.get('timeframe', 'daily')
    date_str = request.args.get('date')
    reference_date = parse_date_param(date_str)
    
    # Get date range based on timeframe
    start_date, end_date = get_date_range(timeframe, reference_date)
    
    try:
        # Initialize database manager
        db_manager = DatabaseManager(user_id)
        
        # Get summary data for all monitoring types
        summary = {
            'posture': get_posture_summary(db_manager, start_date, end_date),
            'stress': get_stress_summary(db_manager, start_date, end_date),
            'cvs': get_cvs_summary(db_manager, start_date, end_date),
            'hydration': get_hydration_summary(db_manager, start_date, end_date)
        }
        
        # Add overall health score
        summary['overall_health_score'] = calculate_overall_health_score(summary)
        
        return jsonify({
            'status': 'success',
            'data': summary,
            'timeframe': timeframe,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error retrieving summary data: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to retrieve summary data: {str(e)}'
        }), 500

# Helper functions for data processing

def process_posture_data(data, timeframe, start_date=None, end_date=None):
    """Process posture data for visualization"""
    # Return empty structure if no data is available
    if not data:
        return {
            'labels': [],
            'good_posture_percentage': [],
            'bad_posture_percentage': []
        }
    
    # Process actual data
    result = {
        'labels': [],
        'good_posture_percentage': [],
        'bad_posture_percentage': []
    }
    
    # Sort data by timestamp to ensure chronological order
    data.sort(key=lambda x: x.get('timestamp', 0))
    
    # Generate formatted labels and extract data
    for entry in data:
        timestamp = entry.get('timestamp', 0)
        date = datetime.fromtimestamp(timestamp / 1000)
        
        # Format label based on timeframe
        if timeframe == 'daily':
            label = date.strftime('%H:%M')
        elif timeframe == 'weekly':
            label = date.strftime('%a')  # Day abbreviation (Mon, Tue, etc.)
        else:  # monthly
            label = date.strftime('%d %b')  # Day with month abbreviation
        
        # Add data to result
        result['labels'].append(label)
        result['good_posture_percentage'].append(round(entry.get('good_posture_percentage', 0), 1))
        result['bad_posture_percentage'].append(round(entry.get('bad_posture_percentage', 0), 1))
    
    # If we have no data but timeframe is specified, generate empty labels
    if not result['labels'] and start_date and end_date:
        result['labels'] = generate_time_labels(timeframe, start_date, end_date)
        result['good_posture_percentage'] = [0] * len(result['labels'])
        result['bad_posture_percentage'] = [0] * len(result['labels'])
    
    return result

def process_stress_data(data, timeframe, start_date=None, end_date=None):
    """Process stress data for visualization"""
    # Return empty structure if no data is available
    if not data:
        logger.warning(f"No stress data available for {timeframe} view, generating empty structure")
        result = {
            'labels': [],
            'low_stress_percentage': [],
            'medium_stress_percentage': [],
            'high_stress_percentage': []
        }
        
        # If we have timeframe info, generate appropriate empty labels
        if start_date and end_date:
            result['labels'] = generate_time_labels(timeframe, start_date, end_date)
            result['low_stress_percentage'] = [0] * len(result['labels'])
            result['medium_stress_percentage'] = [0] * len(result['labels'])
            result['high_stress_percentage'] = [0] * len(result['labels'])
        
        return result
    
    # Process actual data
    logger.info(f"Processing {len(data)} stress data points for {timeframe} view")
    result = {
        'labels': [],
        'low_stress_percentage': [],
        'medium_stress_percentage': [],
        'high_stress_percentage': []
    }
    
    # Sort data by timestamp to ensure chronological order
    data.sort(key=lambda x: x.get('timestamp', 0))
    
    # Generate formatted labels and extract data
    for entry in data:
        timestamp = entry.get('timestamp', 0)
        date = datetime.fromtimestamp(timestamp / 1000)
        
        # Format label based on timeframe
        if timeframe == 'daily':
            label = date.strftime('%H:%M')
        elif timeframe == 'weekly':
            label = date.strftime('%a')  # Day abbreviation (Mon, Tue, etc.)
        else:  # monthly
            label = date.strftime('%d %b')  # Day with month abbreviation
        
        # Add data to result
        result['labels'].append(label)
        result['low_stress_percentage'].append(round(entry.get('low_stress_percentage', 0), 1))
        result['medium_stress_percentage'].append(round(entry.get('medium_stress_percentage', 0), 1))
        result['high_stress_percentage'].append(round(entry.get('high_stress_percentage', 0), 1))
    
    # If we have no data but timeframe is specified, generate empty labels
    if not result['labels'] and start_date and end_date:
        result['labels'] = generate_time_labels(timeframe, start_date, end_date)
        result['low_stress_percentage'] = [0] * len(result['labels'])
        result['medium_stress_percentage'] = [0] * len(result['labels'])
        result['high_stress_percentage'] = [0] * len(result['labels'])
    
    logger.info(f"Processed stress data with {len(result['labels'])} data points")
    return result

def process_cvs_data(data, timeframe, start_date=None, end_date=None):
    """Process CVS (eye strain) data for visualization"""
    # Return empty structure if no data is available
    if not data:
        return {
            'labels': [],
            'normal_blink_percentage': [],
            'low_blink_percentage': [],
            'high_blink_percentage': [],
            'avg_blink_count': []
        }
    
    # Process actual data
    result = {
        'labels': [],
        'normal_blink_percentage': [],
        'low_blink_percentage': [],
        'high_blink_percentage': [],
        'avg_blink_count': []
    }
    
    # Sort data by timestamp to ensure chronological order
    data.sort(key=lambda x: x.get('timestamp', 0))
    
    # Generate formatted labels and extract data
    for entry in data:
        timestamp = entry.get('timestamp', 0)
        date = datetime.fromtimestamp(timestamp / 1000)
        
        # Format label based on timeframe
        if timeframe == 'daily':
            label = date.strftime('%H:%M')
        elif timeframe == 'weekly':
            label = date.strftime('%a')  # Day abbreviation (Mon, Tue, etc.)
        else:  # monthly
            label = date.strftime('%d %b')  # Day with month abbreviation
        
        # Add data to result
        result['labels'].append(label)
        result['normal_blink_percentage'].append(round(entry.get('normal_blink_percentage', 0), 1))
        result['low_blink_percentage'].append(round(entry.get('low_blink_percentage', 0), 1))
        result['high_blink_percentage'].append(round(entry.get('high_blink_percentage', 0), 1))
        result['avg_blink_count'].append(round(entry.get('avg_blink_count', 0), 1))
    
    # If we have no data but timeframe is specified, generate empty labels
    if not result['labels'] and start_date and end_date:
        result['labels'] = generate_time_labels(timeframe, start_date, end_date)
        result['normal_blink_percentage'] = [0] * len(result['labels'])
        result['low_blink_percentage'] = [0] * len(result['labels'])
        result['high_blink_percentage'] = [0] * len(result['labels'])
        result['avg_blink_count'] = [0] * len(result['labels'])
    
    return result

def process_hydration_data(data, timeframe, start_date=None, end_date=None):
    """Process hydration data for visualization"""
    # Return empty structure if no data is available
    if not data:
        logger.warning(f"No hydration data available for {timeframe} view, generating empty structure")
        result = {
            'labels': [],
            'normal_lips_percentage': [],
            'dry_lips_percentage': [],
            'avg_dryness_score': []
        }
        
        # If we have timeframe info, generate appropriate empty labels
        if start_date and end_date:
            result['labels'] = generate_time_labels(timeframe, start_date, end_date)
            result['normal_lips_percentage'] = [0] * len(result['labels'])
            result['dry_lips_percentage'] = [0] * len(result['labels'])
            result['avg_dryness_score'] = [0] * len(result['labels'])
        
        return result
    
    # Process actual data
    logger.info(f"Processing {len(data)} hydration data points for {timeframe} view")
    result = {
        'labels': [],
        'normal_lips_percentage': [],
        'dry_lips_percentage': [],
        'avg_dryness_score': []
    }
    
    # Sort data by timestamp to ensure chronological order
    data.sort(key=lambda x: x.get('timestamp', 0))
    
    # Check if we have fallback data
    has_fallback_data = any(entry.get('is_fallback', False) for entry in data)
    has_sample_data = any(entry.get('is_sample', False) for entry in data)
    
    # Generate formatted labels and extract data
    for entry in data:
        timestamp = entry.get('timestamp', 0)
        date = datetime.fromtimestamp(timestamp / 1000)
        
        # Format label based on timeframe
        if timeframe == 'daily':
            label = date.strftime('%H:%M')
        elif timeframe == 'weekly':
            label = date.strftime('%a')  # Day abbreviation (Mon, Tue, etc.)
        else:  # monthly
            label = date.strftime('%d %b')  # Day with month abbreviation
        
        # Add data to result, ensuring we have values
        normal_percentage = entry.get('normal_lips_percentage', 0)
        dry_percentage = entry.get('dry_lips_percentage', 0)
        dryness_score = entry.get('avg_dryness_score', 0)
        
        # Ensure percentages add up to 100%
        total = normal_percentage + dry_percentage
        if total > 0 and total != 100:
            factor = 100 / total
            normal_percentage *= factor
            dry_percentage *= factor
        
        result['labels'].append(label)
        result['normal_lips_percentage'].append(round(normal_percentage, 1))
        result['dry_lips_percentage'].append(round(dry_percentage, 1))
        result['avg_dryness_score'].append(round(dryness_score, 2))
    
    # If we have no data but timeframe is specified, generate empty labels
    if not result['labels'] and start_date and end_date:
        result['labels'] = generate_time_labels(timeframe, start_date, end_date)
        result['normal_lips_percentage'] = [0] * len(result['labels'])
        result['dry_lips_percentage'] = [0] * len(result['labels'])
        result['avg_dryness_score'] = [0] * len(result['labels'])
    
    logger.info(f"Processed hydration data with {len(result['labels'])} data points")
    
    return result

def generate_time_labels(timeframe, start_date, end_date):
    """Generate time labels for a given timeframe and date range."""
    labels = []
    
    if timeframe == 'daily':
        # Generate hourly labels (9 AM to 5 PM)
        for hour in range(9, 18):
            labels.append(f"{hour:02d}:00")
    elif timeframe == 'weekly':
        # Generate day labels (Mon to Sun)
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        current = start_date
        while current <= end_date and len(labels) < 7:
            labels.append(days[current.weekday()])
            current += timedelta(days=1)
        
        # If we don't have enough days in the range, fill with remaining days
        if len(labels) < 7:
            current_day_index = days.index(labels[-1]) if labels else start_date.weekday()
            while len(labels) < 7:
                current_day_index = (current_day_index + 1) % 7
                labels.append(days[current_day_index])
    else:  # monthly
        # Generate day labels (1 to 30/31)
        current = start_date
        while current <= end_date:
            labels.append(current.strftime('%d %b'))
            current += timedelta(days=1)
    
    logger.info(f"Generated {len(labels)} time labels for {timeframe} view from {start_date} to {end_date}")
    return labels

# Summary data functions

def get_posture_summary(db_manager, start_date, end_date):
    """Get summary of posture data for a date range"""
    # Get actual data from the database
    posture_data = db_manager.get_posture_data_range(start_date, end_date)
    
    if not posture_data:
        return {
            'good_posture_percentage': 0,
            'bad_posture_percentage': 0,
            'alert_count': 0,
            'monitoring_duration': 0
        }
    
    # Calculate average percentages
    good_percentage = sum(entry.get('good_posture_percentage', 0) for entry in posture_data) / len(posture_data)
    bad_percentage = sum(entry.get('bad_posture_percentage', 0) for entry in posture_data) / len(posture_data)
    
    # Get alert count from the database
    alerts = db_manager.get_recent_alerts(100)  # Get a reasonable number of alerts
    posture_alerts = [alert for alert in alerts if alert.get('type') == 'posture']
    
    # Estimate monitoring duration (10 minutes per data point is a reasonable guess)
    monitoring_duration = len(posture_data) * 10
    
    return {
        'good_posture_percentage': round(good_percentage, 1),
        'bad_posture_percentage': round(bad_percentage, 1),
        'alert_count': len(posture_alerts),
        'monitoring_duration': monitoring_duration
    }

def get_stress_summary(db_manager, start_date, end_date):
    """Get summary of stress data for a date range"""
    # Get actual data from the database
    stress_data = db_manager.get_stress_data_range(start_date, end_date)
    
    if not stress_data:
        return {
            'low_stress_percentage': 0,
            'medium_stress_percentage': 0,
            'high_stress_percentage': 0,
            'alert_count': 0,
            'monitoring_duration': 0
        }
    
    # Calculate average percentages
    low_percentage = sum(entry.get('low_stress_percentage', 0) for entry in stress_data) / len(stress_data)
    medium_percentage = sum(entry.get('medium_stress_percentage', 0) for entry in stress_data) / len(stress_data)
    high_percentage = sum(entry.get('high_stress_percentage', 0) for entry in stress_data) / len(stress_data)
    
    # Get alert count from the database
    alerts = db_manager.get_recent_alerts(100)  # Get a reasonable number of alerts
    stress_alerts = [alert for alert in alerts if alert.get('type') == 'stress']
    
    # Estimate monitoring duration (10 minutes per data point is a reasonable guess)
    monitoring_duration = len(stress_data) * 10
    
    return {
        'low_stress_percentage': round(low_percentage, 1),
        'medium_stress_percentage': round(medium_percentage, 1),
        'high_stress_percentage': round(high_percentage, 1),
        'alert_count': len(stress_alerts),
        'monitoring_duration': monitoring_duration
    }

def get_cvs_summary(db_manager, start_date, end_date):
    """Get summary of CVS (eye strain) data for a date range"""
    # Get actual data from the database
    cvs_data = db_manager.get_cvs_data_range(start_date, end_date)
    
    if not cvs_data:
        return {
            'normal_blink_percentage': 0,
            'low_blink_percentage': 0,
            'high_blink_percentage': 0,
            'avg_blink_count': 0,
            'alert_count': 0,
            'monitoring_duration': 0
        }
    
    # Calculate average percentages
    normal_percentage = sum(entry.get('normal_blink_percentage', 0) for entry in cvs_data) / len(cvs_data)
    low_percentage = sum(entry.get('low_blink_percentage', 0) for entry in cvs_data) / len(cvs_data)
    high_percentage = sum(entry.get('high_blink_percentage', 0) for entry in cvs_data) / len(cvs_data)
    avg_blink_count = sum(entry.get('avg_blink_count', 0) for entry in cvs_data) / len(cvs_data)
    
    # Get alert count from the database
    alerts = db_manager.get_recent_alerts(100)  # Get a reasonable number of alerts
    cvs_alerts = [alert for alert in alerts if alert.get('type') == 'cvs']
    
    # Estimate monitoring duration (10 minutes per data point is a reasonable guess)
    monitoring_duration = len(cvs_data) * 10
    
    return {
        'normal_blink_percentage': round(normal_percentage, 1),
        'low_blink_percentage': round(low_percentage, 1),
        'high_blink_percentage': round(high_percentage, 1),
        'avg_blink_count': round(avg_blink_count, 1),
        'alert_count': len(cvs_alerts),
        'monitoring_duration': monitoring_duration
    }

def get_hydration_summary(db_manager, start_date, end_date):
    """Get summary of hydration data for a date range"""
    # Get actual data from the database
    hydration_data = db_manager.get_hydration_data_range(start_date, end_date)
    
    if not hydration_data:
        return {
            'normal_lips_percentage': 0,
            'dry_lips_percentage': 0,
            'avg_dryness_score': 0,
            'alert_count': 0,
            'monitoring_duration': 0
        }
    
    # Calculate average percentages
    normal_percentage = sum(entry.get('normal_lips_percentage', 0) for entry in hydration_data) / len(hydration_data)
    dry_percentage = sum(entry.get('dry_lips_percentage', 0) for entry in hydration_data) / len(hydration_data)
    avg_dryness_score = sum(entry.get('avg_dryness_score', 0) for entry in hydration_data) / len(hydration_data)
    
    # Get alert count from the database
    alerts = db_manager.get_recent_alerts(100)  # Get a reasonable number of alerts
    hydration_alerts = [alert for alert in alerts if alert.get('type') == 'hydration']
    
    # Estimate monitoring duration (10 minutes per data point is a reasonable guess)
    monitoring_duration = len(hydration_data) * 10
    
    return {
        'normal_lips_percentage': round(normal_percentage, 1),
        'dry_lips_percentage': round(dry_percentage, 1),
        'avg_dryness_score': round(avg_dryness_score, 2),
        'alert_count': len(hydration_alerts),
        'monitoring_duration': monitoring_duration
    }

def calculate_overall_health_score(summary):
    """Calculate an overall health score based on all monitoring data"""
    try:
        # Weight each component
        posture_weight = 0.25
        stress_weight = 0.25
        cvs_weight = 0.25
        hydration_weight = 0.25
        
        # Calculate individual scores with safe fallbacks (higher is better)
        posture_score = summary.get('posture', {}).get('good_posture_percentage', 0)
        stress_score = summary.get('stress', {}).get('low_stress_percentage', 0)
        cvs_score = summary.get('cvs', {}).get('normal_blink_percentage', 0)
        hydration_score = summary.get('hydration', {}).get('normal_lips_percentage', 0)
        
        # Calculate weighted average
        overall_score = (
            posture_score * posture_weight +
            stress_score * stress_weight +
            cvs_score * cvs_weight +
            hydration_score * hydration_weight
        )
        
        return round(overall_score, 1)
    except Exception as e:
        logger.error(f"Error calculating overall health score: {e}")
        return 0  # Return 0 as a safe fallback

# Sample data generators for development

def generate_sample_posture_data(timeframe, start_date=None, end_date=None):
    """Generate sample posture data for development"""
    result = {'labels': [], 'good_posture_percentage': [], 'bad_posture_percentage': []}
    
    # If we have date info, use it to generate appropriate sample data
    if start_date and end_date:
        if timeframe == 'daily':
            # For daily, use hours from 9 AM to 5 PM
            hours = ['09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00']
            result['labels'] = hours
        elif timeframe == 'weekly':
            # For weekly, calculate actual days between start_date and end_date (max 7)
            days = []
            current = start_date
            while current <= end_date and len(days) < 7:
                days.append(current.strftime('%a'))
                current += timedelta(days=1)
            result['labels'] = days
        else:  # monthly
            # For monthly, calculate actual days between start_date and end_date (max 31)
            days = []
            current = start_date
            while current <= end_date and len(days) < 31:
                days.append(str(current.day))
                current += timedelta(days=1)
            result['labels'] = days
    else:
        # Fallback to original behavior if no date range provided
        if timeframe == 'daily':
            hours = ['09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00']
            result['labels'] = hours
        elif timeframe == 'weekly':
            days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            result['labels'] = days
        else:  # monthly
            # Use numbers 1-30 for days of month
            result['labels'] = [str(i) for i in range(1, 31)]
    
    # Generate random percentages
    np.random.seed(42)  # For reproducibility
    for _ in range(len(result['labels'])):
        good = np.random.randint(60, 95)
        result['good_posture_percentage'].append(good)
        result['bad_posture_percentage'].append(100 - good)
    
    return result

def generate_sample_stress_data(timeframe, start_date=None, end_date=None):
    """Generate sample stress data for development"""
    result = {
        'labels': [], 
        'low_stress_percentage': [], 
        'medium_stress_percentage': [],
        'high_stress_percentage': []
    }
    
    # If we have date info, use it to generate appropriate sample data
    if start_date and end_date:
        if timeframe == 'daily':
            # For daily, use hours from 9 AM to 5 PM
            hours = ['09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00']
            result['labels'] = hours
        elif timeframe == 'weekly':
            # For weekly, calculate actual days between start_date and end_date (max 7)
            days = []
            current = start_date
            while current <= end_date and len(days) < 7:
                days.append(current.strftime('%a'))
                current += timedelta(days=1)
            result['labels'] = days
        else:  # monthly
            # For monthly, calculate actual days between start_date and end_date (max 31)
            days = []
            current = start_date
            while current <= end_date and len(days) < 31:
                days.append(str(current.day))
                current += timedelta(days=1)
            result['labels'] = days
    else:
        # Fallback to original behavior if no date range provided
        if timeframe == 'daily':
            hours = ['09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00']
            result['labels'] = hours
        elif timeframe == 'weekly':
            days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            result['labels'] = days
        else:  # monthly
            # Use numbers 1-30 for days of month
            result['labels'] = [str(i) for i in range(1, 31)]
    
    # Generate random percentages
    np.random.seed(43)  # For reproducibility
    for _ in range(len(result['labels'])):
        low = np.random.randint(40, 80)
        medium = np.random.randint(10, 40)
        if low + medium > 100:
            medium = 100 - low
        high = 100 - low - medium
        
        result['low_stress_percentage'].append(low)
        result['medium_stress_percentage'].append(medium)
        result['high_stress_percentage'].append(high)
    
    return result

def generate_sample_cvs_data(timeframe, start_date=None, end_date=None):
    """Generate sample CVS (eye strain) data for development"""
    result = {
        'labels': [], 
        'normal_blink_percentage': [], 
        'low_blink_percentage': [],
        'high_blink_percentage': [],
        'avg_blink_count': []
    }
    
    # If we have date info, use it to generate appropriate sample data
    if start_date and end_date:
        if timeframe == 'daily':
            # For daily, use hours from 9 AM to 5 PM
            hours = ['09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00']
            result['labels'] = hours
        elif timeframe == 'weekly':
            # For weekly, calculate actual days between start_date and end_date (max 7)
            days = []
            current = start_date
            while current <= end_date and len(days) < 7:
                days.append(current.strftime('%a'))
                current += timedelta(days=1)
            result['labels'] = days
        else:  # monthly
            # For monthly, calculate actual days between start_date and end_date (max 31)
            days = []
            current = start_date
            while current <= end_date and len(days) < 31:
                days.append(str(current.day))
                current += timedelta(days=1)
            result['labels'] = days
    else:
        # Fallback to original behavior if no date range provided
        if timeframe == 'daily':
            hours = ['09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00']
            result['labels'] = hours
        elif timeframe == 'weekly':
            days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            result['labels'] = days
        else:  # monthly
            # Use numbers 1-30 for days of month
            result['labels'] = [str(i) for i in range(1, 31)]
    
    # Generate random percentages
    np.random.seed(44)  # For reproducibility
    for _ in range(len(result['labels'])):
        normal = np.random.randint(50, 85)
        low = np.random.randint(5, 30)
        if normal + low > 100:
            low = 100 - normal
        high = 100 - normal - low
        
        result['normal_blink_percentage'].append(normal)
        result['low_blink_percentage'].append(low)
        result['high_blink_percentage'].append(high)
        result['avg_blink_count'].append(round(np.random.uniform(12, 20), 1))
    
    return result

def generate_sample_hydration_data(timeframe, start_date=None, end_date=None):
    """Generate sample hydration data for development"""
    result = {
        'labels': [], 
        'normal_lips_percentage': [], 
        'dry_lips_percentage': [],
        'avg_dryness_score': []
    }
    
    # If we have date info, use it to generate appropriate sample data
    if start_date and end_date:
        if timeframe == 'daily':
            # For daily, use hours from 9 AM to 5 PM
            hours = ['09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00']
            result['labels'] = hours
        elif timeframe == 'weekly':
            # For weekly, calculate actual days between start_date and end_date (max 7)
            days = []
            current = start_date
            while current <= end_date and len(days) < 7:
                days.append(current.strftime('%a'))
                current += timedelta(days=1)
            result['labels'] = days
        else:  # monthly
            # For monthly, calculate actual days between start_date and end_date (max 31)
            days = []
            current = start_date
            while current <= end_date and len(days) < 31:
                days.append(str(current.day))
                current += timedelta(days=1)
            result['labels'] = days
    else:
        # Fallback to original behavior if no date range provided
        if timeframe == 'daily':
            hours = ['09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00']
            result['labels'] = hours
        elif timeframe == 'weekly':
            days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            result['labels'] = days
        else:  # monthly
            # Use numbers 1-30 for days of month
            result['labels'] = [str(i) for i in range(1, 31)]
    
    # Generate random percentages
    np.random.seed(45)  # For reproducibility
    for _ in range(len(result['labels'])):
        normal = np.random.randint(60, 90)
        dry = 100 - normal
        
        result['normal_lips_percentage'].append(normal)
        result['dry_lips_percentage'].append(dry)
        result['avg_dryness_score'].append(round(np.random.uniform(0.2, 0.6), 2))
    
    return result 