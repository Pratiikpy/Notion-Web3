import requests
import json
import uuid

class DatabaseIntegrationTest:
    def __init__(self):
        self.base_url = "https://0bb6025e-e237-45ce-a098-51a15829f3a6.preview.emergentagent.com"
        self.api_url = f"{self.base_url}/api"
        self.wallet1 = f"0x{uuid.uuid4().hex[:40]}"
        self.wallet2 = f"0x{uuid.uuid4().hex[:40]}"

    def create_profile(self, wallet_address, username):
        """Create a user profile"""
        response = requests.post(f"{self.api_url}/users/profile", json={
            "wallet_address": wallet_address,
            "username": username,
            "bio": f"Test user {username}"
        })
        return response.status_code == 200, response.json() if response.status_code == 200 else {}

    def get_profile(self, wallet_address):
        """Get user profile"""
        response = requests.get(f"{self.api_url}/users/{wallet_address}")
        return response.status_code == 200, response.json() if response.status_code == 200 else {}

    def follow_user(self, follower, following):
        """Follow a user"""
        response = requests.post(f"{self.api_url}/social/follow", json={
            "follower_address": follower,
            "following_address": following
        })
        return response.status_code == 200

    def unfollow_user(self, follower, following):
        """Unfollow a user"""
        response = requests.delete(f"{self.api_url}/social/unfollow/{follower}/{following}")
        return response.status_code == 200

    def test_follow_counter_updates(self):
        """Test that follow/unfollow updates counters correctly"""
        print("🧪 Testing Follow Counter Updates...")
        
        # Create two test profiles
        success1, profile1 = self.create_profile(self.wallet1, "follower_user")
        success2, profile2 = self.create_profile(self.wallet2, "followed_user")
        
        if not (success1 and success2):
            print("❌ Failed to create test profiles")
            return False
        
        # Get initial counts
        _, initial_follower = self.get_profile(self.wallet1)
        _, initial_following = self.get_profile(self.wallet2)
        
        initial_follower_following_count = initial_follower.get("following_count", 0)
        initial_following_followers_count = initial_following.get("followers_count", 0)
        
        print(f"Initial counts - Follower following: {initial_follower_following_count}, Following followers: {initial_following_followers_count}")
        
        # Follow user
        if not self.follow_user(self.wallet1, self.wallet2):
            print("❌ Failed to follow user")
            return False
        
        # Check updated counts
        _, updated_follower = self.get_profile(self.wallet1)
        _, updated_following = self.get_profile(self.wallet2)
        
        new_follower_following_count = updated_follower.get("following_count", 0)
        new_following_followers_count = updated_following.get("followers_count", 0)
        
        print(f"After follow - Follower following: {new_follower_following_count}, Following followers: {new_following_followers_count}")
        
        # Verify counts increased
        if (new_follower_following_count != initial_follower_following_count + 1 or
            new_following_followers_count != initial_following_followers_count + 1):
            print("❌ Follow counters not updated correctly")
            return False
        
        # Unfollow user
        if not self.unfollow_user(self.wallet1, self.wallet2):
            print("❌ Failed to unfollow user")
            return False
        
        # Check counts after unfollow
        _, final_follower = self.get_profile(self.wallet1)
        _, final_following = self.get_profile(self.wallet2)
        
        final_follower_following_count = final_follower.get("following_count", 0)
        final_following_followers_count = final_following.get("followers_count", 0)
        
        print(f"After unfollow - Follower following: {final_follower_following_count}, Following followers: {final_following_followers_count}")
        
        # Verify counts decreased back to original
        if (final_follower_following_count != initial_follower_following_count or
            final_following_followers_count != initial_following_followers_count):
            print("❌ Unfollow counters not updated correctly")
            return False
        
        print("✅ Follow/Unfollow counter updates working correctly")
        return True

    def test_like_toggle_functionality(self):
        """Test like/unlike toggle functionality"""
        print("🧪 Testing Like Toggle Functionality...")
        
        snippet_id = f"test-snippet-{uuid.uuid4()}"
        
        # First like
        response1 = requests.post(f"{self.api_url}/social/like", json={
            "user_address": self.wallet1,
            "snippet_id": snippet_id
        })
        
        if response1.status_code != 200:
            print("❌ Failed to like snippet")
            return False
        
        result1 = response1.json()
        if not result1.get("liked", False):
            print("❌ First like should return liked: true")
            return False
        
        # Second like (should unlike)
        response2 = requests.post(f"{self.api_url}/social/like", json={
            "user_address": self.wallet1,
            "snippet_id": snippet_id
        })
        
        if response2.status_code != 200:
            print("❌ Failed to unlike snippet")
            return False
        
        result2 = response2.json()
        if result2.get("liked", True):
            print("❌ Second like should return liked: false (unlike)")
            return False
        
        print("✅ Like/Unlike toggle functionality working correctly")
        return True

    def run_database_tests(self):
        """Run all database integration tests"""
        print("🗄️ Starting Database Integration Tests")
        
        test1_passed = self.test_follow_counter_updates()
        test2_passed = self.test_like_toggle_functionality()
        
        total_tests = 2
        passed_tests = sum([test1_passed, test2_passed])
        
        print(f"\n📊 Database Integration Tests: {passed_tests}/{total_tests} passed")
        
        if passed_tests == total_tests:
            print("🎉 All database integration tests passed!")
        else:
            print("⚠️ Some database integration tests failed")
        
        return passed_tests == total_tests

def main():
    tester = DatabaseIntegrationTest()
    success = tester.run_database_tests()
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())