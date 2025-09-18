import pytest
from app import crud

class TestPriorityScore:
    
    def test_calculate_priority_score(self):
        """Test priority score calculation"""
        from datetime import datetime, timedelta
        
        # Test high score, recent submission
        recent_time = datetime.utcnow()
        high_score = 95.0
        
        priority = crud.calculate_priority_score(high_score, recent_time)
        
        assert priority > 90  # Should be high priority
        
        # Test low score, old submission
        old_time = datetime.utcnow() - timedelta(hours=25)  # More than 24 hours
        low_score = 30.0
        
        priority = crud.calculate_priority_score(low_score, old_time)
        
        assert priority < 20  # Should be low priority
    
    def test_calculate_overall_score(self):
        """Test overall score calculation from analysis components"""
        
        # Perfect scores
        perfect_analysis = {
            "formConsistency": 100.0,
            "stability": 100.0,
            "rangeOfMotion": 200.0,  # Will be normalized
            "timing": 2.5  # Optimal timing
        }
        
        score = crud.calculate_overall_score(perfect_analysis)
        assert 90 <= score <= 100  # Should be very high
        
        # Poor scores
        poor_analysis = {
            "formConsistency": 20.0,
            "stability": 30.0,
            "rangeOfMotion": 50.0,
            "timing": 8.0  # Poor timing
        }
        
        score = crud.calculate_overall_score(poor_analysis)
        assert score <= 40  # Should be low
        
        # Missing data handling
        incomplete_analysis = {
            "formConsistency": 80.0
            # Missing other fields
        }
        
        score = crud.calculate_overall_score(incomplete_analysis)
        assert 0 <= score <= 100  # Should handle gracefully