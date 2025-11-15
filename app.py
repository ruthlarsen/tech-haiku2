from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import re
import time
import threading
from collections import defaultdict
import random
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Global word storage
word_pool = defaultdict(list)  # syllable_count -> [words]
used_words = set()
word_frequency = defaultdict(int)  # Track word frequency
scraping_active = False
last_scrape_time = None

def split_compound_word(word):
    """Split camelCase/PascalCase and all-lowercase compound words into separate words."""
    original_word = word
    word_lower = word.lower()
    
    # First, handle camelCase/PascalCase by splitting on capital letters
    if re.search(r'[A-Z]', word):
        parts = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)', word)
        if len(parts) > 1:
            return [p.lower() for p in parts if len(p) >= 2]
    
    # For all-lowercase long words, try to detect word boundaries
    # Only attempt splitting if word is long enough (8+ chars) and looks compound
    if len(word_lower) >= 8 and word_lower.isalpha():
        # Common prefixes that often appear in compound words
        prefixes = ['for', 'non', 'pre', 're', 'un', 'de', 'dis', 'mis', 'over', 'under', 
                   'out', 'up', 'down', 'in', 'ex', 'anti', 'auto', 'co', 'inter', 'multi',
                   'sub', 'super', 'trans', 'web', 'net', 'http', 'ssl', 'tls', 'dns', 'api',
                   'url', 'uri', 'xml', 'json', 'html', 'css', 'js', 'sql', 'db', 'auth',
                   'admin', 'user', 'server', 'client', 'error', 'access', 'permission',
                   'security', 'sandbox', 'script', 'request', 'response', 'timeout',
                   'connection', 'network', 'service', 'resource', 'method', 'header',
                   'cookie', 'session', 'token', 'password', 'username', 'email', 'file',
                   'data', 'buffer', 'stack', 'memory', 'disk', 'storage', 'cache']
        
        # Common suffixes
        suffixes = ['ed', 'ing', 'tion', 'sion', 'ment', 'ness', 'ity', 'er', 'or', 'ly',
                   'able', 'ible', 'ful', 'less', 'ous', 'ious', 'ic', 'al', 'ive']
        
        # Common standalone words that appear in compound words
        common_words = ['for', 'and', 'not', 'the', 'has', 'was', 'are', 'can', 'may',
                       'web', 'net', 'box', 'script', 'sand', 'box', 'sandbox', 'permission',
                       'access', 'denied', 'error', 'failed', 'timeout', 'request', 'response',
                       'server', 'client', 'network', 'connection', 'service', 'resource',
                       'method', 'header', 'auth', 'authenticate', 'security', 'secure',
                       'non', 'pre', 'post', 'get', 'put', 'delete', 'patch', 'head',
                       'option', 'options', 'status', 'code', 'message', 'body', 'content',
                       'type', 'length', 'range', 'accept', 'encoding', 'language', 'charset']
        
        # Combine prefixes and common words for matching
        all_known_words = sorted(set(prefixes + common_words), key=len, reverse=True)
        
        # Try to find word boundaries using greedy matching
        found_words = []
        remaining = word_lower
        i = 0
        
        while i < len(remaining):
            matched = False
            # Try longer words first (greedy approach)
            for known_word in all_known_words:
                if len(known_word) >= 3 and remaining[i:].startswith(known_word):
                    found_words.append(known_word)
                    i += len(known_word)
                    matched = True
                    break
            
            if not matched:
                # If no match, try to advance past current position
                # Look for vowel-consonant boundaries as potential word breaks
                if i + 1 < len(remaining):
                    i += 1
                else:
                    break
        
        # If we found multiple words and consumed most of the string, return them
        if len(found_words) > 1 and i >= len(remaining) * 0.8:
            # Filter out very short words
            filtered = [w for w in found_words if len(w) >= 2]
            if len(filtered) > 1:
                return filtered
    
    # If no splitting worked, return the original word
    return [word_lower]

# Improved syllable counting
def count_syllables(word):
    """Count syllables in a word using an improved heuristic."""
    word = word.lower().strip()
    if not word:
        return 0
    
    # Remove punctuation
    word = re.sub(r'[^a-z]', '', word)
    
    if len(word) <= 2:
        return 1
    
    # Special cases
    if word in ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']:
        return 1
    
    # Count vowel groups
    vowels = 'aeiouy'
    count = 0
    prev_was_vowel = False
    
    # Handle 'y' as vowel when not at start
    for i, char in enumerate(word):
        is_vowel = (char in vowels) or (char == 'y' and i > 0)
        if is_vowel and not prev_was_vowel:
            count += 1
        prev_was_vowel = is_vowel
    
    # Handle silent e (but not if it's the only vowel)
    if word.endswith('e') and count > 1:
        count -= 1
    
    # Handle double vowels (diphthongs)
    if re.search(r'[aeiou]{2}', word):
        # Some double vowels count as one syllable
        count = max(1, count - word.count('ee') - word.count('oo'))
    
    # Minimum 1 syllable
    return max(1, count)

def scrape_error_messages():
    """Scrape the internet for customer-facing error messages."""
    global word_pool, word_frequency, last_scrape_time
    
    sources = [
        "https://httpstatuses.com/",
        "https://developer.mozilla.org/en-US/docs/Web/HTTP/Status",
    ]
    
    words_found = []
    
    for url in sources:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                text = soup.get_text()
                
                # Extract error-related phrases
                error_patterns = [
                    r'error[^.]*',
                    r'failed[^.]*',
                    r'not found[^.]*',
                    r'unauthorized[^.]*',
                    r'forbidden[^.]*',
                    r'timeout[^.]*',
                    r'server error[^.]*',
                    r'bad request[^.]*',
                    r'internal error[^.]*',
                    r'access denied[^.]*',
                    r'connection[^.]*',
                    r'authentication[^.]*',
                    r'resource[^.]*',
                    r'service[^.]*',
                ]
                
                for pattern in error_patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    for match in matches:
                        # Extract words (preserve case for compound word detection)
                        raw_words = re.findall(r'\b[a-zA-Z]{2,}\b', match)
                        for raw_word in raw_words:
                            # Split compound words (camelCase/PascalCase)
                            split_words = split_compound_word(raw_word)
                            words_found.extend(split_words)
        except Exception as e:
            print(f"Error scraping {url}: {e}")
    
    # Add comprehensive common error messages
    common_errors = [
        "page not found", "access denied", "server error", "connection timeout",
        "invalid request", "authentication failed", "resource unavailable",
        "service unavailable", "bad gateway", "forbidden access", "not authorized",
        "internal server error", "bad request", "method not allowed",
        "request timeout", "conflict", "gone", "length required",
        "precondition failed", "payload too large", "uri too long",
        "unsupported media type", "range not satisfiable", "expectation failed",
        "too many requests", "request header fields too large", "network error",
        "connection refused", "host unreachable", "dns error", "ssl error",
        "certificate error", "proxy error", "gateway timeout", "version not supported",
        "variant also negotiates", "insufficient storage", "loop detected",
        "not extended", "network authentication required", "unknown error",
        "operation failed", "try again later", "please wait", "system busy",
        "maintenance mode", "feature unavailable", "account locked", "session expired",
        "invalid credentials", "password incorrect", "username not found",
        "email already exists", "invalid email format", "file too large",
        "file not found", "permission denied", "read only", "write protected",
        "disk full", "out of memory", "buffer overflow", "stack overflow",
        "null pointer", "index out of bounds", "type mismatch", "parse error",
        "syntax error", "compilation error", "runtime error", "logic error"
    ]
    
    for error in common_errors:
        # Extract words and split compound words
        raw_words = re.findall(r'\b[a-zA-Z]{2,}\b', error)
        for raw_word in raw_words:
            split_words = split_compound_word(raw_word)
            words_found.extend(split_words)
    
    # Process and categorize words (add to existing pool, don't replace)
    for word in words_found:
        if len(word) >= 2:  # Only words with 2+ characters
            syllables = count_syllables(word)
            # Always add to pool (even if duplicate) to increase available words
            # But don't re-add words that are currently marked as used
            if word not in used_words:
                word_pool[syllables].append(word)
            word_frequency[word] += 1
    
    last_scrape_time = datetime.now()
    print(f"Scraped {len(words_found)} words")

def generate_haiku():
    """Generate a haiku using available words (5-7-5 syllable pattern)."""
    global word_pool, used_words, word_frequency
    
    # Get unique words first (frequency == 1), then duplicates
    def get_word(syllable_count):
        if syllable_count not in word_pool or not word_pool[syllable_count]:
            return None
            
        # Try unique words first (words that appeared only once in all scrapes)
        unique_words = [w for w in word_pool[syllable_count] 
                       if w not in used_words and word_frequency[w] == 1]
        if unique_words:
            word = random.choice(unique_words)
            used_words.add(word)
            word_pool[syllable_count].remove(word)  # Remove one instance
            return word
        
        # Then try any unused word (even if it appeared multiple times)
        available_words = [w for w in word_pool[syllable_count] if w not in used_words]
        if available_words:
            word = random.choice(available_words)
            used_words.add(word)
            word_pool[syllable_count].remove(word)  # Remove one instance
            return word
        
        # If no unused words, reuse from pool (but mark as used)
        if word_pool[syllable_count]:
            word = random.choice(word_pool[syllable_count])
            used_words.add(word)
            word_pool[syllable_count].remove(word)  # Remove one instance
            return word
        
        return None
    
    line1 = []  # 5 syllables
    line2 = []  # 7 syllables
    line3 = []  # 5 syllables
    
    # Build line 1 (5 syllables)
    while sum(count_syllables(w) for w in line1) < 5:
        remaining = 5 - sum(count_syllables(w) for w in line1)
        if remaining <= 0:
            break
        # Try to find a word that fits
        word = None
        for syllable_count in range(min(remaining, 4), 0, -1):
            word = get_word(syllable_count)
            if word:
                break
        if word:
            line1.append(word)
        else:
            # If no exact match, try any available word
            for syllable_count in range(1, 5):
                if syllable_count in word_pool and word_pool[syllable_count]:
                    word = get_word(syllable_count)
                    if word:
                        line1.append(word)
                        break
            if not word:
                break
    
    # Build line 2 (7 syllables)
    while sum(count_syllables(w) for w in line2) < 7:
        remaining = 7 - sum(count_syllables(w) for w in line2)
        if remaining <= 0:
            break
        word = None
        for syllable_count in range(min(remaining, 4), 0, -1):
            word = get_word(syllable_count)
            if word:
                break
        if word:
            line2.append(word)
        else:
            for syllable_count in range(1, 5):
                if syllable_count in word_pool and word_pool[syllable_count]:
                    word = get_word(syllable_count)
                    if word:
                        line2.append(word)
                        break
            if not word:
                break
    
    # Build line 3 (5 syllables)
    while sum(count_syllables(w) for w in line3) < 5:
        remaining = 5 - sum(count_syllables(w) for w in line3)
        if remaining <= 0:
            break
        word = None
        for syllable_count in range(min(remaining, 4), 0, -1):
            word = get_word(syllable_count)
            if word:
                break
        if word:
            line3.append(word)
        else:
            for syllable_count in range(1, 5):
                if syllable_count in word_pool and word_pool[syllable_count]:
                    word = get_word(syllable_count)
                    if word:
                        line3.append(word)
                        break
            if not word:
                break
    
    return {
        'line1': ' '.join(line1).capitalize(),
        'line2': ' '.join(line2).capitalize(),
        'line3': ' '.join(line3).capitalize(),
        'timestamp': datetime.now().isoformat()
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/words', methods=['GET'])
def get_words():
    """Get all words in the pool."""
    all_words = []
    for syllable_count in sorted(word_pool.keys()):
        for word in word_pool[syllable_count]:
            all_words.append({
                'word': word,
                'syllables': syllable_count,
                'frequency': word_frequency[word],
                'used': word in used_words
            })
    return jsonify({
        'words': all_words,
        'total': len(all_words),
        'used': len(used_words)
    })

@app.route('/api/haiku', methods=['GET'])
def get_haiku():
    """Generate a new haiku."""
    haiku = generate_haiku()
    return jsonify(haiku)

@app.route('/api/scrape', methods=['POST'])
def trigger_scrape():
    """Manually trigger a scrape."""
    thread = threading.Thread(target=scrape_error_messages)
    thread.daemon = True
    thread.start()
    return jsonify({'status': 'scraping started'})

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get statistics about the word pool."""
    total_words = sum(len(words) for words in word_pool.values())
    return jsonify({
        'total_words': total_words,
        'used_words': len(used_words),
        'available_words': total_words - len(used_words),
        'last_scrape': last_scrape_time.isoformat() if last_scrape_time else None,
        'word_distribution': {str(k): len(v) for k, v in word_pool.items()}
    })

# Initialize scraping on module load (for Vercel deployment)
# This will run when the serverless function is first invoked
try:
    if not word_pool or len(word_pool) == 0:
        print("Initial scrape...")
        scrape_error_messages()
except Exception as e:
    print(f"Error during initial scrape: {e}")

if __name__ == '__main__':
    app.run(debug=True, port=5001, host='127.0.0.1')

