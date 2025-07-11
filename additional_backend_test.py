import requests
import json
import uuid
from datetime import datetime

class AdditionalBackendTester:
    def __init__(self):
        # Use production URL from frontend/.env
        try:
            with open('/app/frontend/.env', 'r') as f:
                for line in f:
                    if line.startswith('REACT_APP_BACKEND_URL='):
                        self.base_url = line.split('=', 1)[1].strip()
                        break
        except:
            self.base_url = "https://notion-web3.onrender.com"
        
        self.api_url = f"{self.base_url}/api"
        self.test_wallet = f"0x{uuid.uuid4().hex[:40]}"
        
    def test_endpoint(self, name, method, endpoint, expected_status, data=None):
        """Test a single endpoint"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        print(f"🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            
            success = response.status_code == expected_status
            if success:
                print(f"✅ {name} - Status: {response.status_code}")
                try:
                    return True, response.json()
                except:
                    return True, {}
            else:
                print(f"❌ {name} - Expected {expected_status}, got {response.status_code}")
                return False, {}
                
        except Exception as e:
            print(f"❌ {name} - Error: {str(e)}")
            return False, {}
    
    def test_core_functionality(self):
        """Test the 4 core tasks from test_result.md current_focus"""
        print("🎯 TESTING CORE FUNCTIONALITY - 4 Current Focus Tasks")
        print("="*60)
        
        results = {}
        
        # 1. Core snippet functionality
        print("\n1️⃣ CORE SNIPPET FUNCTIONALITY")
        
        # Extract snippet
        success, data = self.test_endpoint(
            "Web URL Extraction",
            "POST",
            "extract-snippet",
            200,
            {"url": "https://example.com"}
        )
        results['extract_snippet'] = success
        
        if success:
            # AI Summarization
            success2, summary_data = self.test_endpoint(
                "AI Summarization",
                "POST",
                "summarize",
                200,
                {
                    "snippet": data.get("snippet", "Test content"),
                    "title": data.get("title", "Test Title"),
                    "url": "https://example.com",
                    "content_type": "web_snippet"
                }
            )
            results['ai_summarization'] = success2
            
            if success2:
                # Irys blockchain storage
                test_data = {
                    "title": data.get("title", "Test"),
                    "summary": summary_data.get("summary", "Test summary"),
                    "tags": summary_data.get("tags", ["test"]),
                    "network": "devnet"
                }
                
                success3, irys_data = self.test_endpoint(
                    "Irys Blockchain Storage",
                    "POST",
                    "irys-upload",
                    200,
                    {
                        "data": json.dumps(test_data),
                        "signature": f"test-sig-{uuid.uuid4()}",
                        "address": self.test_wallet,
                        "tags": [{"name": "App", "value": "Test"}]
                    }
                )
                results['irys_blockchain'] = success3
                
                if success3:
                    print(f"   ✅ Real Transaction ID: {irys_data.get('id', 'N/A')}")
        
        # 2. Social API endpoints
        print("\n2️⃣ SOCIAL API ENDPOINTS")
        
        # User profiles
        success, _ = self.test_endpoint(
            "User Profile Creation",
            "POST",
            "users/profile",
            200,
            {
                "wallet_address": self.test_wallet,
                "username": f"testuser_{uuid.uuid4().hex[:8]}",
                "bio": "Test user for functionality verification"
            }
        )
        results['user_profiles'] = success
        
        # Follow/unfollow system
        test_wallet_2 = f"0x{uuid.uuid4().hex[:40]}"
        success, _ = self.test_endpoint(
            "Follow System",
            "POST",
            "social/follow",
            200,
            {
                "follower_address": self.test_wallet,
                "following_address": test_wallet_2
            }
        )
        results['follow_system'] = success
        
        # Like system
        success, _ = self.test_endpoint(
            "Like System",
            "POST",
            "social/like",
            200,
            {
                "user_address": self.test_wallet,
                "snippet_id": f"test-snippet-{uuid.uuid4()}"
            }
        )
        results['like_system'] = success
        
        # Comment system
        success, _ = self.test_endpoint(
            "Comment System",
            "POST",
            "social/comment",
            200,
            {
                "user_address": self.test_wallet,
                "snippet_id": f"test-snippet-{uuid.uuid4()}",
                "content": "Test comment for functionality verification"
            }
        )
        results['comment_system'] = success
        
        # Public feed
        success, feed_data = self.test_endpoint(
            "Public Feed",
            "GET",
            "feed/public",
            200
        )
        results['public_feed'] = success
        if success:
            print(f"   ✅ Feed contains {len(feed_data.get('feed', []))} items")
        
        # User discovery
        success, discover_data = self.test_endpoint(
            "User Discovery",
            "GET",
            "users/discover",
            200
        )
        results['user_discovery'] = success
        if success:
            print(f"   ✅ Discovery found {len(discover_data.get('users', []))} users")
        
        # 3. AI mood and theme analysis
        print("\n3️⃣ AI MOOD AND THEME ANALYSIS")
        
        # Text analysis
        success, text_data = self.test_endpoint(
            "Text Analysis with Mood/Theme",
            "POST",
            "process-text",
            200,
            {
                "title": "Beautiful Poetry",
                "content": "The sun sets gently over the horizon, painting the sky in hues of gold and crimson.",
                "content_type": "poetry"
            }
        )
        results['text_analysis'] = success
        if success:
            print(f"   ✅ Mood: {text_data.get('mood', 'N/A')}")
            print(f"   ✅ Theme: {text_data.get('theme', 'N/A')}")
        
        # Image analysis
        test_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        success, image_data = self.test_endpoint(
            "Image Analysis with Mood/Theme",
            "POST",
            "process-image",
            200,
            {
                "title": "Artistic Expression",
                "image_data": test_image,
                "description": "A creative visual representation",
                "content_type": "image"
            }
        )
        results['image_analysis'] = success
        if success:
            print(f"   ✅ Mood: {image_data.get('mood', 'N/A')}")
            print(f"   ✅ Theme: {image_data.get('theme', 'N/A')}")
        
        # 4. Image upload and processing
        print("\n4️⃣ IMAGE UPLOAD AND PROCESSING")
        
        # Complete image workflow
        if results.get('image_analysis'):
            # Upload processed image to blockchain
            image_snippet_data = {
                "title": "Test Image Upload",
                "summary": image_data.get("summary", "Test image"),
                "tags": image_data.get("tags", ["image", "test"]),
                "content_type": "image",
                "mood": image_data.get("mood"),
                "theme": image_data.get("theme"),
                "image_data": test_image,
                "network": "devnet"
            }
            
            success, upload_data = self.test_endpoint(
                "Complete Image Upload Workflow",
                "POST",
                "irys-upload",
                200,
                {
                    "data": json.dumps(image_snippet_data),
                    "signature": f"image-sig-{uuid.uuid4()}",
                    "address": self.test_wallet,
                    "tags": [
                        {"name": "Content-Type", "value": "image"},
                        {"name": "Mood", "value": image_data.get("mood", "")},
                        {"name": "Theme", "value": image_data.get("theme", "")}
                    ]
                }
            )
            results['image_upload_workflow'] = success
            
            if success:
                print(f"   ✅ Image Transaction ID: {upload_data.get('id', 'N/A')}")
                print(f"   ✅ Gateway URL: {upload_data.get('gateway_url', 'N/A')}")
                
                # Save metadata
                success, _ = self.test_endpoint(
                    "Save Image Metadata",
                    "POST",
                    "save-snippet-metadata",
                    200,
                    {
                        "wallet_address": self.test_wallet,
                        "irys_id": upload_data.get('id'),
                        "title": image_snippet_data["title"],
                        "summary": image_snippet_data["summary"],
                        "tags": image_snippet_data["tags"],
                        "network": "devnet",
                        "content_type": "image",
                        "mood": image_snippet_data["mood"],
                        "theme": image_snippet_data["theme"]
                    }
                )
                results['image_metadata_save'] = success
        
        # Print summary
        print("\n" + "="*60)
        print("📊 CORE FUNCTIONALITY TEST RESULTS")
        print("="*60)
        
        total_tests = len(results)
        passed_tests = sum(1 for v in results.values() if v)
        
        print(f"Overall: {passed_tests}/{total_tests} core features working")
        
        for feature, status in results.items():
            status_icon = "✅" if status else "❌"
            print(f"{status_icon} {feature.replace('_', ' ').title()}")
        
        success_rate = (passed_tests / total_tests) * 100
        
        if success_rate == 100:
            print("\n🎉 ALL CORE FUNCTIONALITY WORKING PERFECTLY!")
        elif success_rate >= 90:
            print(f"\n✅ EXCELLENT: {success_rate:.1f}% of core features working")
        elif success_rate >= 80:
            print(f"\n✅ GOOD: {success_rate:.1f}% of core features working")
        else:
            print(f"\n❌ ISSUES: Only {success_rate:.1f}% of core features working")
        
        return passed_tests == total_tests

if __name__ == "__main__":
    tester = AdditionalBackendTester()
    tester.test_core_functionality()