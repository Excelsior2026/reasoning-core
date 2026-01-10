"""Async API for reasoning extraction with streaming support."""

import asyncio
from typing import Dict, Optional, List, AsyncIterator, Callable
from dataclasses import asdict

from reasoning_core.api.reasoning_api import ReasoningAPI, ProcessingError
from reasoning_core.plugins.base_domain import BaseDomain


class AsyncReasoningAPI(ReasoningAPI):
    """Async API for reasoning extraction with streaming and batch support.
    
    Extends ReasoningAPI with async methods for:
    - Non-blocking text processing
    - Streaming text chunk processing
    - Concurrent batch processing
    - Real-time transcription integration
    """

    def __init__(self, domain: Optional[BaseDomain] = None, max_workers: int = 4):
        """Initialize async reasoning API.

        Args:
            domain: Domain plugin for specialized extraction
            max_workers: Maximum concurrent workers for batch processing

        Raises:
            TypeError: If domain is not None and not a BaseDomain instance
        """
        super().__init__(domain=domain)
        self.max_workers = max_workers
        self._executor = None

    async def process_text_async(
        self, text: str, include_graph: bool = True
    ) -> Dict:
        """Process text asynchronously.

        Args:
            text: Input text to process
            include_graph: Whether to build knowledge graph

        Returns:
            Dictionary containing extracted reasoning

        Raises:
            TypeError: If text is not a string
            ValueError: If text is empty
            ProcessingError: If processing fails
        """
        # Run synchronous processing in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor, self.process_text, text, include_graph
        )

    async def process_stream(
        self,
        text_stream: AsyncIterator[str],
        chunk_size: int = 1000,
        overlap: int = 100,
        include_graph: bool = True,
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ) -> AsyncIterator[Dict]:
        """Process streaming text in chunks with overlap.

        Useful for real-time transcription where text arrives incrementally.
        Maintains context between chunks using overlap.

        Args:
            text_stream: Async iterator of text chunks
            chunk_size: Minimum characters to accumulate before processing
            overlap: Characters to overlap between chunks for context
            include_graph: Whether to build knowledge graph for each chunk
            progress_callback: Optional callback(chunk_num, text) for progress

        Yields:
            Processing results for each chunk with metadata

        Example:
            async for result in api.process_stream(transcript_stream):
                print(f"Processed chunk {result['chunk_num']}")
                concepts = result['concepts']
        """
        buffer = ""
        previous_overlap = ""
        chunk_num = 0

        async for chunk in text_stream:
            buffer += chunk

            # Process when buffer exceeds chunk_size
            while len(buffer) >= chunk_size:
                # Extract text to process (includes previous overlap)
                text_to_process = previous_overlap + buffer[:chunk_size]

                # Store overlap for next iteration
                previous_overlap = buffer[chunk_size - overlap : chunk_size]

                # Remove processed text from buffer (keep overlap)
                buffer = buffer[chunk_size - overlap :]

                chunk_num += 1

                # Call progress callback if provided
                if progress_callback:
                    progress_callback(chunk_num, text_to_process[:100] + "...")

                try:
                    result = await self.process_text_async(
                        text_to_process, include_graph=include_graph
                    )
                    result["chunk_num"] = chunk_num
                    result["is_final"] = False
                    yield result
                except ProcessingError as e:
                    # Yield error but continue processing
                    yield {
                        "chunk_num": chunk_num,
                        "is_final": False,
                        "error": str(e),
                        "concepts": [],
                        "relationships": [],
                        "reasoning_chains": [],
                    }

        # Process remaining buffer with overlap
        if buffer.strip() or previous_overlap.strip():
            final_text = previous_overlap + buffer
            chunk_num += 1

            if progress_callback:
                progress_callback(chunk_num, "Final chunk")

            try:
                result = await self.process_text_async(
                    final_text, include_graph=include_graph
                )
                result["chunk_num"] = chunk_num
                result["is_final"] = True
                yield result
            except ProcessingError as e:
                yield {
                    "chunk_num": chunk_num,
                    "is_final": True,
                    "error": str(e),
                    "concepts": [],
                    "relationships": [],
                    "reasoning_chains": [],
                }

    async def process_batch(
        self,
        texts: List[str],
        include_graph: bool = True,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> List[Dict]:
        """Process multiple texts concurrently.

        Args:
            texts: List of texts to process
            include_graph: Whether to build knowledge graphs
            progress_callback: Optional callback(completed, total) for progress

        Returns:
            List of processing results in same order as input

        Example:
            texts = [lecture1, lecture2, lecture3]
            results = await api.process_batch(texts)
            for i, result in enumerate(results):
                print(f"Document {i}: {len(result['concepts'])} concepts")
        """
        if not texts:
            return []

        total = len(texts)
        completed = 0
        results = [None] * total  # Preserve order

        # Create semaphore to limit concurrent tasks
        semaphore = asyncio.Semaphore(self.max_workers)

        async def process_with_semaphore(index: int, text: str) -> None:
            """Process single text with semaphore."""
            nonlocal completed

            async with semaphore:
                try:
                    result = await self.process_text_async(
                        text, include_graph=include_graph
                    )
                    results[index] = result
                except ProcessingError as e:
                    # Store error result
                    results[index] = {
                        "error": str(e),
                        "concepts": [],
                        "relationships": [],
                        "reasoning_chains": [],
                    }

                completed += 1
                if progress_callback:
                    progress_callback(completed, total)

        # Create tasks for all texts
        tasks = [
            asyncio.create_task(process_with_semaphore(i, text))
            for i, text in enumerate(texts)
        ]

        # Wait for all tasks to complete
        await asyncio.gather(*tasks)

        return results

    async def merge_stream_results(
        self, stream_results: AsyncIterator[Dict]
    ) -> Dict:
        """Merge results from streaming processing into single result.

        Combines concepts, relationships, and chains from all chunks,
        removing duplicates and building unified knowledge graph.

        Args:
            stream_results: Async iterator of chunk results

        Returns:
            Merged result dictionary with all extracted information
        """
        all_concepts = []
        all_relationships = []
        all_chains = []
        seen_concepts = set()  # Track unique concepts
        seen_relationships = set()  # Track unique relationships
        chunk_count = 0

        async for result in stream_results:
            if "error" in result:
                continue  # Skip error chunks

            chunk_count += 1

            # Add unique concepts
            for concept in result.get("concepts", []):
                concept_key = (concept["text"], concept["type"])
                if concept_key not in seen_concepts:
                    seen_concepts.add(concept_key)
                    all_concepts.append(concept)

            # Add unique relationships
            for rel in result.get("relationships", []):
                rel_key = (
                    rel["source"]["text"],
                    rel["target"]["text"],
                    rel["type"],
                )
                if rel_key not in seen_relationships:
                    seen_relationships.add(rel_key)
                    all_relationships.append(rel)

            # Add all chains (may have duplicates across chunks)
            all_chains.extend(result.get("reasoning_chains", []))

        # Build unified knowledge graph if we have concepts
        merged_result = {
            "concepts": all_concepts,
            "relationships": all_relationships,
            "reasoning_chains": all_chains,
            "chunk_count": chunk_count,
        }

        # Build knowledge graph from merged data
        if all_concepts:
            try:
                # Reconstruct concept objects for graph building
                from reasoning_core.extractors.concept_extractor import Concept
                from reasoning_core.extractors.relationship_mapper import Relationship

                concepts = [
                    Concept(
                        text=c["text"],
                        type=c["type"],
                        position=c.get("position", 0),
                        context=c.get("context", ""),
                        confidence=c.get("confidence", 1.0),
                    )
                    for c in all_concepts
                ]

                relationships = [
                    Relationship(
                        source=Concept(
                            text=r["source"]["text"],
                            type=r["source"]["type"],
                            position=r["source"].get("position", 0),
                            context=r["source"].get("context", ""),
                            confidence=r["source"].get("confidence", 1.0),
                        ),
                        target=Concept(
                            text=r["target"]["text"],
                            type=r["target"]["type"],
                            position=r["target"].get("position", 0),
                            context=r["target"].get("context", ""),
                            confidence=r["target"].get("confidence", 1.0),
                        ),
                        type=r["type"],
                        evidence=r.get("evidence", ""),
                        confidence=r.get("confidence", 1.0),
                    )
                    for r in all_relationships
                ]

                graph = self._build_knowledge_graph(concepts, relationships)
                merged_result["knowledge_graph"] = graph.to_dict()
            except Exception as e:
                merged_result["knowledge_graph"] = None
                merged_result["graph_error"] = str(e)

        return merged_result

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._executor:
            self._executor.shutdown(wait=True)
        return False
