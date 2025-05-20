#!/usr/bin/env python3
"""
Inverted Index Demonstrator with Beautiful Terminal UI
An interactive tool to understand document indexing and search
"""

import os
import sys
import re
import time
import random
from typing import List, Dict, Set, Tuple
from collections import defaultdict
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich.markdown import Markdown
from rich.live import Live

console = Console()

class InvertedIndex:
    """Inverted index implementation for document search"""
    
    def __init__(self):
        self.index = defaultdict(set)  # Maps terms to document IDs
        self.documents = {}  # Maps document IDs to document content
        self.doc_count = 0  # Total number of documents
        self.index_history = []  # Track indexing operations
        self.search_history = []  # Track search operations
    
    def preprocess_text(self, text: str) -> List[str]:
        """Preprocess text into terms for indexing"""
        # Convert to lowercase
        text = text.lower()
        # Remove punctuation and split into terms
        terms = re.findall(r'\b\w+\b', text)
        return terms
    
    def add_document(self, doc_id: str, content: str) -> Dict:
        """Add a document to the index"""
        # Store raw document
        self.documents[doc_id] = content
        self.doc_count += 1
        
        # Extract terms and build index
        terms = self.preprocess_text(content)
        unique_terms = set(terms)
        positions = {}
        
        # For each term, store document ID in inverted index
        for term in unique_terms:
            self.index[term].add(doc_id)
            # Find all positions of this term in the document
            term_positions = [i for i, t in enumerate(terms) if t == term]
            positions[term] = term_positions
        
        # Track indexing operation
        self.index_history.append({
            'operation': 'add',
            'doc_id': doc_id,
            'terms_count': len(unique_terms),
            'terms': list(unique_terms)[:10]  # Store just the first 10 terms for display
        })
        
        return {
            'doc_id': doc_id,
            'terms_count': len(unique_terms),
            'terms': list(unique_terms),
            'positions': positions
        }
    
    def search(self, query: str) -> Dict:
        """Search the index for documents matching the query"""
        start_time = time.time()
        
        # Process query into terms
        query_terms = self.preprocess_text(query)
        
        # For each term, get matching documents
        results = {}
        matched_docs = set()
        for term in query_terms:
            if term in self.index:
                matching_docs = self.index[term]
                for doc_id in matching_docs:
                    if doc_id not in results:
                        results[doc_id] = {
                            'matches': {},
                            'score': 0
                        }
                    
                    # Calculate term frequency
                    doc_terms = self.preprocess_text(self.documents[doc_id])
                    term_freq = doc_terms.count(term)
                    
                    # Add to results with TF score
                    results[doc_id]['matches'][term] = term_freq
                    results[doc_id]['score'] += term_freq
                
                matched_docs.update(matching_docs)
        
        # Sort results by score (descending)
        sorted_results = []
        for doc_id, data in results.items():
            sorted_results.append({
                'doc_id': doc_id,
                'content': self.documents[doc_id],
                'matches': data['matches'],
                'score': data['score']
            })
        
        sorted_results.sort(key=lambda x: x['score'], reverse=True)
        
        elapsed_time = time.time() - start_time
        
        # Save search to history
        self.search_history.append({
            'query': query,
            'terms': query_terms,
            'matching_docs': len(matched_docs),
            'elapsed_time': elapsed_time
        })
        
        return {
            'query': query,
            'terms': query_terms,
            'results': sorted_results,
            'count': len(matched_docs),
            'elapsed_time': elapsed_time
        }
    
    def get_term_frequency(self) -> Dict[str, int]:
        """Get frequency of terms across all documents"""
        term_freq = {}
        for term, docs in self.index.items():
            term_freq[term] = len(docs)
        
        return term_freq
    
    def clear(self):
        """Clear the index and documents"""
        self.index = defaultdict(set)
        self.documents = {}
        self.doc_count = 0
        self.index_history = []
        self.search_history = []

class InvertedIndexDemo:
    """Interactive demo for Inverted Index"""
    
    def __init__(self):
        self.inverted_index = InvertedIndex()
        self.sample_documents = {
            "doc1": "The quick brown fox jumps over the lazy dog",
            "doc2": "A lazy dog and a quick cat played in the yard",
            "doc3": "The brown fox saw another fox in the forest",
            "doc4": "Programming languages like Python and JavaScript are widely used",
            "doc5": "Python is a popular language for data science and machine learning",
            "doc6": "Natural language processing helps computers understand human language"
        }
    
    def draw_index_visualization(self, highlight_terms: List[str] = None) -> Panel:
        """Draw the inverted index visualization"""
        if not self.inverted_index or self.inverted_index.doc_count == 0:
            return Panel("[yellow]Index is empty. Add documents to build the index.[/yellow]")
        
        # Get term frequency for sorting
        term_freq = self.inverted_index.get_term_frequency()
        
        # Sort terms by frequency for display
        sorted_terms = sorted(term_freq.items(), key=lambda x: x[1], reverse=True)
        
        # Create a table to display the index
        table = Table(title="[bold]Inverted Index[/bold]", expand=False)
        table.add_column("Term", style="cyan")
        table.add_column("Documents", style="green")
        table.add_column("Count", style="yellow", justify="right")
        
        # Limit display to top N terms
        max_terms = 15
        displayed_terms = 0
        
        # Check if we should highlight specific terms
        if highlight_terms:
            highlight_terms = [t.lower() for t in highlight_terms]
            
            # First show highlighted terms
            for term in highlight_terms:
                if term in self.inverted_index.index:
                    docs = self.inverted_index.index[term]
                    formatted_term = f"[bold white on blue]{term}[/bold white on blue]"
                    table.add_row(formatted_term, ", ".join(docs), str(len(docs)))
                    displayed_terms += 1
            
            # Add separator if we showed any highlighted terms
            if displayed_terms > 0:
                table.add_row("---", "---", "---")
                
        # Add most frequent terms
        for term, freq in sorted_terms:
            # Skip if we already displayed this term as highlighted
            if highlight_terms and term in highlight_terms:
                continue
                
            docs = self.inverted_index.index[term]
            table.add_row(term, ", ".join(docs), str(freq))
            
            displayed_terms += 1
            if displayed_terms >= max_terms:
                break
        
        # Display counts in panel subtitle
        doc_count = self.inverted_index.doc_count
        term_count = len(self.inverted_index.index)
        
        return Panel(
            table,
            title="[bold]Inverted Index Visualization[/bold]",
            subtitle=f"Documents: {doc_count} | Unique Terms: {term_count}",
            border_style="cyan"
        )
    
    def show_document_preview(self, doc_id: str, highlight_terms: List[str] = None):
        """Show a preview of a document with highlighted terms"""
        if doc_id not in self.inverted_index.documents:
            console.print(f"[red]Document {doc_id} not found[/red]")
            return
        
        content = self.inverted_index.documents[doc_id]
        
        # Prepare a version of content with highlighted terms
        if highlight_terms:
            highlighted_content = content
            for term in highlight_terms:
                # Create regex pattern to match whole words only
                pattern = fr'\b{re.escape(term)}\b'
                replacement = f"[bold yellow]{term}[/bold yellow]"
                highlighted_content = re.sub(pattern, replacement, highlighted_content, flags=re.IGNORECASE)
        else:
            highlighted_content = content
        
        console.print(Panel(
            highlighted_content,
            title=f"[bold]Document: {doc_id}[/bold]",
            border_style="green"
        ))
    
    def show_indexing_animation(self, doc_id: str, result: Dict):
        """Show animation when indexing a document"""
        terms = result['terms']
        terms_count = result['terms_count']
        
        console.print(f"Indexing document: [bold cyan]{doc_id}[/bold cyan]")
        
        # Show a sample of the indexed terms
        sample_terms = terms[:min(10, len(terms))]
        
        term_table = Table(title="[bold]Sample of Indexed Terms[/bold]", expand=False)
        term_table.add_column("Term", style="cyan")
        
        for term in sample_terms:
            term_table.add_row(term)
        
        console.print(term_table)
        console.print(f"[green]Successfully indexed {terms_count} unique terms[/green]")
        
        # Show updated index
        console.print(self.draw_index_visualization())
    
    def show_search_animation(self, query: str, result: Dict):
        """Show animation when searching the index"""
        terms = result['terms']
        count = result['count']
        elapsed_time = result['elapsed_time']
        
        console.print(f"Searching for: [bold cyan]{query}[/bold cyan]")
        
        # Show search terms
        console.print(f"Query terms: {', '.join(['[bold cyan]' + t + '[/bold cyan]' for t in terms])}")
        
        # Show results summary
        console.print(f"[green]Found {count} matching documents in {elapsed_time:.4f} seconds[/green]")
        
        # Show search results
        if count > 0:
            results_table = Table(title="[bold]Search Results[/bold]", expand=True)
            results_table.add_column("Rank", style="cyan", width=5)
            results_table.add_column("Document", style="green", width=10)
            results_table.add_column("Score", style="yellow", width=8)
            results_table.add_column("Preview", style="white")
            
            for i, doc in enumerate(result['results']):
                # Create a preview with highlighting
                content = doc['content']
                preview = content[:60] + "..." if len(content) > 60 else content
                
                # Highlight matching terms in preview
                for term in terms:
                    if term.lower() in preview.lower():
                        pattern = fr'\b{re.escape(term)}\b'
                        replacement = f"[bold yellow]{term}[/bold yellow]"
                        preview = re.sub(pattern, replacement, preview, flags=re.IGNORECASE)
                
                results_table.add_row(
                    str(i+1),
                    doc['doc_id'],
                    str(doc['score']),
                    preview
                )
            
            console.print(results_table)
            
            # Update index visualization with highlighted query terms
            console.print(self.draw_index_visualization(highlight_terms=terms))
    
    def show_history(self):
        """Show history of operations"""
        if not self.inverted_index:
            console.print("[yellow]Inverted index not initialized.[/yellow]")
            return
        
        # Create combined history table
        history_table = Table(title="Operation History")
        history_table.add_column("Operation", style="cyan", width=10)
        history_table.add_column("Details", style="green")
        history_table.add_column("Terms", style="yellow")
        history_table.add_column("Results", style="magenta", width=12)
        
        # Add indexing history
        for entry in self.inverted_index.index_history:
            terms_preview = ', '.join(entry['terms'])
            history_table.add_row(
                "INDEX",
                f"Doc: {entry['doc_id']}",
                f"{terms_preview}...",
                f"{entry['terms_count']} terms"
            )
        
        # Add search history
        for entry in self.inverted_index.search_history:
            terms = ', '.join(entry['terms'])
            history_table.add_row(
                "SEARCH",
                f"Query: {entry['query']}",
                terms,
                f"{entry['matching_docs']} docs"
            )
        
        console.print(history_table)
    
    def show_statistics(self):
        """Show index statistics"""
        if not self.inverted_index or self.inverted_index.doc_count == 0:
            console.print("[yellow]Inverted index is empty.[/yellow]")
            return
        
        # Create info table
        stats_table = Table(title="Inverted Index Statistics", expand=False)
        stats_table.add_column("Property", style="cyan")
        stats_table.add_column("Value", style="green")
        
        # Basic stats
        doc_count = self.inverted_index.doc_count
        term_count = len(self.inverted_index.index)
        stats_table.add_row("Total Documents", str(doc_count))
        stats_table.add_row("Unique Terms", str(term_count))
        
        # Term distribution
        term_freq = self.inverted_index.get_term_frequency()
        if term_freq:
            max_term = max(term_freq.items(), key=lambda x: x[1])
            min_term = min(term_freq.items(), key=lambda x: x[1])
            avg_docs_per_term = sum(term_freq.values()) / len(term_freq)
            
            stats_table.add_row("Most Common Term", f"{max_term[0]} ({max_term[1]} docs)")
            stats_table.add_row("Least Common Term", f"{min_term[0]} ({min_term[1]} docs)")
            stats_table.add_row("Avg. Docs Per Term", f"{avg_docs_per_term:.2f}")
        
        # Document length statistics
        doc_lengths = {doc_id: len(self.inverted_index.preprocess_text(content)) 
                      for doc_id, content in self.inverted_index.documents.items()}
        if doc_lengths:
            avg_doc_length = sum(doc_lengths.values()) / len(doc_lengths)
            max_doc = max(doc_lengths.items(), key=lambda x: x[1])
            min_doc = min(doc_lengths.items(), key=lambda x: x[1])
            
            stats_table.add_row("Avg. Terms Per Doc", f"{avg_doc_length:.2f}")
            stats_table.add_row("Longest Document", f"{max_doc[0]} ({max_doc[1]} terms)")
            stats_table.add_row("Shortest Document", f"{min_doc[0]} ({min_doc[1]} terms)")
        
        console.print(stats_table)
    
    def show_explanation(self):
        """Show an explanation of how inverted indices work"""
        explanation = """
[bold cyan]What is an Inverted Index?[/bold cyan]
An inverted index is a data structure used to enable fast full-text searches. It maps terms (words) to the documents that contain them - essentially a "word-to-document" mapping.

[bold cyan]Key Properties:[/bold cyan]
• [green]Efficient Search[/green] - Quickly find documents containing specific terms
• [green]Term-Centric[/green] - Organized by terms rather than documents
• [green]Scalable[/green] - Can handle large collections of documents
• [green]Foundation of Search Engines[/green] - Used by virtually all search engines

[bold cyan]How It Works:[/bold cyan]
1. [bold]Document Processing:[/bold] Break documents into terms (tokenization)
2. [bold]Index Building:[/bold] For each term, store a list of documents containing it
3. [bold]Search:[/bold] Break query into terms, find documents containing those terms
4. [bold]Ranking:[/bold] Score and sort results based on relevance metrics

[bold cyan]Simple Example:[/bold cyan]
Documents:
  Doc1: "cats and dogs"
  Doc2: "dogs and birds"
  Doc3: "cats eat fish"

Inverted Index:
  cats → {Doc1, Doc3}
  dogs → {Doc1, Doc2}
  and → {Doc1, Doc2}
  birds → {Doc2}
  eat → {Doc3}
  fish → {Doc3}

[bold cyan]Search Query: "cats and dogs"[/bold cyan]
1. Break into terms: [cats, and, dogs]
2. Lookup in index:
   • cats → {Doc1, Doc3}
   • and → {Doc1, Doc2}
   • dogs → {Doc1, Doc2}
3. Combine results: Doc1 contains all terms, Doc2 and Doc3 contain some terms
4. Rank: Doc1 highest (all terms), Doc2 and Doc3 lower (partial matches)

[bold cyan]Practical Applications:[/bold cyan]
• Web search engines
• Email search
• Document management systems
• Code search tools
• E-commerce search functionality
        """
        
        console.print(Panel(Markdown(explanation), title="Inverted Index Explained", border_style="cyan"))
    
    def load_sample_documents(self):
        """Load sample documents into the index"""
        # Clear existing index
        self.inverted_index.clear()
        
        # Add sample documents
        console.print("[cyan]Loading sample documents...[/cyan]")
        
        for doc_id, content in self.sample_documents.items():
            self.inverted_index.add_document(doc_id, content)
            console.print(f"[green]Indexed document: {doc_id}[/green]")
        
        console.print(f"[green]Loaded {len(self.sample_documents)} sample documents[/green]")
        console.print(self.draw_index_visualization())
    
    def run_interactive_ui(self):
        """Run the interactive UI"""
        # Display welcome banner
        console.print(Panel(
            "[bold cyan]Inverted Index Demonstrator[/bold cyan]\nA tool to understand document indexing and search",
            border_style="cyan"
        ))
        
        while True:
            # Display current index status
            if self.inverted_index.doc_count > 0:
                console.print(self.draw_index_visualization())
            else:
                console.print(Panel("[yellow]Index is empty. Add documents to build the index.[/yellow]"))
            
            # Simple menu
            console.print("\n[bold cyan]Menu Options:[/bold cyan]")
            console.print("1. Add Document")
            console.print("2. Search Index")
            console.print("3. View Document")
            console.print("4. View History")
            console.print("5. View Statistics")
            console.print("6. Load Sample Documents")
            console.print("7. Clear Index")
            console.print("8. How It Works")
            console.print("9. Exit")
            
            choice = input("\nEnter your choice (1-9): ")
            console.print()
            
            if choice == "1":  # Add Document
                doc_id = input("Enter document ID: ")
                content = input("Enter document content: ")
                
                if doc_id and content:
                    # Add document to index
                    result = self.inverted_index.add_document(doc_id, content)
                    self.show_indexing_animation(doc_id, result)
                    
            elif choice == "2":  # Search Index
                if self.inverted_index.doc_count == 0:
                    console.print("[yellow]Index is empty. Add documents first.[/yellow]")
                    continue
                    
                query = input("Enter search query: ")
                
                if query:
                    # Search the index
                    result = self.inverted_index.search(query)
                    self.show_search_animation(query, result)
                    
                    # Ask if user wants to view a document
                    if result['count'] > 0:
                        view_doc = input("View a document? (y/n): ").lower()
                        
                        if view_doc == 'y':
                            # Display available documents
                            console.print("\n[bold]Available Documents:[/bold]")
                            for i, doc in enumerate(result['results']):
                                console.print(f"{i+1}. {doc['doc_id']}")
                            
                            doc_num = input("\nEnter document number to view: ")
                            try:
                                doc_num = int(doc_num) - 1
                                if 0 <= doc_num < len(result['results']):
                                    self.show_document_preview(
                                        result['results'][doc_num]['doc_id'], 
                                        highlight_terms=result['terms']
                                    )
                            except ValueError:
                                console.print("[red]Invalid document number[/red]")
            
            elif choice == "3":  # View Document
                if self.inverted_index.doc_count == 0:
                    console.print("[yellow]No documents available.[/yellow]")
                    continue
                
                # List available documents
                console.print("[bold]Available Documents:[/bold]")
                for i, doc_id in enumerate(self.inverted_index.documents.keys()):
                    console.print(f"{i+1}. {doc_id}")
                
                doc_num = input("\nEnter document number to view: ")
                try:
                    doc_num = int(doc_num) - 1
                    doc_ids = list(self.inverted_index.documents.keys())
                    if 0 <= doc_num < len(doc_ids):
                        self.show_document_preview(doc_ids[doc_num])
                    else:
                        console.print("[red]Invalid document number[/red]")
                except ValueError:
                    console.print("[red]Invalid document number[/red]")
                    
            elif choice == "4":  # View History
                self.show_history()
                
            elif choice == "5":  # View Statistics
                self.show_statistics()
                
            elif choice == "6":  # Load Sample Documents
                if self.inverted_index.doc_count > 0:
                    confirm = input("This will clear existing index. Continue? (y/n): ").lower()
                    if confirm != "y":
                        continue
                
                self.load_sample_documents()
                
            elif choice == "7":  # Clear Index
                confirm = input("Are you sure you want to clear the index? (y/n): ").lower()
                if confirm == "y":
                    self.inverted_index.clear()
                    console.print("[green]Index cleared[/green]")
                    
            elif choice == "8":  # How It Works
                self.show_explanation()
                
            elif choice == "9":  # Exit
                break
                
            # Pause between actions
            console.print()
            input("Press Enter to continue...")
            console.clear()

def main():
    """Main entry point"""
    try:
        demo = InvertedIndexDemo()
        demo.run_interactive_ui()
    except KeyboardInterrupt:
        console.print("\n[red]Demo closed[/red]")
    finally:
        console.print("[green]Thanks for exploring Inverted Indices![/green]")

if __name__ == "__main__":
    main()
