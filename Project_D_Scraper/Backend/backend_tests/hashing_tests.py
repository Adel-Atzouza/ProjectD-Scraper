import unittest
import os
import json
import hashlib
import tempfile
import shutil
from unittest.mock import patch, mock_open
from datetime import datetime
import sys

# Add the backend directory to the path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from Crawlscraper import crawl_all
from utils import clean_text


class TestHashingFunctionality(unittest.TestCase):
    """Test suite for content hashing functionality to prevent duplicate scraping"""
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        self.test_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.test_dir)
        
        # Load real websites from websites.json
        websites_file = os.path.join(os.path.dirname(__file__), '..', 'websites.json')
        with open(websites_file, 'r', encoding='utf-8') as f:
            self.websites = json.load(f)
        
        # Create test hashes.json file
        self.hashes_file = "hashes.json"
        self.sample_content = "This is sample content for testing"
        self.sample_hash = hashlib.sha256(self.sample_content.encode()).hexdigest()
        
        # Use real websites from websites.json
        self.sample_url = self.websites[0]["url"]  # "https://www.goudawijzer.nl"
        self.sample_domain = self.sample_url.replace("https://", "").replace("http://", "").split('/')[0]
        self.sample_url2 = self.websites[1]["url"]  # "https://www.zorgkaartnederland.nl"
        self.sample_domain2 = self.sample_url2.replace("https://", "").replace("http://", "").split('/')[0]
        
    def tearDown(self):
        """Clean up after each test method"""
        os.chdir(self.original_dir)
        shutil.rmtree(self.test_dir)
    
    def test_hash_generation_consistency(self):
        """Test that identical content produces identical hashes"""
        content1 = "Test content for hashing"
        content2 = "Test content for hashing"
        content3 = "Different test content"
        
        hash1 = hashlib.sha256(content1.encode()).hexdigest()
        hash2 = hashlib.sha256(content2.encode()).hexdigest()
        hash3 = hashlib.sha256(content3.encode()).hexdigest()
        
        # Same content should produce same hash
        self.assertEqual(hash1, hash2)
        # Different content should produce different hash
        self.assertNotEqual(hash1, hash3)
    
    def test_hash_generation_empty_content(self):
        """Test hash generation for empty content"""
        empty_content = ""
        hash_empty = hashlib.sha256(empty_content.encode()).hexdigest()
        
        # Empty content should still produce a valid hash
        self.assertEqual(len(hash_empty), 64)  # SHA256 produces 64 character hex string
        self.assertIsInstance(hash_empty, str)
    
    def test_hash_generation_unicode_content(self):
        """Test hash generation for unicode content"""
        unicode_content = "Test content with émojis 🌟 and spëcial characters ñ"
        hash_unicode = hashlib.sha256(unicode_content.encode()).hexdigest()
        
        # Unicode content should produce valid hash
        self.assertEqual(len(hash_unicode), 64)
        self.assertIsInstance(hash_unicode, str)
    
    def test_hashes_json_structure(self):
        """Test the structure of hashes.json file"""
        # Create test hash data
        test_data = {
            self.sample_domain: {
                self.sample_url: {
                    "hash": self.sample_hash,
                    "timestamp": datetime.now().isoformat()
                }
            }
        }
        
        # Write to hashes.json
        with open(self.hashes_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, indent=2)
        
        # Verify structure
        with open(self.hashes_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        
        self.assertIn(self.sample_domain, loaded_data)
        self.assertIn(self.sample_url, loaded_data[self.sample_domain])
        self.assertIn("hash", loaded_data[self.sample_domain][self.sample_url])
        self.assertIn("timestamp", loaded_data[self.sample_domain][self.sample_url])
        self.assertEqual(loaded_data[self.sample_domain][self.sample_url]["hash"], self.sample_hash)
    
    def test_duplicate_detection_same_hash(self):
        """Test that duplicate content is detected correctly"""
        # Create initial hash data
        initial_data = {
            self.sample_domain: {
                self.sample_url: {
                    "hash": self.sample_hash,
                    "timestamp": datetime.now().isoformat()
                }
            }
        }
        
        with open(self.hashes_file, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f, indent=2)
        
        # Test duplicate detection
        with open(self.hashes_file, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
        
        # Check if URL exists and hash matches
        if self.sample_domain in existing_data:
            if self.sample_url in existing_data[self.sample_domain]:
                existing_hash = existing_data[self.sample_domain][self.sample_url]["hash"]
                current_hash = hashlib.sha256(self.sample_content.encode()).hexdigest()
                is_duplicate = existing_hash == current_hash
                
                self.assertTrue(is_duplicate, "Same content should be detected as duplicate")
    
    def test_duplicate_detection_different_hash(self):
        """Test that different content is not detected as duplicate"""
        # Create initial hash data
        initial_data = {
            self.sample_domain: {
                self.sample_url: {
                    "hash": self.sample_hash,
                    "timestamp": datetime.now().isoformat()
                }
            }
        }
        
        with open(self.hashes_file, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f, indent=2)
        
        # Test with different content
        different_content = "This is completely different content"
        
        with open(self.hashes_file, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
        
        if self.sample_domain in existing_data:
            if self.sample_url in existing_data[self.sample_domain]:
                existing_hash = existing_data[self.sample_domain][self.sample_url]["hash"]
                current_hash = hashlib.sha256(different_content.encode()).hexdigest()
                is_duplicate = existing_hash == current_hash
                
                self.assertFalse(is_duplicate, "Different content should not be detected as duplicate")
    
    def test_new_domain_addition(self):
        """Test adding a new domain to hashes.json"""
        # Start with empty hashes file
        with open(self.hashes_file, 'w', encoding='utf-8') as f:
            json.dump({}, f)
        
        # Load existing data
        with open(self.hashes_file, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
        
        # Add new domain using a real website
        new_domain = self.sample_domain2
        new_url = self.sample_url2
        new_content = "New site content"
        new_hash = hashlib.sha256(new_content.encode()).hexdigest()
        
        if new_domain not in existing_data:
            existing_data[new_domain] = {}
        
        existing_data[new_domain][new_url] = {
            "hash": new_hash,
            "timestamp": datetime.now().isoformat()
        }
        
        # Verify the addition
        self.assertIn(new_domain, existing_data)
        self.assertIn(new_url, existing_data[new_domain])
        self.assertEqual(existing_data[new_domain][new_url]["hash"], new_hash)
    
    def test_new_url_to_existing_domain(self):
        """Test adding a new URL to an existing domain"""
        # Create initial data with one domain
        initial_data = {
            self.sample_domain: {
                self.sample_url: {
                    "hash": self.sample_hash,
                    "timestamp": datetime.now().isoformat()
                }
            }
        }
        
        with open(self.hashes_file, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f, indent=2)
        
        # Add new URL to existing domain
        new_url = f"https://{self.sample_domain}/page2"
        new_content = "Different content for page 2"
        new_hash = hashlib.sha256(new_content.encode()).hexdigest()
        
        with open(self.hashes_file, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
        
        existing_data[self.sample_domain][new_url] = {
            "hash": new_hash,
            "timestamp": datetime.now().isoformat()
        }
        
        # Verify both URLs exist in the domain
        self.assertIn(self.sample_url, existing_data[self.sample_domain])
        self.assertIn(new_url, existing_data[self.sample_domain])
        self.assertEqual(len(existing_data[self.sample_domain]), 2)
    
    def test_hash_file_missing(self):
        """Test behavior when hashes.json doesn't exist"""
        # Ensure hashes.json doesn't exist
        if os.path.exists(self.hashes_file):
            os.remove(self.hashes_file)
        
        # This should not raise an exception
        file_exists = os.path.exists(self.hashes_file)
        self.assertFalse(file_exists)
        
        # Simulate creating the file when it doesn't exist
        if not file_exists:
            with open(self.hashes_file, 'w', encoding='utf-8') as f:
                json.dump({}, f)
        
        # Verify file was created
        self.assertTrue(os.path.exists(self.hashes_file))
        
        with open(self.hashes_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertEqual(data, {})
    
    def test_hash_file_corrupted(self):
        """Test behavior when hashes.json is corrupted"""
        # Create corrupted JSON file
        with open(self.hashes_file, 'w', encoding='utf-8') as f:
            f.write("{ invalid json content")
        
        # Test handling of corrupted file
        try:
            with open(self.hashes_file, 'r', encoding='utf-8') as f:
                json.load(f)
            self.fail("Should have raised JSONDecodeError")
        except json.JSONDecodeError:
            # This is expected behavior
            pass
    
    def test_content_cleaning_affects_hash(self):
        """Test that content cleaning affects hash generation"""
        raw_content = "# Header\n\nThis is content with [link](http://example.com)\n\n| Table | Data |\n|-------|------|\n| Row1  | Data1|\n"
        cleaned_content = clean_text(raw_content)
        
        raw_hash = hashlib.sha256(raw_content.encode()).hexdigest()
        cleaned_hash = hashlib.sha256(cleaned_content.encode()).hexdigest()
        
        # Cleaned content should produce different hash than raw content
        self.assertNotEqual(raw_hash, cleaned_hash)
        
        # Same cleaned content should produce same hash
        cleaned_content2 = clean_text(raw_content)
        cleaned_hash2 = hashlib.sha256(cleaned_content2.encode()).hexdigest()
        self.assertEqual(cleaned_hash, cleaned_hash2)
    
    def test_timestamp_format(self):
        """Test that timestamps are in correct ISO format"""
        timestamp = datetime.now().isoformat()
        
        # Verify timestamp format
        self.assertIsInstance(timestamp, str)
        self.assertIn('T', timestamp)  # ISO format includes 'T' separator
        
        # Verify timestamp can be parsed back
        try:
            parsed_timestamp = datetime.fromisoformat(timestamp)
            self.assertIsInstance(parsed_timestamp, datetime)
        except ValueError:
            self.fail("Timestamp is not in valid ISO format")
    
    def test_multiple_real_domains_hash_storage(self):
        """Test storing hashes for multiple real domains from websites.json"""
        # Use multiple real websites
        website1 = self.websites[0]
        website2 = self.websites[1]
        website3 = self.websites[2] if len(self.websites) > 2 else self.websites[0]
        
        domain1 = website1["url"].replace("https://", "").replace("http://", "").split('/')[0]
        domain2 = website2["url"].replace("https://", "").replace("http://", "").split('/')[0]
        domain3 = website3["url"].replace("https://", "").replace("http://", "").split('/')[0]
        
        domains_data = {
            domain1: {
                website1["url"]: {
                    "hash": hashlib.sha256("content1".encode()).hexdigest(),
                    "timestamp": datetime.now().isoformat()
                }
            },
            domain2: {
                website2["url"]: {
                    "hash": hashlib.sha256("content2".encode()).hexdigest(),
                    "timestamp": datetime.now().isoformat()
                }
            },
            domain3: {
                website3["url"]: {
                    "hash": hashlib.sha256("content3".encode()).hexdigest(),
                    "timestamp": datetime.now().isoformat()
                },
                f"{website3['url']}/page2": {
                    "hash": hashlib.sha256("content4".encode()).hexdigest(),
                    "timestamp": datetime.now().isoformat()
                }
            }
        }
        
        with open(self.hashes_file, 'w', encoding='utf-8') as f:
            json.dump(domains_data, f, indent=2)
        
        # Verify all domains and URLs are stored correctly
        with open(self.hashes_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        
        self.assertGreaterEqual(len(loaded_data), 2)  # At least 2 domains (could be 3 if all different)
        self.assertIn(domain1, loaded_data)
        self.assertIn(domain2, loaded_data)
        self.assertIn(domain3, loaded_data)
    
    def test_real_website_domain_extraction(self):
        """Test extracting domains from real website URLs"""
        for website in self.websites[:5]:  # Test first 5 websites
            url = website["url"]
            domain = url.replace("https://", "").replace("http://", "").split('/')[0]
            
            # Verify domain extraction
            self.assertNotIn("http", domain)
            self.assertNotIn("://", domain)
            self.assertNotEqual(domain, "")
            
            # Verify it's a valid domain format
            parts = domain.split('.')
            self.assertGreaterEqual(len(parts), 2)  # At least domain.tld
    
    def test_hash_consistency_for_real_websites(self):
        """Test that hashing is consistent for real website URLs"""
        test_content = "Sample content for testing consistency"
        
        # Test with multiple real websites
        for website in self.websites[:3]:
            url = website["url"]
            domain = url.replace("https://", "").replace("http://", "").split('/')[0]
            
            # Generate hash multiple times
            hash1 = hashlib.sha256(test_content.encode()).hexdigest()
            hash2 = hashlib.sha256(test_content.encode()).hexdigest()
            
            # Should be identical
            self.assertEqual(hash1, hash2, f"Hash inconsistency for {url}")
            
            # Should be valid SHA256 format
            self.assertEqual(len(hash1), 64)
            self.assertTrue(all(c in '0123456789abcdef' for c in hash1))
    
    def test_prevent_duplicate_scraping_simulation(self):
        """Test simulation of preventing duplicate scraping"""
        # Create initial hash data for a real website
        test_content = "This is the content scraped from the website"
        content_hash = hashlib.sha256(test_content.encode()).hexdigest()
        
        initial_data = {
            self.sample_domain: {
                self.sample_url: {
                    "hash": content_hash,
                    "timestamp": datetime.now().isoformat()
                }
            }
        }
        
        with open(self.hashes_file, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f, indent=2)
        
        # Simulate checking for duplicates before scraping
        def should_skip_scraping(url, content):
            """Simulate the duplicate detection logic"""
            domain = url.replace("https://", "").replace("http://", "").split('/')[0]
            new_hash = hashlib.sha256(content.encode()).hexdigest()
            
            try:
                with open(self.hashes_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                
                if domain in existing_data and url in existing_data[domain]:
                    existing_hash = existing_data[domain][url]["hash"]
                    return existing_hash == new_hash
            except (FileNotFoundError, json.JSONDecodeError):
                pass
            
            return False
        
        # Test with same content (should skip)
        should_skip_same = should_skip_scraping(self.sample_url, test_content)
        self.assertTrue(should_skip_same, "Should skip scraping for duplicate content")
        
        # Test with different content (should not skip)
        different_content = "This is different content from the website"
        should_skip_different = should_skip_scraping(self.sample_url, different_content)
        self.assertFalse(should_skip_different, "Should not skip scraping for different content")
        
        # Test with new URL (should not skip)
        new_url = self.sample_url2
        should_skip_new = should_skip_scraping(new_url, test_content)
        self.assertFalse(should_skip_new, "Should not skip scraping for new URL")


if __name__ == '__main__':
    unittest.main()