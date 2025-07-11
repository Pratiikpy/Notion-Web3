import requests
import json
import sys
import uuid
from datetime import datetime
import os
import base64

class IrysSnippetVaultTester:
    def __init__(self, base_url=None):
        # Use the local backend URL for testing instead of production
        if base_url is None:
            base_url = "http://localhost:8001"
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        # Generate realistic test data
        self.test_wallet_address_1 = f"0x{uuid.uuid4().hex[:40]}"
        self.test_wallet_address_2 = f"0x{uuid.uuid4().hex[:40]}"
        self.saved_snippet_id = None
        self.test_snippet_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if endpoint else self.api_url
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                if response.content:
                    try:
                        return success, response.json()
                    except:
                        return success, response.content
                return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                if response.content:
                    try:
                        print(f"Response: {response.json()}")
                    except:
                        print(f"Response: {response.content}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test the root API endpoint"""
        return self.run_test(
            "Root API Endpoint",
            "GET",
            "",
            200
        )

    def test_extract_snippet(self, url="https://example.com"):
        """Test the extract-snippet endpoint"""
        return self.run_test(
            "Extract Snippet",
            "POST",
            "extract-snippet",
            200,
            data={"url": url}
        )

    def test_summarize(self, snippet, url, title):
        """Test the summarize endpoint"""
        return self.run_test(
            "Summarize Snippet",
            "POST",
            "summarize",
            200,
            data={
                "snippet": snippet,
                "url": url,
                "title": title
            }
        )

    def test_save_snippet_metadata(self, url, title, summary, tags, network="devnet", wallet_address=None):
        """Test saving snippet metadata"""
        if wallet_address is None:
            wallet_address = self.test_wallet_address_1
        
        snippet_id = f"test-irys-id-{uuid.uuid4()}"
        success, response = self.run_test(
            "Save Snippet Metadata",
            "POST",
            "save-snippet-metadata",
            200,
            data={
                "wallet_address": wallet_address,
                "irys_id": snippet_id,
                "url": url,
                "title": title,
                "summary": summary,
                "tags": tags,
                "network": network
            }
        )
        if success:
            self.test_snippet_id = snippet_id
        return success, response

    def test_get_user_snippets(self, wallet_address=None):
        """Test getting user snippets"""
        if wallet_address is None:
            wallet_address = self.test_wallet_address_1
        return self.run_test(
            "Get User Snippets",
            "GET",
            f"snippets/{wallet_address}",
            200
        )

    # NEW SOCIAL FEATURES TESTS
    
    def test_create_user_profile(self, wallet_address=None, username=None, bio=None):
        """Test creating/updating user profile"""
        if wallet_address is None:
            wallet_address = self.test_wallet_address_1
        if username is None:
            username = f"testuser_{uuid.uuid4().hex[:8]}"
        if bio is None:
            bio = "This is a test user profile for social features testing"
            
        return self.run_test(
            "Create User Profile",
            "POST",
            "users/profile",
            200,
            data={
                "wallet_address": wallet_address,
                "username": username,
                "bio": bio
            }
        )

    def test_get_user_profile(self, wallet_address=None):
        """Test getting user profile"""
        if wallet_address is None:
            wallet_address = self.test_wallet_address_1
        return self.run_test(
            "Get User Profile",
            "GET",
            f"users/{wallet_address}",
            200
        )

    def test_public_feed(self):
        """Test getting public feed"""
        return self.run_test(
            "Get Public Feed",
            "GET",
            "feed/public",
            200,
            params={"skip": 0, "limit": 10}
        )

    def test_discover_users(self):
        """Test user discovery"""
        return self.run_test(
            "Discover Users",
            "GET",
            "users/discover",
            200,
            params={"skip": 0, "limit": 10}
        )

    def test_follow_user(self, follower_address=None, following_address=None):
        """Test following a user"""
        if follower_address is None:
            follower_address = self.test_wallet_address_1
        if following_address is None:
            following_address = self.test_wallet_address_2
            
        return self.run_test(
            "Follow User",
            "POST",
            "social/follow",
            200,
            data={
                "follower_address": follower_address,
                "following_address": following_address
            }
        )

    def test_unfollow_user(self, follower_address=None, following_address=None):
        """Test unfollowing a user"""
        if follower_address is None:
            follower_address = self.test_wallet_address_1
        if following_address is None:
            following_address = self.test_wallet_address_2
            
        return self.run_test(
            "Unfollow User",
            "DELETE",
            f"social/unfollow/{follower_address}/{following_address}",
            200
        )

    def test_like_snippet(self, user_address=None, snippet_id=None):
        """Test liking a snippet"""
        if user_address is None:
            user_address = self.test_wallet_address_1
        if snippet_id is None:
            snippet_id = self.test_snippet_id or f"test-snippet-{uuid.uuid4()}"
            
        return self.run_test(
            "Like Snippet",
            "POST",
            "social/like",
            200,
            data={
                "user_address": user_address,
                "snippet_id": snippet_id
            }
        )

    def test_unlike_snippet(self, user_address=None, snippet_id=None):
        """Test unliking a snippet (toggle functionality)"""
        if user_address is None:
            user_address = self.test_wallet_address_1
        if snippet_id is None:
            snippet_id = self.test_snippet_id or f"test-snippet-{uuid.uuid4()}"
            
        return self.run_test(
            "Unlike Snippet (Toggle)",
            "POST",
            "social/like",
            200,
            data={
                "user_address": user_address,
                "snippet_id": snippet_id
            }
        )

    def test_add_comment(self, user_address=None, snippet_id=None, content=None):
        """Test adding a comment to a snippet"""
        if user_address is None:
            user_address = self.test_wallet_address_1
        if snippet_id is None:
            snippet_id = self.test_snippet_id or f"test-snippet-{uuid.uuid4()}"
        if content is None:
            content = "This is a test comment for the social features testing"
            
        return self.run_test(
            "Add Comment",
            "POST",
            "social/comment",
            200,
            data={
                "user_address": user_address,
                "snippet_id": snippet_id,
                "content": content
            }
        )

    def test_get_comments(self, snippet_id=None):
        """Test getting comments for a snippet"""
        if snippet_id is None:
            snippet_id = self.test_snippet_id or f"test-snippet-{uuid.uuid4()}"
            
        return self.run_test(
            "Get Comments",
            "GET",
            f"social/comments/{snippet_id}",
            200
        )

    # NEW ENHANCED CONTENT CREATION TESTS
    
    def test_process_text_content(self, content_type="text"):
        """Test processing text/poetry content with AI analysis"""
        test_content = {
            "text": "This is a beautiful day to explore new technologies and create amazing applications.",
            "poetry": "Roses are red, violets are blue, testing APIs is what we do, making sure they work for me and you.",
            "quote": "The only way to do great work is to love what you do. - Steve Jobs"
        }
        
        return self.run_test(
            f"Process {content_type.title()} Content",
            "POST",
            "process-text",
            200,
            data={
                "title": f"Test {content_type.title()}",
                "content": test_content.get(content_type, test_content["text"]),
                "content_type": content_type
            }
        )

    def test_process_image_content(self):
        """Test processing image content with AI description"""
        # Create a simple base64 encoded test image (1x1 pixel PNG)
        test_image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        
        return self.run_test(
            "Process Image Content",
            "POST",
            "process-image",
            200,
            data={
                "title": "Test Image Upload",
                "image_data": test_image_base64,
                "description": "A test image for API validation",
                "content_type": "image"
            }
        )

    def test_enhanced_summarize(self, content_type="web_snippet"):
        """Test enhanced summarize endpoint with different content types"""
        test_data = {
            "web_snippet": {
                "snippet": "This is a comprehensive guide to building modern web applications using React and FastAPI.",
                "url": "https://example.com/web-dev-guide",
                "title": "Modern Web Development Guide"
            },
            "text": {
                "content": "Today I learned about the importance of testing in software development. It's crucial for maintaining code quality.",
                "title": "Learning About Testing"
            },
            "poetry": {
                "content": "In the realm of code and dreams, where logic meets art, we craft digital symphonies, each function a part.",
                "title": "Digital Symphony"
            }
        }
        
        data = test_data.get(content_type, test_data["web_snippet"])
        data["content_type"] = content_type
        
        return self.run_test(
            f"Enhanced Summarize ({content_type})",
            "POST",
            "summarize",
            200,
            data=data
        )

    def test_irys_upload_simulation(self):
        """Test Irys blockchain upload with realistic data"""
        # Create test data that would be uploaded to Irys
        test_data = {
            "title": "Test Blockchain Upload",
            "summary": "Testing the Irys blockchain integration with real data",
            "tags": ["blockchain", "irys", "test"],
            "content_type": "text",
            "network": "devnet",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Simulate the data that would be sent to Irys
        irys_data = {
            "data": json.dumps(test_data),
            "signature": f"test-signature-{uuid.uuid4()}",
            "address": self.test_wallet_address_1,
            "tags": [
                {"name": "Content-Type", "value": "application/json"},
                {"name": "App-Name", "value": "IrysSnippetVault"},
                {"name": "Version", "value": "1.0"}
            ]
        }
        
        return self.run_test(
            "Irys Blockchain Upload",
            "POST",
            "irys-upload",
            200,
            data=irys_data
        )

    def test_irys_query(self, wallet_address=None):
        """Test querying Irys blockchain for user snippets"""
        if wallet_address is None:
            wallet_address = self.test_wallet_address_1
            
        return self.run_test(
            "Query Irys Blockchain",
            "GET",
            f"irys-query/{wallet_address}",
            200
        )

    def test_full_image_workflow(self):
        """Test the complete image upload workflow"""
        print("\n🖼️ Testing Complete Image Upload Workflow...")
        
        # Step 1: Process image content
        success1, image_response = self.test_process_image_content()
        if not success1:
            print("❌ Image processing failed")
            return False, {}
        
        print("✅ Step 1: Image processing successful")
        
        # Step 2: Create enhanced snippet data with image
        test_image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        
        snippet_data = {
            "title": "Beautiful Sunset Photo",
            "summary": image_response.get("summary", "A beautiful image captured and stored on blockchain"),
            "tags": image_response.get("tags", ["image", "photo", "memory"]),
            "content_type": "image",
            "mood": image_response.get("mood", "peaceful"),
            "theme": image_response.get("theme", "nature"),
            "image_data": test_image_base64,
            "network": "devnet",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Step 3: Upload to Irys blockchain
        irys_upload_data = {
            "data": json.dumps(snippet_data),
            "signature": f"image-signature-{uuid.uuid4()}",
            "address": self.test_wallet_address_1,
            "tags": [
                {"name": "Content-Type", "value": "application/json"},
                {"name": "App-Name", "value": "IrysSnippetVault"},
                {"name": "Data-Type", "value": "image"},
                {"name": "Mood", "value": snippet_data["mood"]},
                {"name": "Theme", "value": snippet_data["theme"]}
            ]
        }
        
        success2, irys_response = self.run_test(
            "Upload Image to Irys Blockchain",
            "POST",
            "irys-upload",
            200,
            data=irys_upload_data
        )
        
        if not success2:
            print("❌ Irys blockchain upload failed")
            return False, {}
        
        print("✅ Step 2: Blockchain upload successful")
        print(f"   Transaction ID: {irys_response.get('id', 'N/A')}")
        print(f"   Gateway URL: {irys_response.get('gateway_url', 'N/A')}")
        
        # Step 4: Save metadata to database
        if irys_response.get('id'):
            success3, metadata_response = self.run_test(
                "Save Image Metadata",
                "POST",
                "save-snippet-metadata",
                200,
                data={
                    "wallet_address": self.test_wallet_address_1,
                    "irys_id": irys_response['id'],
                    "title": snippet_data["title"],
                    "summary": snippet_data["summary"],
                    "tags": snippet_data["tags"],
                    "network": "devnet",
                    "content_type": "image",
                    "mood": snippet_data["mood"],
                    "theme": snippet_data["theme"]
                }
            )
            
            if success3:
                print("✅ Step 3: Metadata saved successfully")
                print("🎉 Complete image workflow successful!")
                return True, {
                    "image_processing": image_response,
                    "blockchain_upload": irys_response,
                    "metadata_save": metadata_response
                }
            else:
                print("❌ Step 3: Metadata save failed")
                return False, {}
        
        return False, {}

    def test_error_handling(self):
        """Test error handling and edge cases"""
        print("\n🚨 Testing Error Handling and Edge Cases...")
        
        # Test invalid image data
        invalid_image_test = self.run_test(
            "Invalid Image Data",
            "POST",
            "process-image",
            500,  # Expecting error
            data={
                "title": "Invalid Image",
                "image_data": "invalid-base64-data",
                "content_type": "image"
            }
        )
        
        # Test empty content
        empty_content_test = self.run_test(
            "Empty Text Content",
            "POST",
            "process-text",
            500,  # Expecting error
            data={
                "title": "",
                "content": "",
                "content_type": "text"
            }
        )
        
        # Test invalid wallet address for Irys query
        invalid_wallet_test = self.run_test(
            "Invalid Wallet Query",
            "GET",
            "irys-query/invalid-wallet-address",
            200  # Should return empty results, not error
        )
        
        return True

    def test_api_routing_fix(self):
        """Test the specific API routing fix - NO MORE double /api/api/ prefix"""
        print("\n🔧 TESTING API ROUTING FIX - Critical Double Prefix Issue")
        print("="*60)
        
        routing_tests_passed = 0
        routing_tests_total = 5
        
        # Test 1: /api/health endpoint (basic connectivity)
        print("\n1️⃣ Testing /api/health endpoint...")
        success, response = self.run_test(
            "Health Check Endpoint",
            "GET",
            "health",
            200
        )
        if success:
            routing_tests_passed += 1
            print("✅ /api/health working - NO 404 errors")
        else:
            print("❌ /api/health failed - API routing issue detected")
        
        # Test 2: /api/extract-snippet endpoint (POST)
        print("\n2️⃣ Testing /api/extract-snippet endpoint...")
        success, response = self.run_test(
            "Extract Snippet Endpoint",
            "POST",
            "extract-snippet",
            200,
            data={"url": "https://example.com"}
        )
        if success:
            routing_tests_passed += 1
            print("✅ /api/extract-snippet working - NO 404/405 errors")
        else:
            print("❌ /api/extract-snippet failed - API routing issue detected")
        
        # Test 3: /api/feed/public endpoint (GET)
        print("\n3️⃣ Testing /api/feed/public endpoint...")
        success, response = self.run_test(
            "Public Feed Endpoint",
            "GET",
            "feed/public",
            200
        )
        if success:
            routing_tests_passed += 1
            print("✅ /api/feed/public working - NO 404/405 errors")
        else:
            print("❌ /api/feed/public failed - API routing issue detected")
        
        # Test 4: /api/users/discover endpoint (GET)
        print("\n4️⃣ Testing /api/users/discover endpoint...")
        success, response = self.run_test(
            "User Discovery Endpoint",
            "GET",
            "users/discover",
            200
        )
        if success:
            routing_tests_passed += 1
            print("✅ /api/users/discover working - NO 404/405 errors")
        else:
            print("❌ /api/users/discover failed - API routing issue detected")
        
        # Test 5: /api/irys-query/{address} endpoint (GET)
        print("\n5️⃣ Testing /api/irys-query/{address} endpoint...")
        success, response = self.run_test(
            "Irys Query Endpoint",
            "GET",
            f"irys-query/{self.test_wallet_address_1}",
            200
        )
        if success:
            routing_tests_passed += 1
            print("✅ /api/irys-query/{address} working - NO 404/405 errors")
        else:
            print("❌ /api/irys-query/{address} failed - API routing issue detected")
        
        # Summary of routing fix test
        print("\n" + "="*60)
        print(f"🔧 API ROUTING FIX RESULTS: {routing_tests_passed}/{routing_tests_total} endpoints working")
        print("="*60)
        
        if routing_tests_passed == routing_tests_total:
            print("🎉 API ROUTING FIX SUCCESSFUL!")
            print("✅ NO MORE double /api/api/ prefix issues")
            print("✅ All critical endpoints responding correctly")
            print("✅ Frontend can now communicate with backend properly")
        else:
            failed_routing = routing_tests_total - routing_tests_passed
            print(f"❌ API ROUTING ISSUES DETECTED: {failed_routing} endpoints failing")
            print("❌ Double prefix /api/api/ issue may still exist")
            print("❌ Frontend-backend communication may be broken")
        
        return routing_tests_passed == routing_tests_total

    def run_all_tests(self):
        """Run all API tests in sequence"""
        print("🚀 Starting Irys Snippet Vault API Tests with Enhanced Content Creation")
        
        # PRIORITY: Test API routing fix first (as requested in review)
        print("\n🚨 PRIORITY TEST: API Routing Fix Verification")
        routing_fix_success = self.test_api_routing_fix()
        
        if not routing_fix_success:
            print("\n❌ CRITICAL: API routing fix failed - this is the main issue reported by user")
            print("❌ Stopping comprehensive tests due to routing failure")
            print(f"📊 ROUTING FIX TEST RESULTS: FAILED")
            return False
        
        print("\n✅ API routing fix verified - continuing with comprehensive tests...")
        
        # Test root endpoint
        self.test_root_endpoint()
        
        # Test extract snippet
        success, extract_data = self.test_extract_snippet()
        if not success or not extract_data:
            print("❌ Extract snippet test failed, cannot continue with dependent tests")
            return
        
        # Test summarize
        success, summarize_data = self.test_summarize(
            extract_data.get("snippet", "Example snippet text for testing"),
            extract_data.get("url", "https://example.com"),
            extract_data.get("title", "Example Title")
        )
        if not success or not summarize_data:
            print("❌ Summarize test failed, cannot continue with dependent tests")
            return
        
        # Test save snippet metadata
        success, metadata = self.test_save_snippet_metadata(
            extract_data.get("url", "https://example.com"),
            extract_data.get("title", "Example Title"),
            summarize_data.get("summary", "Example summary"),
            summarize_data.get("tags", ["tag1", "tag2", "tag3"])
        )
        if not success:
            print("❌ Save snippet metadata test failed")
        
        # Test get user snippets
        success, snippets_data = self.test_get_user_snippets()
        if success:
            # Verify the saved snippet is in the returned data
            if snippets_data and "snippets" in snippets_data:
                if len(snippets_data["snippets"]) > 0:
                    print(f"✅ Found {len(snippets_data['snippets'])} snippets for the test wallet")
                else:
                    print("⚠️ No snippets found for the test wallet")

        print("\n" + "="*60)
        print("🎨 TESTING ENHANCED CONTENT CREATION FEATURES")
        print("="*60)

        # Test text content processing
        print("\n📝 Testing AI Text Analysis...")
        self.test_process_text_content("text")
        self.test_process_text_content("poetry")
        self.test_process_text_content("quote")
        
        # Test enhanced summarize with different content types
        print("\n🤖 Testing Enhanced AI Summarization...")
        self.test_enhanced_summarize("web_snippet")
        self.test_enhanced_summarize("text")
        self.test_enhanced_summarize("poetry")
        
        # Test image processing
        print("\n🖼️ Testing Image Processing...")
        self.test_process_image_content()
        
        # Test Irys blockchain integration
        print("\n⛓️ Testing Irys Blockchain Integration...")
        irys_success, irys_response = self.test_irys_upload_simulation()
        if irys_success:
            print("✅ Irys blockchain upload working")
            # Test querying after upload
            self.test_irys_query()
        else:
            print("❌ Irys blockchain upload failed")
        
        # Test complete image workflow
        print("\n🔄 Testing Complete Image Upload Workflow...")
        workflow_success, workflow_data = self.test_full_image_workflow()
        if workflow_success:
            print("🎉 Complete image workflow successful!")
        else:
            print("❌ Image workflow failed")
        
        # Test error handling
        self.test_error_handling()

        print("\n" + "="*60)
        print("🧑‍🤝‍🧑 TESTING SOCIAL FEATURES")
        print("="*60)

        # Test user profile creation for both test users
        print("\n📝 Testing User Profile Management...")
        success1, profile1 = self.test_create_user_profile(
            self.test_wallet_address_1, 
            "alice_crypto", 
            "Crypto enthusiast and snippet collector"
        )
        success2, profile2 = self.test_create_user_profile(
            self.test_wallet_address_2, 
            "bob_developer", 
            "Full-stack developer sharing code snippets"
        )
        
        # Test getting user profiles
        self.test_get_user_profile(self.test_wallet_address_1)
        self.test_get_user_profile(self.test_wallet_address_2)

        # Test social interactions
        print("\n👥 Testing Social Interactions...")
        
        # Test follow functionality
        follow_success, follow_response = self.test_follow_user()
        if follow_success:
            print("✅ Follow functionality working")
            
            # Test follow again (should return already following message)
            self.test_follow_user()
            
            # Test unfollow
            unfollow_success, unfollow_response = self.test_unfollow_user()
            if unfollow_success:
                print("✅ Unfollow functionality working")

        # Test like functionality
        print("\n❤️ Testing Like System...")
        if self.test_snippet_id:
            like_success, like_response = self.test_like_snippet()
            if like_success:
                print("✅ Like functionality working")
                
                # Test unlike (toggle functionality)
                unlike_success, unlike_response = self.test_unlike_snippet()
                if unlike_success:
                    print("✅ Unlike (toggle) functionality working")

        # Test comment system
        print("\n💬 Testing Comment System...")
        if self.test_snippet_id:
            comment_success, comment_response = self.test_add_comment()
            if comment_success:
                print("✅ Comment creation working")
                
                # Test getting comments
                get_comments_success, comments_data = self.test_get_comments()
                if get_comments_success:
                    if comments_data and "comments" in comments_data:
                        print(f"✅ Found {len(comments_data['comments'])} comments")
                    else:
                        print("⚠️ No comments found")

        # Test feed and discovery
        print("\n🌐 Testing Feed and Discovery...")
        
        # Test public feed
        feed_success, feed_data = self.test_public_feed()
        if feed_success:
            if feed_data and "feed" in feed_data:
                print(f"✅ Public feed working - {len(feed_data['feed'])} items")
            else:
                print("⚠️ Public feed empty")

        # Test user discovery
        discover_success, discover_data = self.test_discover_users()
        if discover_success:
            if discover_data and "users" in discover_data:
                print(f"✅ User discovery working - {len(discover_data['users'])} users")
            else:
                print("⚠️ No users found in discovery")

        # Print summary
        print("\n" + "="*60)
        print(f"📊 FINAL TEST RESULTS: {self.tests_passed}/{self.tests_run} tests passed")
        print("="*60)
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL TESTS PASSED! Enhanced content creation and social features are working correctly.")
        else:
            failed_tests = self.tests_run - self.tests_passed
            print(f"⚠️ {failed_tests} tests failed. Check the output above for details.")
        
        return self.tests_passed == self.tests_run

def main():
    tester = IrysSnippetVaultTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())