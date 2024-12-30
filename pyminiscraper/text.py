import re
from typing import List, Optional

def chunk_text(text: str, 
               max_chunk_size: int = 1000,
               overlap: int = 100,
               min_chunk_size: int = 100) -> List[str]:
    """
    Split text into semantically meaningful chunks while preserving context.
    
    Args:
        text (str): Input text to be chunked
        max_chunk_size (int): Maximum size of each chunk in characters
        overlap (int): Number of characters to overlap between chunks
        min_chunk_size (int): Minimum chunk size to prevent tiny chunks
        
    Returns:
        List[str]: List of text chunks
    """
    # Clean and normalize text
    text = text.strip()
    
    # If text is shorter than max_chunk_size, return it as is
    if len(text) <= max_chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        # Find the end point for this chunk
        end = start + max_chunk_size
        
        if end >= len(text):
            chunks.append(text[start:])
            break
            
        # Look for paragraph breaks first
        next_para = text.find('\n\n', start, end)
        if next_para != -1 and (next_para - start) >= min_chunk_size:
            chunks.append(text[start:next_para].strip())
            start = next_para + 2
            continue
            
        # Look for sentence breaks
        last_period = text.rfind('. ', start, end)
        if last_period != -1 and (last_period - start) >= min_chunk_size:
            chunks.append(text[start:last_period + 1].strip())
            start = last_period + 1
            continue
            
        # If no good breaking point, look for last space
        last_space = text.rfind(' ', start, end)
        if last_space != -1 and (last_space - start) >= min_chunk_size:
            chunks.append(text[start:last_space].strip())
            start = last_space + 1
            continue
            
        # If no good breaking point found, force a break at max_chunk_size
        chunks.append(text[start:end].strip())
        start = end - overlap
    
    # Clean up chunks
    chunks = [chunk.strip() for chunk in chunks if chunk.strip()]
    
    return chunks

def get_chunk_stats(chunks: List[str]) -> dict:
    """
    Get statistics about the chunks.
    
    Args:
        chunks (List[str]): List of text chunks
        
    Returns:
        dict: Dictionary containing chunk statistics
    """
    lengths = [len(chunk) for chunk in chunks]
    return {
        'num_chunks': len(chunks),
        'avg_chunk_size': sum(lengths) / len(chunks) if chunks else 0,
        'min_chunk_size': min(lengths) if chunks else 0,
        'max_chunk_size': max(lengths) if chunks else 0
    }