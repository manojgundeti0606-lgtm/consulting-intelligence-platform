"""
Comprehensive Unit Tests for AI Analyzer Module

Tests cover:
- GeminiAnalyzer initialization and configuration
- API call retry logic and error handling
- Consulting Fit Score calculation with various bid types
- Go/No-Go matrix generation with edge cases
- Executive summary generation
- Complete bid analysis workflow
- Virtual user integration
- JSON parsing edge cases
- Timeout and rate limiting scenarios
"""

import os
import json
import time
import pytest
from unittest.mock import MagicMock, patch, Mock
from datetime import datetime, timedelta
from ai_analyzer import (
    GeminiAnalyzer,
    calculate_consulting_fit_score,
    generate_go_no_go_matrix,
    generate_executive_summary,
    analyze_bid_complete
)
from config import AI_CONFIG, FIRM_PROFILE


class TestGeminiAnalyzer:
    """Test suite for GeminiAnalyzer class"""
    
    def test_initialization(self):
        """Test GeminiAnalyzer initializes correctly"""
        analyzer = GeminiAnalyzer()
        assert analyzer.model_name is not None
        assert hasattr(analyzer, 'config')
        assert analyzer.config.temperature == AI_CONFIG['temperature']
        assert analyzer.config.max_output_tokens == AI_CONFIG['max_tokens']
    
    def test_model_name_prefix_removal(self):
        """Test that 'models/' prefix is removed from model name"""
        with patch.dict('ai_analyzer.AI_CONFIG', {'model': 'models/gemini-test-model'}):
            analyzer = GeminiAnalyzer()
            assert analyzer.model_name == 'gemini-test-model'
            assert not analyzer.model_name.startswith('models/')
    
    def test_model_name_without_prefix(self):
        """Test model name without prefix stays unchanged"""
        with patch.dict('ai_analyzer.AI_CONFIG', {'model': 'gemini-test-model'}):
            analyzer = GeminiAnalyzer()
            assert analyzer.model_name == 'gemini-test-model'
    
    @patch('ai_analyzer.client.models.generate_content')
    def test_call_gemini_success(self, mock_generate):
        """Test successful Gemini API call"""
        mock_response = Mock()
        mock_response.text = "Test response"
        mock_generate.return_value = mock_response
        
        analyzer = GeminiAnalyzer()
        result = analyzer._call_gemini("test prompt")
        
        assert result == "Test response"
        mock_generate.assert_called_once()
    
    @patch('ai_analyzer.client.models.generate_content')
    def test_call_gemini_retry_logic(self, mock_generate):
        """Test retry logic with exponential backoff"""
        # First call fails, second succeeds
        mock_response = Mock()
        mock_response.text = "Success after retry"
        mock_generate.side_effect = [Exception("API Error"), mock_response]
        
        analyzer = GeminiAnalyzer()
        with patch('time.sleep') as mock_sleep:
            result = analyzer._call_gemini("test prompt")
        
        assert result == "Success after retry"
        assert mock_generate.call_count == 2
        mock_sleep.assert_called_once_with(1)  # 2^0 = 1
    
    @patch('ai_analyzer.client.models.generate_content')
    def test_call_gemini_max_retries_exceeded(self, mock_generate):
        """Test that API call fails after max retries"""
        mock_generate.side_effect = Exception("Persistent API Error")
        
        analyzer = GeminiAnalyzer()
        with patch('time.sleep'):
            result = analyzer._call_gemini("test prompt")
        
        assert result is None
        assert mock_generate.call_count == AI_CONFIG['retry_attempts'] + 1
    
    @patch('ai_analyzer.client.models.generate_content')
    def test_call_gemini_exponential_backoff(self, mock_generate):
        """Test exponential backoff timing"""
        mock_generate.side_effect = [
            Exception("Error 1"),
            Exception("Error 2"),
            Exception("Error 3")
        ]
        
        analyzer = GeminiAnalyzer()
        with patch('time.sleep') as mock_sleep:
            result = analyzer._call_gemini("test prompt", retry_count=0)
        
        # Should sleep with 2^0 = 1 second
        mock_sleep.assert_called_with(1)


class TestConsultingFitScore:
    """Test suite for calculate_consulting_fit_score function"""
    
    @patch.object(GeminiAnalyzer, '_call_gemini')
    def test_strong_fit_consulting_bid(self, mock_call):
        """Test CFS calculation for strong fit consulting bid"""
        mock_call.return_value = json.dumps({
            "score": 95,
            "verdict": "Strong Fit",
            "reasoning": "Perfect match for EY's digital transformation expertise"
        })
        
        bid_data = {
            "Bid Number": "TEST/2024/001",
            "Items": "Digital Transformation Consultancy",
            "Department": "Ministry of Electronics"
        }
        
        result = calculate_consulting_fit_score(bid_data)
        
        assert result['score'] == 95
        assert result['verdict'] == "Strong Fit"
        assert "digital transformation" in result['reasoning'].lower()
    
    @patch.object(GeminiAnalyzer, '_call_gemini')
    def test_marginal_fit_bid(self, mock_call):
        """Test CFS calculation for marginal fit bid"""
        mock_call.return_value = json.dumps({
            "score": 65,
            "verdict": "Marginal Fit",
            "reasoning": "Some alignment with EY capabilities but not core expertise"
        })
        
        bid_data = {
            "Bid Number": "TEST/2024/002",
            "Items": "Training and Capacity Building",
            "Department": "Ministry of Skill Development"
        }
        
        result = calculate_consulting_fit_score(bid_data)
        
        assert 50 <= result['score'] < 80
        assert result['verdict'] == "Marginal Fit"
    
    @patch.object(GeminiAnalyzer, '_call_gemini')
    def test_out_of_scope_hardware_bid(self, mock_call):
        """Test CFS calculation for hardware procurement (out of scope)"""
        mock_call.return_value = json.dumps({
            "score": 15,
            "verdict": "Out of Scope",
            "reasoning": "This is hardware procurement, not consulting services"
        })
        
        bid_data = {
            "Bid Number": "TEST/2024/003",
            "Items": "Supply of 500 Desktop Computers",
            "Department": "Department of Education"
        }
        
        result = calculate_consulting_fit_score(bid_data)
        
        assert result['score'] < 50
        assert result['verdict'] == "Out of Scope"
    
    @patch.object(GeminiAnalyzer, '_call_gemini')
    def test_json_extraction_with_extra_text(self, mock_call):
        """Test JSON extraction when response has extra text"""
        mock_call.return_value = """Here is the analysis:
        {
            "score": 85,
            "verdict": "Strong Fit",
            "reasoning": "Excellent alignment with core capabilities"
        }
        Additional comments here."""
        
        bid_data = {
            "Bid Number": "TEST/2024/004",
            "Items": "ERP Implementation",
            "Department": "Ministry of Finance"
        }
        
        result = calculate_consulting_fit_score(bid_data)
        
        assert result['score'] == 85
        assert result['verdict'] == "Strong Fit"
    
    @patch.object(GeminiAnalyzer, '_call_gemini')
    def test_invalid_json_response(self, mock_call):
        """Test fallback when JSON parsing fails"""
        mock_call.return_value = "This is not valid JSON at all"
        
        bid_data = {
            "Bid Number": "TEST/2024/005",
            "Items": "Test Project",
            "Department": "Test Department"
        }
        
        result = calculate_consulting_fit_score(bid_data)
        
        assert result['score'] == 50
        assert result['verdict'] == "Marginal Fit"
        assert "Unable to analyze" in result['reasoning']
    
    @patch.object(GeminiAnalyzer, '_call_gemini')
    def test_no_json_in_response(self, mock_call):
        """Test fallback when no JSON brackets found"""
        mock_call.return_value = "No JSON here"
        
        bid_data = {
            "Bid Number": "TEST/2024/006",
            "Items": "Project",
            "Department": "Department"
        }
        
        result = calculate_consulting_fit_score(bid_data)
        
        assert result['score'] == 50
        assert result['verdict'] == "Marginal Fit"
    
    @patch.object(GeminiAnalyzer, '_call_gemini')
    def test_api_failure_returns_error_result(self, mock_call):
        """Test that API failure returns appropriate error result"""
        mock_call.return_value = None
        
        bid_data = {
            "Bid Number": "TEST/2024/007",
            "Items": "Test",
            "Department": "Test"
        }
        
        result = calculate_consulting_fit_score(bid_data)
        
        assert result['score'] == 0
        assert result['verdict'] == "Analysis Failed"
        assert "Gemini API unavailable" in result['reasoning']
    
    @patch.object(GeminiAnalyzer, '_call_gemini')
    def test_custom_firm_profile(self, mock_call):
        """Test CFS calculation with custom firm profile"""
        mock_call.return_value = json.dumps({
            "score": 80,
            "verdict": "Strong Fit",
            "reasoning": "Matches custom profile expertise"
        })
        
        custom_profile = {
            "expertise_areas": ["Custom Expertise 1", "Custom Expertise 2"],
            "industries": ["Custom Industry"]
        }
        
        bid_data = {
            "Bid Number": "TEST/2024/008",
            "Items": "Custom Project",
            "Department": "Custom Department"
        }
        
        result = calculate_consulting_fit_score(bid_data, custom_profile)
        
        assert result['score'] == 80
        mock_call.assert_called_once()
        # Verify custom profile was used in prompt
        call_args = mock_call.call_args[0][0]
        assert "Custom Expertise" in call_args


class TestGoNoGoMatrix:
    """Test suite for generate_go_no_go_matrix function"""
    
    @patch.object(GeminiAnalyzer, '_call_gemini')
    def test_go_decision_green_flags(self, mock_call):
        """Test GO decision with all green flags"""
        mock_call.return_value = json.dumps({
            "eligibility_flag": "GREEN",
            "timeline_flag": "GREEN",
            "technical_flag": "GREEN",
            "overall_recommendation": "GO",
            "key_concerns": "No major concerns identified",
            "opportunities": "Strong strategic fit with growth potential"
        })
        
        future_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        bid_data = {
            "Bid Number": "TEST/2024/001",
            "Items": "Cloud Migration Project",
            "Department": "Ministry of IT",
            "End Date": future_date
        }
        
        result = generate_go_no_go_matrix(bid_data)
        
        assert result['eligibility_flag'] == "GREEN"
        assert result['technical_flag'] == "GREEN"
        assert result['overall_recommendation'] == "GO"
        assert result['timeline_flag'] == "GREEN"  # 30+ days
    
    @patch.object(GeminiAnalyzer, '_call_gemini')
    def test_no_go_decision_red_flags(self, mock_call):
        """Test NO-GO decision with red flags"""
        mock_call.return_value = json.dumps({
            "eligibility_flag": "RED",
            "timeline_flag": "RED",
            "technical_flag": "RED",
            "overall_recommendation": "NO-GO",
            "key_concerns": "Incompatible requirements and insufficient timeline",
            "opportunities": "Limited value proposition"
        })
        
        past_date = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')
        bid_data = {
            "Bid Number": "TEST/2024/002",
            "Items": "Hardware Supply",
            "Department": "Department",
            "End Date": past_date
        }
        
        result = generate_go_no_go_matrix(bid_data)
        
        assert result['eligibility_flag'] == "RED"
        assert result['overall_recommendation'] == "NO-GO"
        assert result['timeline_flag'] == "RED"  # Less than 7 days
    
    @patch.object(GeminiAnalyzer, '_call_gemini')
    def test_timeline_calculation_less_than_7_days(self, mock_call):
        """Test timeline flag is RED when less than 7 days"""
        mock_call.return_value = json.dumps({
            "eligibility_flag": "GREEN",
            "timeline_flag": "GREEN",
            "technical_flag": "GREEN",
            "overall_recommendation": "MAYBE",
            "key_concerns": "Tight timeline",
            "opportunities": "Good fit otherwise"
        })
        
        future_date = (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d')
        bid_data = {
            "Bid Number": "TEST/2024/003",
            "Items": "Consulting",
            "Department": "Dept",
            "End Date": future_date
        }
        
        result = generate_go_no_go_matrix(bid_data)
        
        # Timeline should be overridden to RED
        assert result['timeline_flag'] == "RED"
    
    @patch.object(GeminiAnalyzer, '_call_gemini')
    def test_timeline_calculation_7_to_14_days(self, mock_call):
        """Test timeline flag is YELLOW when 7-14 days"""
        mock_call.return_value = json.dumps({
            "eligibility_flag": "GREEN",
            "timeline_flag": "GREEN",
            "technical_flag": "GREEN",
            "overall_recommendation": "GO",
            "key_concerns": "None",
            "opportunities": "Good"
        })
        
        future_date = (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d')
        bid_data = {
            "Bid Number": "TEST/2024/004",
            "Items": "Project",
            "Department": "Dept",
            "End Date": future_date
        }
        
        result = generate_go_no_go_matrix(bid_data)
        
        assert result['timeline_flag'] == "YELLOW"
    
    @patch.object(GeminiAnalyzer, '_call_gemini')
    def test_timeline_calculation_more_than_14_days(self, mock_call):
        """Test timeline flag is GREEN when more than 14 days"""
        mock_call.return_value = json.dumps({
            "eligibility_flag": "GREEN",
            "timeline_flag": "GREEN",
            "technical_flag": "GREEN",
            "overall_recommendation": "GO",
            "key_concerns": "None",
            "opportunities": "Excellent"
        })
        
        future_date = (datetime.now() + timedelta(days=20)).strftime('%Y-%m-%d')
        bid_data = {
            "Bid Number": "TEST/2024/005",
            "Items": "Project",
            "Department": "Dept",
            "End Date": future_date
        }
        
        result = generate_go_no_go_matrix(bid_data)
        
        assert result['timeline_flag'] == "GREEN"
    
    @patch.object(GeminiAnalyzer, '_call_gemini')
    def test_invalid_date_format(self, mock_call):
        """Test handling of invalid date format"""
        mock_call.return_value = json.dumps({
            "eligibility_flag": "GREEN",
            "timeline_flag": "GREEN",
            "technical_flag": "GREEN",
            "overall_recommendation": "MAYBE",
            "key_concerns": "Unknown timeline",
            "opportunities": "TBD"
        })
        
        bid_data = {
            "Bid Number": "TEST/2024/006",
            "Items": "Project",
            "Department": "Dept",
            "End Date": "invalid-date"
        }
        
        result = generate_go_no_go_matrix(bid_data)
        
        # Should default to YELLOW when date parsing fails
        assert result['timeline_flag'] == "YELLOW"
    
    @patch.object(GeminiAnalyzer, '_call_gemini')
    def test_with_sow_text(self, mock_call):
        """Test Go/No-Go analysis with SOW text provided"""
        mock_call.return_value = json.dumps({
            "eligibility_flag": "GREEN",
            "timeline_flag": "GREEN",
            "technical_flag": "GREEN",
            "overall_recommendation": "GO",
            "key_concerns": "None identified",
            "opportunities": "Well-documented scope"
        })
        
        sow_text = "Detailed scope of work: Implement cloud infrastructure..."
        bid_data = {
            "Bid Number": "TEST/2024/007",
            "Items": "Cloud Project",
            "Department": "IT Dept",
            "End Date": "2025-12-31"
        }
        
        result = generate_go_no_go_matrix(bid_data, sow_text)
        
        assert result['overall_recommendation'] == "GO"
        # Verify SOW was included in prompt
        call_args = mock_call.call_args[0][0]
        assert "Implement cloud infrastructure" in call_args
    
    @patch.object(GeminiAnalyzer, '_call_gemini')
    def test_long_sow_text_truncation(self, mock_call):
        """Test that long SOW text is truncated to 1000 chars"""
        mock_call.return_value = json.dumps({
            "eligibility_flag": "GREEN",
            "timeline_flag": "GREEN",
            "technical_flag": "GREEN",
            "overall_recommendation": "GO",
            "key_concerns": "None",
            "opportunities": "Good"
        })
        
        sow_text = "x" * 2000  # 2000 character SOW
        bid_data = {
            "Bid Number": "TEST/2024/008",
            "Items": "Project",
            "Department": "Dept",
            "End Date": "2025-12-31"
        }
        
        result = generate_go_no_go_matrix(bid_data, sow_text)
        
        # Verify SOW was truncated in prompt
        call_args = mock_call.call_args[0][0]
        assert "x" * 1000 in call_args
        assert "x" * 1001 not in call_args
    
    @patch.object(GeminiAnalyzer, '_call_gemini')
    def test_api_failure_fallback(self, mock_call):
        """Test fallback when API fails"""
        mock_call.return_value = None
        
        bid_data = {
            "Bid Number": "TEST/2024/009",
            "Items": "Project",
            "Department": "Dept",
            "End Date": "2025-12-31"
        }
        
        result = generate_go_no_go_matrix(bid_data)
        
        assert result['eligibility_flag'] == "YELLOW"
        assert result['technical_flag'] == "YELLOW"
        assert result['overall_recommendation'] == "MAYBE"
        assert "Unable to analyze" in result['key_concerns']
    
    @patch.object(GeminiAnalyzer, '_call_gemini')
    def test_json_parse_error_fallback(self, mock_call):
        """Test fallback when JSON parsing fails"""
        mock_call.return_value = "Not valid JSON"
        
        bid_data = {
            "Bid Number": "TEST/2024/010",
            "Items": "Project",
            "Department": "Dept",
            "End Date": "2025-12-31"
        }
        
        result = generate_go_no_go_matrix(bid_data)
        
        assert result['eligibility_flag'] == "YELLOW"
        assert result['overall_recommendation'] == "MAYBE"


class TestExecutiveSummary:
    """Test suite for generate_executive_summary function"""
    
    @patch.object(GeminiAnalyzer, '_call_gemini')
    def test_summary_generation_with_sow(self, mock_call):
        """Test executive summary generation with SOW text"""
        mock_call.return_value = json.dumps({
            "the_ask": "Implement cloud-based ERP system for financial management",
            "key_deliverables": [
                "Cloud infrastructure setup",
                "ERP system configuration",
                "User training program"
            ],
            "evaluation_criteria": "QCBS with 70% technical and 30% financial weightage"
        })
        
        sow_text = "The client requires cloud ERP implementation..."
        bid_data = {
            "Bid Number": "TEST/2024/001",
            "Items": "ERP Implementation"
        }
        
        result = generate_executive_summary(sow_text, bid_data)
        
        assert "ERP system" in result['the_ask']
        assert len(result['key_deliverables']) == 3
        assert "QCBS" in result['evaluation_criteria']
    
    @patch.object(GeminiAnalyzer, '_call_gemini')
    def test_summary_without_sow_text(self, mock_call):
        """Test summary generation when SOW text is empty"""
        mock_call.return_value = json.dumps({
            "the_ask": "Digital transformation consultancy services",
            "key_deliverables": [
                "Assessment report",
                "Implementation roadmap",
                "Change management plan"
            ],
            "evaluation_criteria": "L1 - Lowest bidder"
        })
        
        bid_data = {
            "Bid Number": "TEST/2024/002",
            "Items": "Digital Transformation Consultancy"
        }
        
        result = generate_executive_summary("", bid_data)
        
        assert result['the_ask'] is not None
        assert len(result['key_deliverables']) > 0
    
    @patch.object(GeminiAnalyzer, '_call_gemini')
    def test_long_sow_truncation(self, mock_call):
        """Test that long SOW is truncated to 2000 chars"""
        mock_call.return_value = json.dumps({
            "the_ask": "Test ask",
            "key_deliverables": ["Test deliverable"],
            "evaluation_criteria": "Test criteria"
        })
        
        sow_text = "y" * 5000  # 5000 character SOW
        bid_data = {
            "Bid Number": "TEST/2024/003",
            "Items": "Project"
        }
        
        result = generate_executive_summary(sow_text, bid_data)
        
        # Verify SOW was truncated
        call_args = mock_call.call_args[0][0]
        assert "y" * 2000 in call_args
        assert "y" * 2001 not in call_args
    
    @patch.object(GeminiAnalyzer, '_call_gemini')
    def test_api_failure_fallback(self, mock_call):
        """Test fallback when API fails"""
        mock_call.return_value = None
        
        bid_data = {
            "Bid Number": "TEST/2024/004",
            "Items": "Test Project"
        }
        
        result = generate_executive_summary("SOW text", bid_data)
        
        assert "Test Project" in result['the_ask']
        assert "To be determined" in result['key_deliverables'][0]
        assert result['evaluation_criteria'] == "Not specified"
    
    @patch.object(GeminiAnalyzer, '_call_gemini')
    def test_json_parse_error_fallback(self, mock_call):
        """Test fallback when JSON parsing fails"""
        mock_call.return_value = "Invalid JSON response"
        
        bid_data = {
            "Bid Number": "TEST/2024/005",
            "Items": "Consulting Services"
        }
        
        result = generate_executive_summary("SOW", bid_data)
        
        assert "Consulting Services" in result['the_ask']
        assert len(result['key_deliverables']) > 0
    
    @patch.object(GeminiAnalyzer, '_call_gemini')
    def test_deliverables_list_format(self, mock_call):
        """Test that deliverables are returned as a list"""
        mock_call.return_value = json.dumps({
            "the_ask": "Test",
            "key_deliverables": [
                "Deliverable 1",
                "Deliverable 2",
                "Deliverable 3"
            ],
            "evaluation_criteria": "Test"
        })
        
        bid_data = {"Bid Number": "TEST/2024/006", "Items": "Test"}
        result = generate_executive_summary("SOW", bid_data)
        
        assert isinstance(result['key_deliverables'], list)
        assert len(result['key_deliverables']) == 3


class TestCompleteBidAnalysis:
    """Test suite for analyze_bid_complete function"""
    
    @patch('ai_analyzer.calculate_consulting_fit_score')
    @patch('ai_analyzer.generate_go_no_go_matrix')
    @patch('ai_analyzer.generate_executive_summary')
    def test_complete_analysis_high_cfs(self, mock_summary, mock_gng, mock_cfs):
        """Test complete analysis with high CFS score"""
        mock_cfs.return_value = {
            "score": 85,
            "verdict": "Strong Fit",
            "reasoning": "Perfect match"
        }
        mock_gng.return_value = {
            "eligibility_flag": "GREEN",
            "timeline_flag": "GREEN",
            "technical_flag": "GREEN",
            "overall_recommendation": "GO",
            "key_concerns": "None",
            "opportunities": "Great opportunity"
        }
        mock_summary.return_value = {
            "the_ask": "Implement system",
            "key_deliverables": ["System", "Training", "Documentation"],
            "evaluation_criteria": "QCBS"
        }
        
        bid_data = {
            "Bid Number": "TEST/2024/001",
            "Items": "System Implementation",
            "Department": "IT Dept",
            "End Date": "2025-12-31"
        }
        
        result = analyze_bid_complete(bid_data)
        
        assert result['bid_number'] == "TEST/2024/001"
        assert result['cfs']['score'] == 85
        assert result['go_no_go']['overall_recommendation'] == "GO"
        assert len(result['executive_summary']['key_deliverables']) == 3
        assert 'analyzed_at' in result
    
    @patch('ai_analyzer.calculate_consulting_fit_score')
    @patch('ai_analyzer.generate_go_no_go_matrix')
    @patch('ai_analyzer.generate_executive_summary')
    def test_complete_analysis_low_cfs_skips_summary(self, mock_summary, mock_gng, mock_cfs):
        """Test that executive summary is skipped when CFS < 50"""
        mock_cfs.return_value = {
            "score": 30,
            "verdict": "Out of Scope",
            "reasoning": "Hardware procurement"
        }
        mock_gng.return_value = {
            "eligibility_flag": "RED",
            "timeline_flag": "YELLOW",
            "technical_flag": "RED",
            "overall_recommendation": "NO-GO",
            "key_concerns": "Not consulting",
            "opportunities": "None"
        }
        
        bid_data = {
            "Bid Number": "TEST/2024/002",
            "Items": "Hardware Supply",
            "Department": "Dept",
            "End Date": "2025-12-31"
        }
        
        result = analyze_bid_complete(bid_data)
        
        assert result['cfs']['score'] == 30
        assert result['executive_summary']['the_ask'] == "Out of scope - analysis skipped"
        assert result['executive_summary']['key_deliverables'] == []
        # Verify summary was not called
        mock_summary.assert_not_called()
    
    @patch('ai_analyzer.calculate_consulting_fit_score')
    @patch('ai_analyzer.generate_go_no_go_matrix')
    @patch('ai_analyzer.generate_executive_summary')
    @patch('os.path.exists')
    @patch('ai_analyzer.BidReaderAgent')
    def test_complete_analysis_with_pdf(self, mock_agent_class, mock_exists, 
                                       mock_summary, mock_gng, mock_cfs):
        """Test complete analysis with PDF virtual user"""
        mock_exists.return_value = True
        mock_agent = Mock()
        mock_agent.summarize_sow.return_value = "Virtual user extracted SOW text"
        mock_agent_class.return_value = mock_agent
        
        mock_cfs.return_value = {
            "score": 75,
            "verdict": "Marginal Fit",
            "reasoning": "Some alignment"
        }
        mock_gng.return_value = {
            "eligibility_flag": "GREEN",
            "timeline_flag": "YELLOW",
            "technical_flag": "GREEN",
            "overall_recommendation": "MAYBE",
            "key_concerns": "Tight timeline",
            "opportunities": "Good fit"
        }
        mock_summary.return_value = {
            "the_ask": "Test",
            "key_deliverables": ["Test"],
            "evaluation_criteria": "Test"
        }
        
        bid_data = {
            "Bid Number": "TEST/2024/003",
            "Items": "Project",
            "Department": "Dept",
            "End Date": "2025-12-31"
        }
        
        result = analyze_bid_complete(bid_data, pdf_path="test.pdf")
        
        assert result['sow_summary'] == "Virtual user extracted SOW text"
        mock_agent_class.assert_called_once_with("test.pdf")
        mock_agent.summarize_sow.assert_called_once()
        # Verify Go/No-Go was called with virtual user summary
        mock_gng.assert_called_once()
        gng_call_args = mock_gng.call_args[0]
        assert gng_call_args[1] == "Virtual user extracted SOW text"
    
    @patch('ai_analyzer.calculate_consulting_fit_score')
    @patch('ai_analyzer.generate_go_no_go_matrix')
    @patch('ai_analyzer.generate_executive_summary')
    @patch('os.path.exists')
    def test_complete_analysis_pdf_not_exists(self, mock_exists, mock_summary, 
                                              mock_gng, mock_cfs):
        """Test analysis when PDF path doesn't exist"""
        mock_exists.return_value = False
        
        mock_cfs.return_value = {
            "score": 70,
            "verdict": "Marginal Fit",
            "reasoning": "Test"
        }
        mock_gng.return_value = {
            "eligibility_flag": "GREEN",
            "timeline_flag": "GREEN",
            "technical_flag": "GREEN",
            "overall_recommendation": "GO",
            "key_concerns": "None",
            "opportunities": "Good"
        }
        mock_summary.return_value = {
            "the_ask": "Test",
            "key_deliverables": ["Test"],
            "evaluation_criteria": "Test"
        }
        
        bid_data = {
            "Bid Number": "TEST/2024/004",
            "Items": "Project",
            "Department": "Dept",
            "End Date": "2025-12-31"
        }
        
        result = analyze_bid_complete(bid_data, sow_text="Manual SOW", 
                                      pdf_path="nonexistent.pdf")
        
        # Should use manual SOW text instead
        assert result['sow_summary'] == "Manual SOW"
    
    @patch('ai_analyzer.calculate_consulting_fit_score')
    @patch('ai_analyzer.generate_go_no_go_matrix')
    @patch('ai_analyzer.generate_executive_summary')
    @patch('os.path.exists')
    @patch('ai_analyzer.BidReaderAgent')
    def test_complete_analysis_pdf_error_handling(self, mock_agent_class, 
                                                  mock_exists, mock_summary,
                                                  mock_gng, mock_cfs):
        """Test error handling when virtual user fails"""
        mock_exists.return_value = True
        mock_agent = Mock()
        mock_agent.summarize_sow.side_effect = Exception("PDF read error")
        mock_agent_class.return_value = mock_agent
        
        mock_cfs.return_value = {
            "score": 60,
            "verdict": "Marginal Fit",
            "reasoning": "Test"
        }
        mock_gng.return_value = {
            "eligibility_flag": "YELLOW",
            "timeline_flag": "GREEN",
            "technical_flag": "GREEN",
            "overall_recommendation": "MAYBE",
            "key_concerns": "Unknown",
            "opportunities": "TBD"
        }
        mock_summary.return_value = {
            "the_ask": "Test",
            "key_deliverables": ["Test"],
            "evaluation_criteria": "Test"
        }
        
        bid_data = {
            "Bid Number": "TEST/2024/005",
            "Items": "Project",
            "Department": "Dept",
            "End Date": "2025-12-31"
        }
        
        result = analyze_bid_complete(bid_data, sow_text="Fallback SOW", 
                                      pdf_path="error.pdf")
        
        # Should use fallback SOW when virtual user fails
        assert result['sow_summary'] == "Fallback SOW"
    
    @patch('ai_analyzer.calculate_consulting_fit_score')
    @patch('ai_analyzer.generate_go_no_go_matrix')
    def test_timestamp_format(self, mock_gng, mock_cfs):
        """Test that analyzed_at timestamp is in correct format"""
        mock_cfs.return_value = {
            "score": 40,
            "verdict": "Out of Scope",
            "reasoning": "Test"
        }
        mock_gng.return_value = {
            "eligibility_flag": "RED",
            "timeline_flag": "RED",
            "technical_flag": "RED",
            "overall_recommendation": "NO-GO",
            "key_concerns": "Test",
            "opportunities": "None"
        }
        
        bid_data = {
            "Bid Number": "TEST/2024/006",
            "Items": "Test",
            "Department": "Test",
            "End Date": "2025-12-31"
        }
        
        result = analyze_bid_complete(bid_data)
        
        # Verify timestamp format
        timestamp = result['analyzed_at']
        datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')  # Should not raise


class TestEdgeCases:
    """Test suite for edge cases and error conditions"""
    
    @patch.object(GeminiAnalyzer, '_call_gemini')
    def test_empty_bid_data(self, mock_call):
        """Test handling of empty bid data"""
        mock_call.return_value = json.dumps({
            "score": 0,
            "verdict": "Analysis Failed",
            "reasoning": "Insufficient data"
        })
        
        result = calculate_consulting_fit_score({})
        
        assert result['score'] >= 0
        assert result['verdict'] is not None
    
    @patch.object(GeminiAnalyzer, '_call_gemini')
    def test_missing_bid_fields(self, mock_call):
        """Test handling when bid fields are missing"""
        mock_call.return_value = json.dumps({
            "score": 50,
            "verdict": "Marginal Fit",
            "reasoning": "Limited information"
        })
        
        # Bid with missing optional fields
        bid_data = {"Bid Number": "TEST/2024/001"}
        
        result = calculate_consulting_fit_score(bid_data)
        
        assert result is not None
        assert 'score' in result
    
    @patch.object(GeminiAnalyzer, '_call_gemini')
    def test_special_characters_in_bid_data(self, mock_call):
        """Test handling of special characters in bid data"""
        mock_call.return_value = json.dumps({
            "score": 70,
            "verdict": "Marginal Fit",
            "reasoning": "Test with special chars"
        })
        
        bid_data = {
            "Bid Number": "TEST/2024/001 & 'Special' \"Chars\"",
            "Items": "Project <with> {special} [characters]",
            "Department": "Dept\nWith\nNewlines"
        }
        
        result = calculate_consulting_fit_score(bid_data)
        
        assert result['score'] == 70
    
    @patch.object(GeminiAnalyzer, '_call_gemini')
    def test_unicode_characters(self, mock_call):
        """Test handling of Unicode characters"""
        mock_call.return_value = json.dumps({
            "score": 65,
            "verdict": "Marginal Fit",
            "reasoning": "Unicode test"
        })
        
        bid_data = {
            "Bid Number": "TEST/2024/001",
            "Items": "परियोजना संबंधी कार्य",
            "Department": "部门"
        }
        
        result = calculate_consulting_fit_score(bid_data)
        
        assert result is not None
    
    @patch.object(GeminiAnalyzer, '_call_gemini')
    def test_very_long_bid_description(self, mock_call):
        """Test handling of very long bid descriptions"""
        mock_call.return_value = json.dumps({
            "score": 55,
            "verdict": "Marginal Fit",
            "reasoning": "Long description"
        })
        
        bid_data = {
            "Bid Number": "TEST/2024/001",
            "Items": "A" * 10000,  # 10000 character description
            "Department": "Test Department"
        }
        
        result = calculate_consulting_fit_score(bid_data)
        
        assert result is not None


class TestIntegration:
    """Integration tests for complete workflows"""
    
    @patch.object(GeminiAnalyzer, '_call_gemini')
    def test_full_workflow_consulting_bid(self, mock_call):
        """Test full workflow for a typical consulting bid"""
        # Mock different responses for different function calls
        def side_effect(prompt):
            if "Consulting Fit Score" in prompt or "score from 0-100" in prompt:
                return json.dumps({
                    "score": 88,
                    "verdict": "Strong Fit",
                    "reasoning": "Excellent match for digital transformation"
                })
            elif "GO/NO-GO" in prompt or "Assess this bid" in prompt:
                return json.dumps({
                    "eligibility_flag": "GREEN",
                    "timeline_flag": "GREEN",
                    "technical_flag": "GREEN",
                    "overall_recommendation": "GO",
                    "key_concerns": "None identified",
                    "opportunities": "Strong strategic value"
                })
            else:  # Executive summary
                return json.dumps({
                    "the_ask": "Modernize government IT infrastructure",
                    "key_deliverables": [
                        "Cloud migration strategy",
                        "Security framework",
                        "Training program"
                    ],
                    "evaluation_criteria": "QCBS 70:30"
                })
        
        mock_call.side_effect = side_effect
        
        bid_data = {
            "Bid Number": "MoIT/2024/DT/001",
            "Items": "Digital Transformation Consultancy Services",
            "Department": "Ministry of IT",
            "End Date": (datetime.now() + timedelta(days=20)).strftime('%Y-%m-%d')
        }
        
        result = analyze_bid_complete(bid_data)
        
        # Verify complete workflow
        assert result['cfs']['score'] >= 80
        assert result['cfs']['verdict'] == "Strong Fit"
        assert result['go_no_go']['overall_recommendation'] == "GO"
        assert len(result['executive_summary']['key_deliverables']) == 3
        assert result['bid_number'] == "MoIT/2024/DT/001"
    
    @patch.object(GeminiAnalyzer, '_call_gemini')
    def test_full_workflow_out_of_scope_bid(self, mock_call):
        """Test full workflow for out-of-scope hardware bid"""
        def side_effect(prompt):
            if "Consulting Fit Score" in prompt or "score from 0-100" in prompt:
                return json.dumps({
                    "score": 20,
                    "verdict": "Out of Scope",
                    "reasoning": "Hardware procurement, not consulting"
                })
            else:  # Go/No-Go
                return json.dumps({
                    "eligibility_flag": "RED",
                    "timeline_flag": "GREEN",
                    "technical_flag": "RED",
                    "overall_recommendation": "NO-GO",
                    "key_concerns": "Not a consulting opportunity",
                    "opportunities": "None"
                })
        
        mock_call.side_effect = side_effect
        
        bid_data = {
            "Bid Number": "HARDWARE/2024/001",
            "Items": "Supply of 1000 Desktop Computers",
            "Department": "Education Department",
            "End Date": (datetime.now() + timedelta(days=15)).strftime('%Y-%m-%d')
        }
        
        result = analyze_bid_complete(bid_data)
        
        # Verify out-of-scope handling
        assert result['cfs']['score'] < 50
        assert result['cfs']['verdict'] == "Out of Scope"
        assert result['go_no_go']['overall_recommendation'] == "NO-GO"
        assert result['executive_summary']['the_ask'] == "Out of scope - analysis skipped"
        assert result['executive_summary']['key_deliverables'] == []


# Performance and stress tests
class TestPerformance:
    """Performance and stress tests"""
    
    @patch.object(GeminiAnalyzer, '_call_gemini')
    def test_multiple_sequential_analyses(self, mock_call):
        """Test multiple sequential bid analyses"""
        mock_call.return_value = json.dumps({
            "score": 75,
            "verdict": "Marginal Fit",
            "reasoning": "Test"
        })
        
        bids = [
            {"Bid Number": f"TEST/2024/{i:03d}", "Items": f"Project {i}", 
             "Department": f"Dept {i}"} 
            for i in range(10)
        ]
        
        results = []
        for bid in bids:
            result = calculate_consulting_fit_score(bid)
            results.append(result)
        
        assert len(results) == 10
        assert all(r['score'] == 75 for r in results)
    
    @patch.object(GeminiAnalyzer, '_call_gemini')
    def test_retry_backoff_timing(self, mock_call):
        """Test that retry backoff actually increases wait time"""
        mock_call.side_effect = [
            Exception("Error 1"),
            Exception("Error 2"),
            Mock(text="Success")
        ]
        
        analyzer = GeminiAnalyzer()
        start_time = time.time()
        
        with patch('time.sleep') as mock_sleep:
            result = analyzer._call_gemini("test")
        
        # Verify exponential backoff was called with increasing values
        calls = mock_sleep.call_args_list
        assert len(calls) == 2  # Two failures before success
        assert calls[0][0][0] == 1  # 2^0 = 1
        assert calls[1][0][0] == 2  # 2^1 = 2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])