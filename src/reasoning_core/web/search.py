"""Advanced search and analytics functionality."""

import re
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass


@dataclass
class SearchResult:
    """Search result with relevance scoring."""
    item: Dict[str, Any]
    score: float
    matched_fields: List[str]
    highlights: Dict[str, List[str]]


class AdvancedSearch:
    """Advanced search engine for analysis results."""

    def __init__(self):
        """Initialize search engine."""
        self.index = {}
        self.stop_words = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'will', 'with', 'the', 'this', 'but', 'they', 'have',
            'had', 'what', 'said', 'each', 'which', 'their', 'time', 'if',
            'up', 'out', 'many', 'then', 'them', 'these', 'so', 'some', 'her',
            'would', 'make', 'like', 'into', 'him', 'has', 'two', 'more',
            'very', 'after', 'words', 'long', 'than', 'first', 'been', 'call',
            'who', 'oil', 'sit', 'now', 'find', 'down', 'day', 'did', 'get',
            'come', 'made', 'may', 'part',
        }

    def build_index(self, results: Dict[str, Any]) -> None:
        """Build search index from results.

        Args:
            results: Analysis results dictionary
        """
        self.index = {
            'concepts': {},
            'relationships': {},
            'chains': {},
            'questions': {},
        }

        # Index concepts
        for concept in results.get('concepts', []):
            text = concept.get('text', '').lower()
            concept_type = concept.get('type', '').lower()
            context = concept.get('context', '').lower()
            
            words = self._tokenize(text + ' ' + concept_type + ' ' + context)
            for word in words:
                if word not in self.stop_words and len(word) > 2:
                    if word not in self.index['concepts']:
                        self.index['concepts'][word] = []
                    self.index['concepts'][word].append(concept)

        # Index relationships
        for rel in results.get('relationships', []):
            source = rel.get('source', {})
            target = rel.get('target', {})
            rel_type = rel.get('type', '').lower()
            
            source_text = (source.get('text', '') if isinstance(source, dict) else str(source)).lower()
            target_text = (target.get('text', '') if isinstance(target, dict) else str(target)).lower()
            
            words = self._tokenize(source_text + ' ' + target_text + ' ' + rel_type)
            for word in words:
                if word not in self.stop_words and len(word) > 2:
                    if word not in self.index['relationships']:
                        self.index['relationships'][word] = []
                    self.index['relationships'][word].append(rel)

        # Index questions
        for question in results.get('questions', []):
            words = self._tokenize(question.lower())
            for word in words:
                if word not in self.stop_words and len(word) > 2:
                    if word not in self.index['questions']:
                        self.index['questions'][word] = []
                    self.index['questions'][word].append(question)

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into words.

        Args:
            text: Input text

        Returns:
            List of tokens
        """
        # Remove punctuation and split
        text = re.sub(r'[^\w\s]', ' ', text)
        return text.split()

    def search(
        self,
        query: str,
        results: Dict[str, Any],
        filters: Optional[Dict[str, Any]] = None,
        max_results: int = 100,
    ) -> Dict[str, List[SearchResult]]:
        """Search across results.

        Args:
            query: Search query string
            results: Analysis results dictionary
            filters: Optional filters (type, confidence, etc.)
            max_results: Maximum results per category

        Returns:
            Dictionary of search results by category
        """
        if not query:
            return self._filter_results(results, filters)

        # Build index if not already built
        if not self.index:
            self.build_index(results)

        query_lower = query.lower()
        query_words = self._tokenize(query_lower)

        search_results = {
            'concepts': [],
            'relationships': [],
            'chains': [],
            'questions': [],
        }

        # Search concepts
        for concept in results.get('concepts', []):
            score = self._calculate_score(concept, query_words, 'concept')
            if score > 0:
                # Apply filters
                if self._matches_filters(concept, filters):
                    highlights = self._extract_highlights(concept, query_words)
                    search_results['concepts'].append(
                        SearchResult(
                            item=concept,
                            score=score,
                            matched_fields=self._get_matched_fields(concept, query_words),
                            highlights=highlights,
                        )
                    )

        # Search relationships
        for rel in results.get('relationships', []):
            score = self._calculate_score(rel, query_words, 'relationship')
            if score > 0:
                if self._matches_filters(rel, filters):
                    highlights = self._extract_highlights(rel, query_words)
                    search_results['relationships'].append(
                        SearchResult(
                            item=rel,
                            score=score,
                            matched_fields=self._get_matched_fields(rel, query_words),
                            highlights=highlights,
                        )
                    )

        # Search questions
        for question in results.get('questions', []):
            score = self._calculate_question_score(question, query_words)
            if score > 0:
                highlights = self._extract_question_highlights(question, query_words)
                search_results['questions'].append(
                    SearchResult(
                        item={'text': question},
                        score=score,
                        matched_fields=['text'],
                        highlights={'text': highlights},
                    )
                )

        # Sort by score and limit
        for category in search_results:
            search_results[category].sort(key=lambda x: x.score, reverse=True)
            search_results[category] = search_results[category][:max_results]

        return search_results

    def _calculate_score(self, item: Dict[str, Any], query_words: List[str], item_type: str) -> float:
        """Calculate relevance score for an item.

        Args:
            item: Item to score
            query_words: Query words
            item_type: Type of item

        Returns:
            Relevance score (0.0 to 1.0)
        """
        score = 0.0
        total_words = len(query_words)

        if item_type == 'concept':
            text = item.get('text', '').lower()
            concept_type = item.get('type', '').lower()
            context = item.get('context', '').lower()
            confidence = item.get('confidence', 0.5)

            # Exact match bonus
            full_text = text + ' ' + concept_type + ' ' + context
            for word in query_words:
                if word in text:
                    score += 0.4  # High weight for text match
                elif word in concept_type:
                    score += 0.2  # Medium weight for type match
                elif word in context:
                    score += 0.1  # Lower weight for context match

            # Normalize and apply confidence
            score = min(score / total_words, 1.0) * confidence

        elif item_type == 'relationship':
            source = item.get('source', {})
            target = item.get('target', {})
            rel_type = item.get('type', '').lower()
            confidence = item.get('confidence', 0.5)

            source_text = (source.get('text', '') if isinstance(source, dict) else str(source)).lower()
            target_text = (target.get('text', '') if isinstance(target, dict) else str(target)).lower()

            for word in query_words:
                if word in source_text or word in target_text:
                    score += 0.3
                elif word in rel_type:
                    score += 0.2

            score = min(score / total_words, 1.0) * confidence

        return score

    def _calculate_question_score(self, question: str, query_words: List[str]) -> float:
        """Calculate score for a question.

        Args:
            question: Question text
            query_words: Query words

        Returns:
            Relevance score
        """
        question_lower = question.lower()
        matches = sum(1 for word in query_words if word in question_lower)
        return matches / len(query_words) if query_words else 0.0

    def _matches_filters(self, item: Dict[str, Any], filters: Optional[Dict[str, Any]]) -> bool:
        """Check if item matches filters.

        Args:
            item: Item to check
            filters: Filter criteria

        Returns:
            True if matches filters
        """
        if not filters:
            return True

        # Type filter
        if 'type' in filters and filters['type']:
            if item.get('type', '').lower() != filters['type'].lower():
                return False

        # Confidence filter
        if 'min_confidence' in filters:
            confidence = item.get('confidence', 0)
            if confidence < filters['min_confidence']:
                return False

        # Date range filter (if applicable)
        if 'date_from' in filters or 'date_to' in filters:
            # Implement date filtering if items have dates
            pass

        return True

    def _extract_highlights(self, item: Dict[str, Any], query_words: List[str]) -> Dict[str, List[str]]:
        """Extract highlighted snippets.

        Args:
            item: Item to extract from
            query_words: Query words

        Returns:
            Dictionary of highlighted snippets by field
        """
        highlights = {}

        if 'text' in item:
            text = item['text']
            snippets = self._find_snippets(text, query_words)
            if snippets:
                highlights['text'] = snippets

        if 'context' in item:
            context = item['context']
            snippets = self._find_snippets(context, query_words)
            if snippets:
                highlights['context'] = snippets

        return highlights

    def _extract_question_highlights(self, question: str, query_words: List[str]) -> List[str]:
        """Extract highlights from question.

        Args:
            question: Question text
            query_words: Query words

        Returns:
            List of highlighted snippets
        """
        return self._find_snippets(question, query_words)

    def _find_snippets(self, text: str, query_words: List[str], context_size: int = 50) -> List[str]:
        """Find snippets around query words.

        Args:
            text: Text to search
            query_words: Query words
            context_size: Characters of context around match

        Returns:
            List of snippets
        """
        text_lower = text.lower()
        snippets = []

        for word in query_words:
            if word in text_lower:
                # Find all occurrences
                start = 0
                while True:
                    idx = text_lower.find(word, start)
                    if idx == -1:
                        break

                    # Extract context
                    snippet_start = max(0, idx - context_size)
                    snippet_end = min(len(text), idx + len(word) + context_size)
                    snippet = text[snippet_start:snippet_end]

                    if snippet not in snippets:
                        snippets.append(snippet)

                    start = idx + 1

        return snippets[:3]  # Limit to 3 snippets

    def _get_matched_fields(self, item: Dict[str, Any], query_words: List[str]) -> List[str]:
        """Get list of fields that matched query.

        Args:
            item: Item to check
            query_words: Query words

        Returns:
            List of matched field names
        """
        matched = []

        text = (item.get('text', '') if isinstance(item.get('text'), str) else '').lower()
        concept_type = item.get('type', '').lower()
        context = item.get('context', '').lower()

        for word in query_words:
            if word in text:
                matched.append('text')
            if word in concept_type:
                matched.append('type')
            if word in context:
                matched.append('context')

        return list(set(matched))  # Remove duplicates

    def _filter_results(self, results: Dict[str, Any], filters: Optional[Dict[str, Any]]) -> Dict[str, List[SearchResult]]:
        """Filter results without search query.

        Args:
            results: Analysis results
            filters: Filter criteria

        Returns:
            Filtered results
        """
        if not filters:
            # Return all results as SearchResults with score 1.0
            return {
                'concepts': [SearchResult(item=c, score=1.0, matched_fields=[], highlights={}) for c in results.get('concepts', [])],
                'relationships': [SearchResult(item=r, score=1.0, matched_fields=[], highlights={}) for r in results.get('relationships', [])],
                'chains': [SearchResult(item=c, score=1.0, matched_fields=[], highlights={}) for c in results.get('reasoning_chains', [])],
                'questions': [SearchResult(item={'text': q}, score=1.0, matched_fields=[], highlights={}) for q in results.get('questions', [])],
            }

        filtered = {
            'concepts': [],
            'relationships': [],
            'chains': [],
            'questions': [],
        }

        for concept in results.get('concepts', []):
            if self._matches_filters(concept, filters):
                filtered['concepts'].append(SearchResult(item=concept, score=1.0, matched_fields=[], highlights={}))

        for rel in results.get('relationships', []):
            if self._matches_filters(rel, filters):
                filtered['relationships'].append(SearchResult(item=rel, score=1.0, matched_fields=[], highlights={}))

        for chain in results.get('reasoning_chains', []):
            filtered['chains'].append(SearchResult(item=chain, score=1.0, matched_fields=[], highlights={}))

        for question in results.get('questions', []):
            filtered['questions'].append(SearchResult(item={'text': question}, score=1.0, matched_fields=[], highlights={}))

        return filtered


class Analytics:
    """Analytics and statistics for analysis results."""

    @staticmethod
    def calculate_statistics(results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive statistics.

        Args:
            results: Analysis results

        Returns:
            Statistics dictionary
        """
        concepts = results.get('concepts', [])
        relationships = results.get('relationships', [])
        chains = results.get('reasoning_chains', [])

        # Concept statistics
        concept_types = {}
        confidence_distribution = {'high': 0, 'medium': 0, 'low': 0}
        total_confidence = 0

        for concept in concepts:
            # Type distribution
            ctype = concept.get('type', 'unknown')
            concept_types[ctype] = concept_types.get(ctype, 0) + 1

            # Confidence distribution
            confidence = concept.get('confidence', 0.5)
            total_confidence += confidence
            if confidence >= 0.7:
                confidence_distribution['high'] += 1
            elif confidence >= 0.4:
                confidence_distribution['medium'] += 1
            else:
                confidence_distribution['low'] += 1

        avg_confidence = total_confidence / len(concepts) if concepts else 0

        # Relationship statistics
        relationship_types = {}
        for rel in relationships:
            rel_type = rel.get('type', 'unknown')
            relationship_types[rel_type] = relationship_types.get(rel_type, 0) + 1

        # Chain statistics
        chain_types = {}
        chain_lengths = []
        for chain in chains:
            ctype = chain.get('type', 'unknown')
            chain_types[ctype] = chain_types.get(ctype, 0) + 1
            steps = chain.get('steps', [])
            chain_lengths.append(len(steps))

        avg_chain_length = sum(chain_lengths) / len(chain_lengths) if chain_lengths else 0

        return {
            'concepts': {
                'total': len(concepts),
                'types': concept_types,
                'average_confidence': avg_confidence,
                'confidence_distribution': confidence_distribution,
            },
            'relationships': {
                'total': len(relationships),
                'types': relationship_types,
            },
            'chains': {
                'total': len(chains),
                'types': chain_types,
                'average_length': avg_chain_length,
                'length_distribution': {
                    'short': sum(1 for l in chain_lengths if l <= 3),
                    'medium': sum(1 for l in chain_lengths if 3 < l <= 7),
                    'long': sum(1 for l in chain_lengths if l > 7),
                },
            },
            'graph': {
                'nodes': len(results.get('knowledge_graph', {}).get('nodes', [])),
                'edges': len(results.get('knowledge_graph', {}).get('edges', [])),
            },
        }
