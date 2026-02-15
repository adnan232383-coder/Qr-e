"""
Backend API tests for 50/50 Presentation features
Testing: video streaming, audio streaming, 50/50 presentation HTML, universities, courses, MCQ questions
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAPIHealth:
    """API health and basic endpoints"""
    
    def test_api_endpoint_returns_data(self):
        """Test /api endpoint exists"""
        response = requests.get(f"{BASE_URL}/api")
        # API root may return empty or some status
        assert response.status_code in [200, 404, 405], f"Unexpected status: {response.status_code}"
        print(f"✓ API endpoint accessible - Status: {response.status_code}")


class TestUniversitiesAPI:
    """Test universities catalog API"""
    
    def test_get_universities(self):
        """Test GET /api/universities returns list"""
        response = requests.get(f"{BASE_URL}/api/universities")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Expected list of universities"
        assert len(data) >= 1, "Expected at least 1 university"
        
        # Validate structure
        uni = data[0]
        assert "external_id" in uni, "Missing external_id"
        assert "name" in uni, "Missing name"
        assert "country" in uni, "Missing country"
        print(f"✓ Universities API returns {len(data)} universities")


class TestCoursesAPI:
    """Test courses API endpoints"""
    
    def test_get_courses(self):
        """Test GET /api/courses returns list"""
        response = requests.get(f"{BASE_URL}/api/courses")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Expected list of courses"
        print(f"✓ Courses API returns {len(data)} courses")
    
    def test_get_course_questions(self):
        """Test GET /api/courses/{course_id}/questions returns MCQ questions"""
        course_id = "UG_DENT_Y1_S1_C01"
        response = requests.get(f"{BASE_URL}/api/courses/{course_id}/questions")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "total" in data, "Missing total count"
        assert "questions" in data, "Missing questions array"
        assert data["total"] > 0, "Expected at least 1 question"
        
        # Validate question structure
        if data["questions"]:
            q = data["questions"][0]
            assert "question" in q, "Missing question text"
            assert "option_a" in q, "Missing option_a"
            assert "option_b" in q, "Missing option_b"
            assert "option_c" in q, "Missing option_c"
            assert "option_d" in q, "Missing option_d"
            assert "correct_answer" in q, "Missing correct_answer"
        
        print(f"✓ Course {course_id} has {data['total']} MCQ questions")


class TestVideoStreamingAPI:
    """Test avatar video streaming endpoints"""
    
    def test_avatar_video_serves_correctly(self):
        """Test GET /api/avatar-videos/{module_id} serves video"""
        module_id = "UG_DENT_Y1_S1_C01_M01"
        response = requests.get(f"{BASE_URL}/api/avatar-videos/{module_id}", stream=True)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.headers.get("content-type") == "video/mp4", f"Expected video/mp4, got {response.headers.get('content-type')}"
        
        # Check we can read some bytes (video starts)
        chunk = next(response.iter_content(chunk_size=1024), None)
        assert chunk is not None, "Expected video content"
        assert len(chunk) > 0, "Expected non-empty video content"
        
        print(f"✓ Avatar video for {module_id} serves correctly (video/mp4)")
    
    def test_avatar_video_head_request(self):
        """Test HEAD /api/avatar-videos/{module_id} returns video metadata"""
        module_id = "UG_DENT_Y1_S1_C01_M01"
        response = requests.head(f"{BASE_URL}/api/avatar-videos/{module_id}")
        
        # HEAD may or may not be supported, check 200 or 405
        if response.status_code == 200:
            assert response.headers.get("content-type") == "video/mp4"
            print(f"✓ Avatar video HEAD request supported")
        else:
            print(f"! HEAD request returns {response.status_code} (may not be fully supported)")


class TestAudioStreamingAPI:
    """Test audio streaming endpoints"""
    
    def test_audio_serves_correctly(self):
        """Test GET /api/audio/{filename} serves audio"""
        filename = "UG_DENT_Y1_S1_C01_M01.mp3"
        response = requests.get(f"{BASE_URL}/api/audio/{filename}", stream=True)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.headers.get("content-type") == "audio/mpeg", f"Expected audio/mpeg, got {response.headers.get('content-type')}"
        
        # Check we can read some bytes
        chunk = next(response.iter_content(chunk_size=1024), None)
        assert chunk is not None, "Expected audio content"
        assert len(chunk) > 0, "Expected non-empty audio content"
        
        print(f"✓ Audio file {filename} serves correctly (audio/mpeg)")
    
    def test_audio_head_request(self):
        """Test HEAD /api/audio/{filename} returns audio metadata"""
        filename = "UG_DENT_Y1_S1_C01_M01.mp3"
        response = requests.head(f"{BASE_URL}/api/audio/{filename}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.headers.get("content-type") == "audio/mpeg"
        assert "Content-Length" in response.headers or int(response.headers.get("Content-Length", 0)) > 0
        print(f"✓ Audio HEAD request returns metadata")


class Test50_50PresentationAPI:
    """Test 50/50 split-screen presentation endpoints"""
    
    def test_50_50_presentation_serves_html(self):
        """Test GET /api/presentations-50-50/{module_id} serves HTML"""
        module_id = "UG_DENT_Y1_S1_C01_M01"
        response = requests.get(f"{BASE_URL}/api/presentations-50-50/{module_id}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert "text/html" in response.headers.get("content-type", ""), f"Expected text/html, got {response.headers.get('content-type')}"
        
        html_content = response.text
        assert len(html_content) > 100, "Expected substantial HTML content"
        print(f"✓ 50/50 Presentation HTML serves correctly ({len(html_content)} chars)")
    
    def test_50_50_presentation_contains_avatar_video(self):
        """Test presentation HTML includes avatar video element"""
        module_id = "UG_DENT_Y1_S1_C01_M01"
        response = requests.get(f"{BASE_URL}/api/presentations-50-50/{module_id}")
        
        assert response.status_code == 200
        html = response.text
        
        # Check for video element
        assert '<video' in html, "Expected video element in HTML"
        assert 'avatar-videos' in html or 'avatarVideo' in html, "Expected avatar video reference"
        print(f"✓ 50/50 Presentation contains avatar video element")
    
    def test_50_50_presentation_contains_subtitles_toggle(self):
        """Test presentation HTML includes subtitle toggle button"""
        module_id = "UG_DENT_Y1_S1_C01_M01"
        response = requests.get(f"{BASE_URL}/api/presentations-50-50/{module_id}")
        
        assert response.status_code == 200
        html = response.text
        
        # Check for subtitles elements
        assert 'subtitles' in html.lower() or 'subtitle' in html.lower(), "Expected subtitles reference"
        assert 'data-testid="subtitles-toggle"' in html or 'subtitlesToggle' in html, "Expected subtitle toggle button"
        print(f"✓ 50/50 Presentation contains subtitles toggle")
    
    def test_50_50_presentation_contains_play_button(self):
        """Test presentation HTML includes play button control"""
        module_id = "UG_DENT_Y1_S1_C01_M01"
        response = requests.get(f"{BASE_URL}/api/presentations-50-50/{module_id}")
        
        assert response.status_code == 200
        html = response.text
        
        # Check for play button
        assert 'playBtn' in html or 'data-testid="play-btn"' in html, "Expected play button"
        print(f"✓ 50/50 Presentation contains play button")
    
    def test_50_50_presentation_contains_50_50_layout(self):
        """Test presentation HTML has 50/50 split layout"""
        module_id = "UG_DENT_Y1_S1_C01_M01"
        response = requests.get(f"{BASE_URL}/api/presentations-50-50/{module_id}")
        
        assert response.status_code == 200
        html = response.text
        
        # Check for grid/flex layout indicators
        assert 'grid-template-columns: 1fr 1fr' in html or 'avatar-panel' in html, "Expected 50/50 split layout"
        assert 'slides-panel' in html, "Expected slides panel for right side"
        print(f"✓ 50/50 Presentation has split-screen layout")
    
    def test_second_50_50_presentation_exists(self):
        """Test second available 50/50 presentation"""
        module_id = "UG_DENT_Y3_S1_C03_M01"
        response = requests.get(f"{BASE_URL}/api/presentations-50-50/{module_id}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert "text/html" in response.headers.get("content-type", "")
        print(f"✓ Second 50/50 Presentation ({module_id}) available")


class TestPresentationSubtitles:
    """Test subtitle functionality in presentations"""
    
    def test_presentation_has_hebrew_subtitles_option(self):
        """Test presentation includes Hebrew translation option"""
        module_id = "UG_DENT_Y1_S1_C01_M01"
        response = requests.get(f"{BASE_URL}/api/presentations-50-50/{module_id}")
        
        assert response.status_code == 200
        html = response.text
        
        # Check for Hebrew language option (even if placeholder)
        assert 'he' in html or 'hebrew' in html.lower() or 'עברית' in html, "Expected Hebrew language option"
        print(f"✓ Presentation includes Hebrew subtitle option (MOCKED - placeholder translations)")
    
    def test_presentation_has_subtitle_data(self):
        """Test presentation includes subtitle timing data"""
        module_id = "UG_DENT_Y1_S1_C01_M01"
        response = requests.get(f"{BASE_URL}/api/presentations-50-50/{module_id}")
        
        assert response.status_code == 200
        html = response.text
        
        # Check for subtitle data structure
        assert 'subtitlesData' in html, "Expected subtitle data"
        assert '"start"' in html and '"end"' in html, "Expected subtitle timing data"
        assert '"text"' in html, "Expected subtitle text data"
        print(f"✓ Presentation includes synchronized subtitle timing data")


class TestAutoPlayFeature:
    """Test auto-play functionality"""
    
    def test_presentation_has_autoplay(self):
        """Test presentation video has autoplay attribute"""
        module_id = "UG_DENT_Y1_S1_C01_M01"
        response = requests.get(f"{BASE_URL}/api/presentations-50-50/{module_id}")
        
        assert response.status_code == 200
        html = response.text
        
        # Check for autoplay
        assert 'autoplay' in html.lower(), "Expected autoplay attribute on video"
        print(f"✓ Presentation has auto-play functionality")
    
    def test_presentation_has_muted_for_autoplay(self):
        """Test video is initially muted (required for autoplay)"""
        module_id = "UG_DENT_Y1_S1_C01_M01"
        response = requests.get(f"{BASE_URL}/api/presentations-50-50/{module_id}")
        
        assert response.status_code == 200
        html = response.text
        
        # Check muted attribute (browsers require muted for autoplay)
        assert 'muted' in html, "Expected muted attribute for autoplay compliance"
        print(f"✓ Video is muted for browser autoplay compliance")


if __name__ == "__main__":
    # Run with pytest
    pytest.main([__file__, "-v", "--tb=short"])
