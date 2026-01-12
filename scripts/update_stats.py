import os
import requests
from datetime import datetime
import json
import re

# Configuration
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME", "10xCore")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def log(message):
    """Print log with timestamp"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")

def get_user_stats():
    """Fetch user statistics from GitHub API"""
    try:
        log(f"📥 Fetching stats for user: {GITHUB_USERNAME}")
        url = f"https://api.github.com/users/{GITHUB_USERNAME}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        log(f"✅ Successfully fetched user stats")
        return data
    except Exception as e:
        log(f"❌ Error fetching user stats: {e}")
        return {}

def get_repos():
    """Fetch all repositories"""
    try:
        log("📥 Fetching repositories...")
        url = f"https://api.github.com/users/{GITHUB_USERNAME}/repos?sort=stars&per_page=100&type=owner"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        log(f"✅ Successfully fetched {len(data)} repositories")
        return data
    except Exception as e:
        log(f"❌ Error fetching repos: {e}")
        return []

def get_total_commits():
    """Get total commits count"""
    try:
        log("📥 Fetching total commits...")
        url = f"https://api.github.com/search/commits?q=author:{GITHUB_USERNAME}&per_page=1"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        total = response.json().get('total_count', 0)
        log(f"✅ Total commits: {total}")
        return total
    except Exception as e:
        log(f"⚠️  Could not fetch commits: {e}")
        return 0

def format_number(num):
    """Format large numbers with K, M, etc."""
    if num >= 1000000:
        return f"{num/1000000:.1f}M"
    elif num >= 1000:
        return f"{num/1000:.1f}K"
    return str(num)

def get_language_stats(repos):
    """Calculate language distribution"""
    languages = {}
    for repo in repos:
        lang = repo.get('language')
        if lang:
            languages[lang] = languages.get(lang, 0) + 1
    
    # Sort by count
    sorted_langs = sorted(languages.items(), key=lambda x: x[1], reverse=True)
    return dict(sorted_langs[:10])

def create_language_bar(lang_stats, max_count=10):
    """Create a visual bar for languages"""
    if not lang_stats:
        return "No language data available"
    
    max_val = max(lang_stats.values())
    bars = []
    
    for lang, count in lang_stats.items():
        percentage = (count / max_val) * 100 if max_val > 0 else 0
        bar_length = int(percentage / 5)  # 20 chars max
        bar = "█" * bar_length + "░" * (20 - bar_length)
        bars.append(f"{lang:<15} {bar} {count} repos")
    
    return "\n".join(bars)

def update_readme():
    """Update README with dynamic data"""
    log("🚀 Starting README update process...")
    
    try:
        # Fetch data
        user_data = get_user_stats()
        repos = get_repos()
        total_commits = get_total_commits()
        
        if not user_data or not repos:
            log("❌ Failed to fetch data")
            return
        
        # Calculate stats
        public_repos = user_data.get('public_repos', 0)
        followers = user_data.get('followers', 0)
        following = user_data.get('following', 0)
        total_stars = sum(repo['stargazers_count'] for repo in repos)
        total_forks = sum(repo['forks_count'] for repo in repos)
        avg_stars = int(total_stars / public_repos) if public_repos > 0 else 0
        
        # Get language stats
        lang_stats = get_language_stats(repos)
        language_bar = create_language_bar(lang_stats)
        
        # Get top repos
        top_repos = sorted(repos, key=lambda x: x['stargazers_count'], reverse=True)[:5]
        
        log(f"📊 Stats calculated:")
        log(f"   - Public Repos: {public_repos}")
        log(f"   - Total Stars: {format_number(total_stars)}")
        log(f"   - Total Forks: {format_number(total_forks)}")
        log(f"   - Followers: {format_number(followers)}")
        log(f"   - Total Commits: {format_number(total_commits)}")
        
        # Read current README
        log("📖 Reading current README...")
        with open("README.md", "r", encoding="utf-8") as f:
            readme_content = f.read()
        
        # Build replacement sections
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
        
        # Create stats table
        stats_section = f"""
### 📊 Live Statistics

| Metric | Value |
|--------|-------|
| Public Repositories | **{public_repos}** |
| Total Stars | ⭐ **{format_number(total_stars)}** |
| Total Forks | 🍴 **{format_number(total_forks)}** |
| Followers | 👥 **{format_number(followers)}** |
| Following | 🔗 **{format_number(following)}** |
| Total Commits | 📝 **{format_number(total_commits)}** |
| Average Stars/Repo | 📈 **{avg_stars}** |
| Last Updated | 🕐 *{now}* |

"""
        
        # Create language stats section
        language_section = f"""
### 🛠️ Language Distribution

```
{language_bar}
```

"""
        
        # Create top repos section
        repos_section = "\n### ⭐ Top Repositories\n\n"
        for repo in top_repos:
            lang = repo.get('language', 'N/A') or 'N/A'
            desc = repo.get('description', 'No description') or 'No description'
            repos_section += f"- **[{repo['name']}]({repo['html_url']})** - {desc}\n"
            repos_section += f"  - ⭐ {format_number(repo['stargazers_count'])} stars | 🍴 {format_number(repo['forks_count'])} forks | 🔧 {lang}\n\n"
        
        # Replace or insert sections
        if "<!-- STATS_START -->" in readme_content and "<!-- STATS_END -->" in readme_content:
            # Replace between markers
            readme_content = re.sub(
                r'<!-- STATS_START -->.*?<!-- STATS_END -->',
                f'<!-- STATS_START -->\n{stats_section}\n<!-- STATS_END -->',
                readme_content,
                flags=re.DOTALL
            )
        
        if "<!-- LANGUAGE_START -->" in readme_content and "<!-- LANGUAGE_END -->" in readme_content:
            readme_content = re.sub(
                r'<!-- LANGUAGE_START -->.*?<!-- LANGUAGE_END -->',
                f'<!-- LANGUAGE_START -->\n{language_section}\n<!-- LANGUAGE_END -->',
                readme_content,
                flags=re.DOTALL
            )
        
        if "<!-- REPOS_START -->" in readme_content and "<!-- REPOS_END -->" in readme_content:
            readme_content = re.sub(
                r'<!-- REPOS_START -->.*?<!-- REPOS_END -->',
                f'<!-- REPOS_START -->\n{repos_section}\n<!-- REPOS_END -->',
                readme_content,
                flags=re.DOTALL
            )
        
        # Write updated README
        log("✍️  Writing updated README...")
        with open("README.md", "w", encoding="utf-8") as f:
            f.write(readme_content)
        
        log("✅ README updated successfully!")
        log(f"📊 Updated with {len(top_repos)} top repositories")
        log(f"🎯 Language stats for {len(lang_stats)} languages")
        
    except Exception as e:
        log(f"❌ Error during update: {e}")
        raise

if __name__ == "__main__":
    update_readme()
