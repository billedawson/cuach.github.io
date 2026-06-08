#!/usr/bin/env python3
"""
Convert a Ghost JSON export to Jekyll markdown posts.
Usage: python3 ghost_to_jekyll.py ghost-export.json
"""

import json
import sys
import os
import re
from datetime import datetime

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text.strip('-')

def convert(export_file):
    with open(export_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Handle different Ghost export formats
    try:
        posts = data['db'][0]['data']['posts']
    except (KeyError, IndexError):
        try:
            posts = data['data']['posts']
        except KeyError:
            print("ERROR: Could not find posts in export. Check your Ghost export format.")
            sys.exit(1)

    os.makedirs('_posts', exist_ok=True)

    converted = 0
    skipped = 0

    for post in posts:
        # Skip drafts and pages — only export published posts
        status = post.get('status', '')
        post_type = post.get('type', 'post')
        if status != 'published' or post_type != 'post':
            skipped += 1
            continue

        title = post.get('title') or 'Untitled'
        slug = post.get('slug') or slugify(title)
        content = post.get('plaintext') or post.get('html') or ''
        custom_excerpt = post.get('custom_excerpt') or ''

        # Parse date
        published_at = post.get('published_at') or post.get('created_at')
        try:
            dt = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            date_str = dt.strftime('%Y-%m-%d')
            date_full = dt.strftime('%Y-%m-%d %H:%M:%S %z')
        except Exception:
            date_str = '1970-01-01'
            date_full = '1970-01-01 00:00:00 +0000'

        filename = f"_posts/{date_str}-{slug}.md"

        # Escape quotes outside the f-string to avoid backslash-in-f-string error
        safe_title = title.replace('"', '\\"')
        safe_excerpt = custom_excerpt.replace('"', '\\"')

        front_matter = f"---\nlayout: post\ntitle: \"{safe_title}\"\ndate: {date_full}\nslug: {slug}\n"

        if custom_excerpt:
            front_matter += f"excerpt: \"{safe_excerpt}\"\n"

        front_matter += "---\n"

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(front_matter)
            f.write('\n')
            f.write(content)

        print(f"  created {filename}")
        converted += 1

    print(f"\nDone. {converted} posts converted, {skipped} skipped (drafts/pages).")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 ghost_to_jekyll.py ghost-export.json")
        sys.exit(1)
    convert(sys.argv[1])
