from urllib.parse import urlparse
from collections import defaultdict
from typing import List, Dict, Tuple
from dataclasses import dataclass

@dataclass
class DomainStats:
    domain: str
    frequent_subpaths: Dict[str, int]

@dataclass
class ScraperStats:

    #     start_time: string;
    # end_time: string;
    # elapsed_time: number;
    # total_pages: number;
    # total_errors: number;
    # total_warnings: number;
    # total_urls: number;
    # total_text_chunks: number;

    queued_urls_count: int
    requested_urls_count: int
    success_urls_count: int
    error_urls_count: int
    skipped_urls_count: int
    domain_stats: Dict[str, DomainStats]

def analyze_url_groups(urls: List[str], min_pages_per_sub_path: int = 5) -> Dict[str, DomainStats]:
    # Group URLs by domain
    domain_groups = defaultdict(list)
    for url in urls:
        parsed = urlparse(url)
        domain = parsed.netloc
        path = parsed.path.strip('/')
        domain_groups[domain].append(path)
    
    # Process each domain group
    results = {}
    for domain, paths in domain_groups.items():
        subpath_counts: Dict[str, int] = defaultdict(int)
        
        # Count occurrences of each subpath
        for path in paths:
            segments = path.split('/')
            current_path = ''
            
            # Count each parent path
            for segment in segments:
                if current_path:
                    current_path += '/'
                current_path += segment
                subpath_counts[current_path] += 1
        
        # Filter subpaths that meet minimum frequency requirement
        frequent_subpaths = {
            subpath: count
            for subpath, count in subpath_counts.items()
            if count >= min_pages_per_sub_path
        }
        
        # Sort by count descending, then by path
        if frequent_subpaths:
            results[domain] = DomainStats(
                domain=domain,
                frequent_subpaths=frequent_subpaths
            )
    
    return results

# Example usage:
if __name__ == "__main__":
    test_urls = [
        "https://example.com/blog/2023/post1",
        "https://example.com/blog/2023/post2",
        "https://example.com/blog/2022/post1",
        "https://example.com/blog/2022/post1/1",
        "https://example.com/blog/2022/post1/2",
        "https://example.com/blog/2022/post1/3",
        "https://example.com/about",
        "https://another.com/products/item1",
        "https://another.com/products/item2"
    ]
    
    result = analyze_url_groups(test_urls, min_pages_per_sub_path=3)
    for domain in result.values():
        print(f"\nDomain: {domain}")
        for subpath, count in domain.frequent_subpaths.items():
            print(f"  {subpath}: {count} pages")