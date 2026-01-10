"""Async API usage examples for real-world scenarios."""

import asyncio
from typing import AsyncIterator

from reasoning_core import AsyncReasoningAPI, MedicalDomain, MeetingDomain


# Example 1: Basic async processing
async def example_basic_async():
    """Basic async text processing."""
    print("\n=== Example 1: Basic Async Processing ===")

    api = AsyncReasoningAPI(domain=MedicalDomain())

    text = """
    Patient presents with acute chest pain and shortness of breath.
    ECG shows ST elevation in inferior leads.
    Troponin is significantly elevated.
    Diagnosis: acute myocardial infarction.
    Treatment: aspirin, heparin, and urgent catheterization.
    """

    result = await api.process_text_async(text)

    print(f"Extracted {len(result['concepts'])} concepts")
    print(f"Found {len(result['relationships'])} relationships")
    print(f"Built {len(result['reasoning_chains'])} reasoning chains")

    # Print some concepts
    print("\nSample concepts:")
    for concept in result["concepts"][:5]:
        print(f"  - {concept['text']} ({concept['type']})")


# Example 2: Streaming processing (for real-time transcription)
async def example_streaming_transcription():
    """Simulate streaming medical transcription processing."""
    print("\n=== Example 2: Streaming Transcription ===")

    api = AsyncReasoningAPI(domain=MedicalDomain())

    # Simulate streaming transcription from speech-to-text
    async def transcription_stream() -> AsyncIterator[str]:
        """Simulate real-time transcription chunks."""
        chunks = [
            "Patient presents with chest pain ",
            "radiating to left arm. ",
            "Blood pressure is elevated. ",
            "ECG shows ST segment elevation. ",
            "Troponin levels are rising. ",
            "Clinical diagnosis is acute MI. ",
            "Initiating treatment with aspirin ",
            "and preparing for catheterization.",
        ]

        for chunk in chunks:
            await asyncio.sleep(0.5)  # Simulate transcription delay
            yield chunk

    # Track progress
    def progress_callback(chunk_num: int, text: str):
        print(f"  Processing chunk {chunk_num}: {text[:50]}...")

    # Process stream
    all_concepts = []
    async for result in api.process_stream(
        transcription_stream(),
        chunk_size=100,
        overlap=20,
        progress_callback=progress_callback,
    ):
        chunk_concepts = len(result["concepts"])
        all_concepts.extend(result["concepts"])
        print(f"    → Found {chunk_concepts} concepts in chunk {result['chunk_num']}")

    print(f"\nTotal concepts extracted: {len(all_concepts)}")


# Example 3: Batch processing multiple documents
async def example_batch_processing():
    """Process multiple medical documents concurrently."""
    print("\n=== Example 3: Batch Document Processing ===")

    api = AsyncReasoningAPI(domain=MedicalDomain(), max_workers=3)

    # Multiple patient cases
    documents = [
        "Case 1: Patient with acute MI. ECG shows ST elevation. Troponin elevated.",
        "Case 2: Suspected pneumonia. Fever, cough, dyspnea. Chest X-ray shows infiltrate.",
        "Case 3: Diabetic ketoacidosis. High glucose, ketones, acidosis. IV insulin started.",
        "Case 4: Stroke presentation. Facial droop, arm weakness, speech difficulty.",
        "Case 5: Sepsis with hypotension. Blood cultures positive. Broad spectrum antibiotics.",
    ]

    # Progress tracking
    def progress_callback(completed: int, total: int):
        print(f"  Progress: {completed}/{total} documents processed")

    # Process all documents concurrently
    results = await api.process_batch(
        documents, progress_callback=progress_callback
    )

    print("\nResults summary:")
    for i, result in enumerate(results, 1):
        concepts = len(result.get("concepts", []))
        chains = len(result.get("reasoning_chains", []))
        print(f"  Case {i}: {concepts} concepts, {chains} reasoning chains")


# Example 4: Merging stream results
async def example_merge_stream_results():
    """Process stream and merge results into unified output."""
    print("\n=== Example 4: Merge Stream Results ===")

    api = AsyncReasoningAPI(domain=MedicalDomain())

    long_transcript = """
    Patient is a 65-year-old male presenting with acute chest pain.
    Pain started 2 hours ago, described as crushing, radiating to left arm.
    Associated symptoms include diaphoresis, nausea, and dyspnea.
    Past medical history significant for hypertension and hyperlipidemia.
    Medications include lisinopril and atorvastatin.
    On exam: BP 150/90, HR 105, RR 20, O2 sat 95% on room air.
    Cardiovascular exam reveals S4 gallop, no murmurs.
    ECG shows ST elevation in leads II, III, aVF consistent with inferior STEMI.
    Troponin I elevated at 8.5 ng/mL.
    Decision made for urgent cardiac catheterization.
    Angiography revealed 100% occlusion of right coronary artery.
    Successful PCI with drug-eluting stent placement.
    Patient stable post-procedure on dual antiplatelet therapy.
    """

    # Create stream
    async def create_stream() -> AsyncIterator[str]:
        for i in range(0, len(long_transcript), 150):
            await asyncio.sleep(0.1)
            yield long_transcript[i : i + 150]

    # Process and merge
    stream_results = api.process_stream(create_stream(), chunk_size=300)
    merged = await api.merge_stream_results(stream_results)

    print(f"Processed {merged['chunk_count']} chunks")
    print(f"Total unique concepts: {len(merged['concepts'])}")
    print(f"Total relationships: {len(merged['relationships'])}")
    print(f"Total reasoning chains: {len(merged['reasoning_chains'])}")

    # Show concept types
    concept_types = {}
    for concept in merged["concepts"]:
        ctype = concept["type"]
        concept_types[ctype] = concept_types.get(ctype, 0) + 1

    print("\nConcepts by type:")
    for ctype, count in sorted(concept_types.items()):
        print(f"  {ctype}: {count}")


# Example 5: Real-time meeting notes with async
async def example_meeting_notes():
    """Process meeting transcription in real-time."""
    print("\n=== Example 5: Real-Time Meeting Notes ===")

    api = AsyncReasoningAPI(domain=MeetingDomain())

    # Simulate meeting transcription
    async def meeting_stream() -> AsyncIterator[str]:
        meeting_chunks = [
            "Let's discuss the Q1 roadmap. ",
            "First priority is the authentication feature. ",
            "Sarah will lead the backend implementation. ",
            "Target deadline is March 15th. ",
            "Second item: database migration. ",
            "John volunteers to handle this. ",
            "We need to complete testing by February 28th. ",
            "Action item: schedule follow-up next week.",
        ]

        for chunk in meeting_chunks:
            await asyncio.sleep(0.3)
            yield chunk

    print("Processing meeting transcription...\n")

    async for result in api.process_stream(
        meeting_stream(), chunk_size=80, overlap=15
    ):
        if result["concepts"]:
            print(f"Chunk {result['chunk_num']}:")
            for concept in result["concepts"][:3]:  # Show first 3
                print(f"  - {concept['text']} [{concept['type']}]")


# Example 6: Using async context manager
async def example_context_manager():
    """Use async context manager for automatic cleanup."""
    print("\n=== Example 6: Async Context Manager ===")

    text = "Patient diagnosed with pneumonia. Treatment: antibiotics and supportive care."

    async with AsyncReasoningAPI(domain=MedicalDomain()) as api:
        result = await api.process_text_async(text)
        print(f"Extracted {len(result['concepts'])} concepts")
        print("API resources cleaned up automatically")


# Example 7: Concurrent processing of multiple streams
async def example_concurrent_streams():
    """Process multiple streams concurrently."""
    print("\n=== Example 7: Concurrent Stream Processing ===")

    api = AsyncReasoningAPI(domain=MedicalDomain())

    # Multiple transcription sources
    async def stream1() -> AsyncIterator[str]:
        texts = ["Patient A: chest pain. ", "ECG abnormal. ", "Troponin elevated."]
        for text in texts:
            await asyncio.sleep(0.2)
            yield text

    async def stream2() -> AsyncIterator[str]:
        texts = ["Patient B: fever and cough. ", "X-ray shows pneumonia. ", "Antibiotics started."]
        for text in texts:
            await asyncio.sleep(0.2)
            yield text

    # Process both streams concurrently
    async def process_stream(stream_id: str, stream: AsyncIterator[str]):
        concepts_count = 0
        async for result in api.process_stream(stream, chunk_size=50):
            concepts_count += len(result["concepts"])
        print(f"  {stream_id}: {concepts_count} total concepts")

    await asyncio.gather(
        process_stream("Stream 1", stream1()),
        process_stream("Stream 2", stream2()),
    )


# Example 8: Integration with CogniScribe
async def example_cogniscribe_integration():
    """Example integration with CogniScribe medical transcription."""
    print("\n=== Example 8: CogniScribe Integration ===")

    api = AsyncReasoningAPI(domain=MedicalDomain())

    # Simulate CogniScribe transcription output
    async def cogniscribe_transcription() -> AsyncIterator[str]:
        """Simulate real-time medical lecture transcription."""
        lecture_chunks = [
            "Today we're discussing acute coronary syndrome. ",
            "The pathophysiology involves plaque rupture and thrombosis. ",
            "Clinical presentation includes chest pain, often described as crushing or pressure. ",
            "Diagnostic workup includes ECG, troponin, and cardiac enzymes. ",
            "STEMI requires immediate reperfusion therapy. ",
            "Treatment options include PCI or thrombolysis. ",
            "Prognosis depends on time to treatment and extent of damage.",
        ]

        for chunk in lecture_chunks:
            await asyncio.sleep(0.4)  # Simulate transcription speed
            yield chunk

    print("Processing medical lecture transcription...\n")

    results = []
    async for result in api.process_stream(
        cogniscribe_transcription(), chunk_size=120, include_graph=True
    ):
        results.append(result)
        print(f"Chunk {result['chunk_num']}: "
              f"{len(result['concepts'])} concepts, "
              f"{len(result['reasoning_chains'])} chains")

    # Merge results for final knowledge graph
    async def result_iterator():
        for r in results:
            yield r

    merged = await api.merge_stream_results(result_iterator())

    print(f"\nFinal merged results:")
    print(f"  Total concepts: {len(merged['concepts'])}")
    print(f"  Knowledge graph nodes: {len(merged['knowledge_graph']['nodes'])}")
    print(f"  Knowledge graph edges: {len(merged['knowledge_graph']['edges'])}")


# Main execution
async def main():
    """Run all examples."""
    examples = [
        example_basic_async,
        example_streaming_transcription,
        example_batch_processing,
        example_merge_stream_results,
        example_meeting_notes,
        example_context_manager,
        example_concurrent_streams,
        example_cogniscribe_integration,
    ]

    print("\n" + "=" * 60)
    print("ASYNC REASONING API - USAGE EXAMPLES")
    print("=" * 60)

    for example in examples:
        try:
            await example()
        except Exception as e:
            print(f"\n❌ Error in {example.__name__}: {e}")

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
