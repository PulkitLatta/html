import pytest
from app.crud import calculate_priority_score

def test_priority_score_high_score():
    """Test priority score calculation with high overall score."""
    analysis_data = {
        "overallScore": 95.0,
        "avgConfidence": 0.9,
        "duration": 12.0
    }
    
    priority = calculate_priority_score(analysis_data)
    
    # High score should get high priority
    # 95 * 0.6 + 10 (confidence bonus) + 5 (duration bonus) = 72
    assert priority >= 70
    assert priority <= 100

def test_priority_score_low_score():
    """Test priority score calculation with low overall score."""
    analysis_data = {
        "overallScore": 45.0,
        "avgConfidence": 0.6,
        "duration": 5.0
    }
    
    priority = calculate_priority_score(analysis_data)
    
    # Low score should get lower priority
    # 45 * 0.6 = 27, no bonuses
    assert priority < 50

def test_priority_score_with_confidence_bonus():
    """Test priority score with confidence bonus."""
    analysis_data = {
        "overallScore": 70.0,
        "avgConfidence": 0.85,  # > 0.8, should get bonus
        "duration": 8.0
    }
    
    priority = calculate_priority_score(analysis_data)
    
    # Should get confidence bonus
    # 70 * 0.6 + 10 = 52
    assert priority >= 52

def test_priority_score_with_duration_bonus():
    """Test priority score with duration bonus."""
    analysis_data = {
        "overallScore": 60.0,
        "avgConfidence": 0.7,
        "duration": 15.0  # > 10, should get bonus
    }
    
    priority = calculate_priority_score(analysis_data)
    
    # Should get duration bonus
    # 60 * 0.6 + 5 = 41
    assert priority >= 41

def test_priority_score_all_bonuses():
    """Test priority score with all bonuses."""
    analysis_data = {
        "overallScore": 80.0,
        "avgConfidence": 0.85,  # Confidence bonus
        "duration": 15.0  # Duration bonus
    }
    
    priority = calculate_priority_score(analysis_data)
    
    # Should get all bonuses
    # 80 * 0.6 + 10 + 5 = 63
    assert priority >= 63

def test_priority_score_missing_fields():
    """Test priority score with missing fields (defaults to 0)."""
    analysis_data = {}
    
    priority = calculate_priority_score(analysis_data)
    
    # Should default to 0 for missing fields
    assert priority == 0.0

def test_priority_score_capped_at_100():
    """Test that priority score is capped at 100."""
    analysis_data = {
        "overallScore": 100.0,
        "avgConfidence": 1.0,
        "duration": 20.0
    }
    
    priority = calculate_priority_score(analysis_data)
    
    # Should be capped at 100
    assert priority == 100.0