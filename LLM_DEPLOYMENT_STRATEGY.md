# LLM Deployment Strategy for Reasoning Core

## Local Model Installation Options

### Option 1: Ollama with Bundled Model (Recommended)

**Approach:** Include Ollama installer and optionally pre-download a small model.

**Pros:**
- ✅ Fully local, no internet required after installation
- ✅ Privacy-preserving (data never leaves device)
- ✅ Fast inference (no network latency)
- ✅ Works offline

**Cons:**
- ❌ Larger installer size (~500MB - 2GB for model)
- ❌ Requires more disk space (~4-8GB total)
- ❌ Initial download time during installation

**Implementation:**
```bash
# During installation
if [ ! -f "$INSTALL_DIR/.ollama-installed" ]; then
    echo "Installing Ollama..."
    curl -fsSL https://ollama.ai/install.sh | sh
    
    echo "Downloading model (this may take a few minutes)..."
    ollama pull llama3.2:3b  # ~2GB model
    
    touch "$INSTALL_DIR/.ollama-installed"
fi
```

### Option 2: Ollama with Optional Model Download

**Approach:** Install Ollama but let users download models on-demand.

**Pros:**
- ✅ Smaller installer (~50MB)
- ✅ Users choose which model to use
- ✅ Can update models easily

**Cons:**
- ❌ Requires internet for first use
- ❌ Users need to manually pull models

**Implementation:**
```bash
# During installation
install_ollama_if_needed() {
    if ! command -v ollama &> /dev/null; then
        echo "Installing Ollama..."
        curl -fsSL https://ollama.ai/install.sh | sh
    fi
}

# On first LLM use
if ! ollama list | grep -q llama3.2:3b; then
    echo "Downloading model (this may take a few minutes)..."
    ollama pull llama3.2:3b
fi
```

### Option 3: Bundled Quantized Model (Advanced)

**Approach:** Include a quantized model file directly in the installer.

**Pros:**
- ✅ No external dependencies
- ✅ Works completely offline
- ✅ Smaller than full models (1-3GB vs 4-8GB)

**Cons:**
- ❌ Complex to implement
- ❌ Requires maintaining model files
- ❌ Larger installer

**Tools:**
- Use `llama.cpp` with GGUF format
- Or `transformers` with quantized models

### Recommendation

**Use Option 2 (Optional Model Download)** for initial release:
1. Smaller installer
2. Flexibility for users
3. Easy to upgrade to Option 1 later

**Allow users to choose:**
```bash
./install-unified.sh --with-llm-model  # Downloads model during install
./install-unified.sh                    # Downloads model on first use
```

## Storage Considerations

### Model Sizes
- **Llama 3.2 3B** (4-bit): ~2GB
- **Llama 3.2 3B** (8-bit): ~3.5GB
- **Phi-3 Mini** (4-bit): ~2.5GB
- **Mistral 7B** (4-bit): ~4GB

### Recommended Disk Space
- Minimum: 5GB free
- Recommended: 10GB free
- With multiple models: 20GB+

## Platform-Specific Considerations

### macOS
- Ollama installs to `~/.ollama`
- Models stored in `~/.ollama/models`
- Can use system-wide installation

### Windows
- Ollama installs to `%LOCALAPPDATA%\Programs\Ollama`
- Models in `%USERPROFILE%\.ollama\models`
- Can use system-wide installation

### Linux
- Ollama installs to `/usr/local/bin/ollama` or `~/.local/bin/ollama`
- Models in `~/.ollama/models`

## Installation Integration

### Updated install-unified.sh

```bash
# Add LLM option
INSTALL_LLM=false
DOWNLOAD_MODEL=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --with-llm)
            INSTALL_LLM=true
            ;;
        --with-llm-model)
            INSTALL_LLM=true
            DOWNLOAD_MODEL=true
            ;;
        --no-start)
            NO_START=true
            ;;
        *)
            ;;
    esac
    shift
done

# Install Ollama if requested
if [ "$INSTALL_LLM" = true ]; then
    install_ollama
    if [ "$DOWNLOAD_MODEL" = true ]; then
        download_model
    fi
fi
```

## Configuration

### Environment Variables

```bash
# .env or config file
REASONING_CORE_LLM_ENABLED=true
REASONING_CORE_LLM_MODEL=llama3.2:3b
REASONING_CORE_LLM_URL=http://localhost:11434
REASONING_CORE_LLM_AUTO_DOWNLOAD=true
```

### UI Configuration

Add LLM settings to SettingsPanel:
- Enable/Disable LLM
- Select model
- Configure Ollama URL
- Auto-download models option

## Fallback Strategy

Always maintain pattern-based extraction as fallback:

```python
def extract(self, text: str) -> List[Concept]:
    # Try LLM first if enabled
    if self.llm_service and self.llm_enabled:
        try:
            concepts = self.llm_service.extract_concepts(text)
            if concepts:
                return concepts
        except Exception as e:
            logger.warning(f"LLM extraction failed: {e}, falling back to patterns")
    
    # Fallback to pattern-based
    return self._pattern_extraction(text)
```
