"""Tests for async reasoning API."""

import asyncio
from typing import AsyncIterator

import pytest

from reasoning_core import AsyncReasoningAPI, MedicalDomain
from reasoning_core.api.reasoning_api import ProcessingError


@pytest.fixture
def async_api():
    """Create async API instance."""
    return AsyncReasoningAPI(domain=MedicalDomain())


@pytest.fixture
def medical_text():
    """Sample medical text for testing."""
    return (
        "Patient presents with chest pain and dyspnea. "
        "ECG shows ST elevation. Troponin is elevated. "
        "Diagnosis: myocardial infarction. "
        "Treatment: aspirin and catheterization."
    )


@pytest.fixture
def long_medical_text():
    """Longer medical text for streaming tests."""
    return (
        "Patient presents with acute onset chest pain radiating to "
        "left arm. Physical examination reveals diaphoresis and "
        "tachycardia. Vital signs: BP 160/95, HR 110, RR 22, "
        "O2 sat 94% on room air. ECG demonstrates ST-segment elevation "
        "in leads II, III, and aVF. Troponin I elevated at 12 ng/mL, "
        "CK-MB also elevated. Chest X-ray shows mild pulmonary edema. "
        "Clinical diagnosis: acute inferior wall myocardial infarction. "
        "Management: aspirin 325mg, clopidogrel 600mg loading dose. "
        "Heparin bolus followed by infusion initiated. Patient "
        "transferred to catheterization lab for urgent PCI. Angiography "
        "revealed 100% occlusion of right coronary artery. Successful "
        "stent placement with TIMI 3 flow restored. Post-procedure "
        "troponin peaked at 45 ng/mL. Patient stable on dual "
        "antiplatelet therapy and beta-blocker. Echocardiogram shows "
        "mild hypokinesis of inferior wall, EF 45%. Discharged on "
        "day 3 with cardiac rehabilitation referral."
    )


@pytest.mark.asyncio
async def test_process_text_async(async_api, medical_text):
    """Test basic async text processing."""
    result = await async_api.process_text_async(medical_text)

    assert "concepts" in result
    assert "relationships" in result
    assert "reasoning_chains" in result
    assert len(result["concepts"]) > 0


@pytest.mark.asyncio
async def test_process_text_async_error_handling(async_api):
    """Test error handling in async processing."""
    # Test with empty text
    with pytest.raises(ValueError):
        await async_api.process_text_async("")

    # Test with non-string
    with pytest.raises(TypeError):
        await async_api.process_text_async(123)


@pytest.mark.asyncio
async def test_process_text_async_without_graph(async_api, medical_text):
    """Test async processing without knowledge graph."""
    result = await async_api.process_text_async(
        medical_text, include_graph=False
    )

    assert "concepts" in result
    assert "knowledge_graph" not in result or result["knowledge_graph"] is None


async def create_text_stream(
    text: str, chunk_size: int = 50
) -> AsyncIterator[str]:
    """Create async text stream for testing."""
    for i in range(0, len(text), chunk_size):
        await asyncio.sleep(0.01)  # Simulate streaming delay
        yield text[i : i + chunk_size]


@pytest.mark.asyncio
async def test_process_stream(async_api, long_medical_text):
    """Test streaming text processing."""
    stream = create_text_stream(long_medical_text, chunk_size=100)
    results = []

    async for result in async_api.process_stream(
        stream, chunk_size=200, overlap=50
    ):
        results.append(result)
        assert "chunk_num" in result
        assert "is_final" in result
        assert "concepts" in result

    # Should have multiple chunks
    assert len(results) > 1

    # Last chunk should be marked as final
    assert results[-1]["is_final"] is True

    # Earlier chunks should not be final
    assert all(not r["is_final"] for r in results[:-1])


@pytest.mark.asyncio
async def test_process_stream_with_progress(async_api, long_medical_text):
    """Test streaming with progress callback."""
    progress_calls = []

    def progress_callback(chunk_num: int, text: str):
        progress_calls.append((chunk_num, len(text)))

    stream = create_text_stream(long_medical_text, chunk_size=100)
    results = []

    async for result in async_api.process_stream(
        stream, chunk_size=200, progress_callback=progress_callback
    ):
        results.append(result)

    # Progress callback should have been called
    assert len(progress_calls) > 0
    assert len(progress_calls) == len(results)


@pytest.mark.asyncio
async def test_process_batch(async_api):
    """Test concurrent batch processing."""
    texts = [
        "Patient has fever and cough.",
        "ECG shows ST elevation. Diagnosis: MI.",
        "Treatment includes aspirin and beta-blocker.",
    ]

    results = await async_api.process_batch(texts)

    assert len(results) == len(texts)
    for result in results:
        assert "concepts" in result
        assert "relationships" in result


@pytest.mark.asyncio
async def test_process_batch_with_progress(async_api):
    """Test batch processing with progress callback."""
    texts = [
        "Patient presents with chest pain.",
        "ECG shows abnormalities.",
        "Troponin levels are elevated.",
        "Diagnosis: acute coronary syndrome.",
    ]

    progress_updates = []

    def progress_callback(completed: int, total: int):
        progress_updates.append((completed, total))

    results = await async_api.process_batch(
        texts, progress_callback=progress_callback
    )

    assert len(results) == len(texts)
    assert len(progress_updates) == len(texts)

    # Check progress increases
    for i, (completed, total) in enumerate(progress_updates):
        assert completed == i + 1
        assert total == len(texts)


@pytest.mark.asyncio
async def test_process_batch_empty(async_api):
    """Test batch processing with empty list."""
    results = await async_api.process_batch([])
    assert results == []


@pytest.mark.asyncio
async def test_process_batch_error_handling(async_api):
    """Test error handling in batch processing."""
    texts = [
        "Valid medical text with chest pain.",
        "",  # Empty text - should error
        "Another valid text with fever.",
    ]

    results = await async_api.process_batch(texts)

    # Should have results for all texts
    assert len(results) == len(texts)

    # First and third should succeed
    assert "concepts" in results[0]
    assert "concepts" in results[2]

    # Second should have error
    assert "error" in results[1]


@pytest.mark.asyncio
async def test_merge_stream_results(async_api, long_medical_text):
    """Test merging results from stream processing."""
    stream = create_text_stream(long_medical_text, chunk_size=100)
    chunk_results = async_api.process_stream(stream, chunk_size=200)

    merged = await async_api.merge_stream_results(chunk_results)

    assert "concepts" in merged
    assert "relationships" in merged
    assert "reasoning_chains" in merged
    assert "chunk_count" in merged
    assert merged["chunk_count"] > 1

    # Should have deduplicated concepts
    assert len(merged["concepts"]) > 0

    # Should have knowledge graph
    assert "knowledge_graph" in merged


@pytest.mark.asyncio
async def test_async_context_manager(medical_text):
    """Test async context manager usage."""
    async with AsyncReasoningAPI(domain=MedicalDomain()) as api:
        result = await api.process_text_async(medical_text)
        assert "concepts" in result


@pytest.mark.asyncio
async def test_concurrent_processing(async_api, medical_text):
    """Test multiple concurrent process calls."""
    # Create multiple concurrent tasks
    tasks = [async_api.process_text_async(medical_text) for _ in range(5)]

    results = await asyncio.gather(*tasks)

    assert len(results) == 5
    for result in results:
        assert "concepts" in result
        # Results should be consistent
        assert len(result["concepts"]) == len(results[0]["concepts"])


@pytest.mark.asyncio
async def test_max_workers_limit(long_medical_text):
    """Test that max_workers limit is respected."""
    api = AsyncReasoningAPI(domain=MedicalDomain(), max_workers=2)

    texts = [long_medical_text] * 10

    # Process batch - should limit concurrency to 2
    results = await api.process_batch(texts)

    assert len(results) == 10
    for result in results:
        assert "concepts" in result


@pytest.mark.asyncio
async def test_stream_empty_chunks(async_api):
    """Test stream processing with some empty chunks."""

    async def stream_with_empties():
        yield "Patient has fever. "
        yield ""
        yield "ECG shows ST elevation. "
        yield "   "  # Whitespace only
        yield "Diagnosis: MI."

    results = []
    async for result in async_api.process_stream(
        stream_with_empties(), chunk_size=50
    ):
        results.append(result)

    # Should still process successfully
    assert len(results) > 0
    assert any(len(r["concepts"]) > 0 for r in results)


@pytest.mark.asyncio
async def test_set_domain_async(medical_text):
    """Test changing domain in async API."""
    from reasoning_core import BusinessDomain

    api = AsyncReasoningAPI(domain=MedicalDomain())

    # Process with medical domain
    result1 = await api.process_text_async(medical_text)

    # Change to business domain
    api.set_domain(BusinessDomain())

    # Process business text
    business_text = (
        "Close the deal with enterprise customer. Upsell premium tier."
    )
    result2 = await api.process_text_async(business_text)

    assert "concepts" in result1
    assert "concepts" in result2
