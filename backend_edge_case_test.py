import requests
import json
import sys
import uuid

class EdgeCaseTests:
    def __init__(self):
        self.base_url = "https://f0c3a356-7eed-4148-b03d-09fcdaab0dad.preview.emergentagent.com"
        self.api_url = f"{self.base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if endpoint else self.api_url
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json()
                except:
                    return success, response.content
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    print(f"Response: {response.json()}")
                except:
                    print(f"Response: {response.content}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_invalid_wallet_address(self):
        """Test with invalid wallet address"""
        return self.run_test(
            "Get Profile with Invalid Wallet",
            "GET",
            "users/invalid-wallet-address",
            200  # Should return basic profile even for non-existent wallet
        )

    def test_nonexistent_snippet_comments(self):
        """Test getting comments for non-existent snippet"""
        return self.run_test(
            "Get Comments for Non-existent Snippet",
            "GET",
            "social/comments/non-existent-snippet-id",
            200  # Should return empty comments array
        )

    def test_duplicate_follow(self):
        """Test following the same user twice"""
        wallet1 = f"0x{uuid.uuid4().hex[:40]}"
        wallet2 = f"0x{uuid.uuid4().hex[:40]}"
        
        # First follow
        success1, _ = self.run_test(
            "First Follow",
            "POST",
            "social/follow",
            200,
            data={"follower_address": wallet1, "following_address": wallet2}
        )
        
        # Second follow (duplicate)
        success2, response2 = self.run_test(
            "Duplicate Follow",
            "POST",
            "social/follow",
            200,
            data={"follower_address": wallet1, "following_address": wallet2}
        )
        
        return success1 and success2

    def test_unfollow_nonexistent(self):
        """Test unfollowing a user that was never followed"""
        wallet1 = f"0x{uuid.uuid4().hex[:40]}"
        wallet2 = f"0x{uuid.uuid4().hex[:40]}"
        
        return self.run_test(
            "Unfollow Non-existent Relationship",
            "DELETE",
            f"social/unfollow/{wallet1}/{wallet2}",
            200  # Should handle gracefully
        )

    def test_empty_comment(self):
        """Test adding empty comment"""
        return self.run_test(
            "Add Empty Comment",
            "POST",
            "social/comment",
            200,  # Should accept empty comments
            data={
                "user_address": f"0x{uuid.uuid4().hex[:40]}",
                "snippet_id": f"test-snippet-{uuid.uuid4()}",
                "content": ""
            }
        )

    def run_edge_case_tests(self):
        """Run all edge case tests"""
        print("🧪 Starting Edge Case Tests for Social Features")
        
        self.test_invalid_wallet_address()
        self.test_nonexistent_snippet_comments()
        self.test_duplicate_follow()
        self.test_unfollow_nonexistent()
        self.test_empty_comment()
        
        print(f"\n📊 Edge Case Tests: {self.tests_passed}/{self.tests_run} passed")
        return self.tests_passed == self.tests_run

def main():
    tester = EdgeCaseTests()
    success = tester.run_edge_case_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())