# Copy these values into your current PowerShell session before using Threads API scripts.
# Do not commit or share real app secrets or access tokens.

$env:THREADS_APP_ID = "YOUR_THREADS_APP_ID"
$env:THREADS_APP_SECRET = "YOUR_THREADS_APP_SECRET"
$env:THREADS_REDIRECT_URI = "https://YOUR_REGISTERED_REDIRECT_URI"

$env:THREADS_ACCESS_TOKEN = "YOUR_THREADS_ACCESS_TOKEN"
$env:OPENROUTER_API_KEY = "YOUR_OPENROUTER_API_KEY"
$env:OPENROUTER_MODEL = "google/gemma-4-26b-a4b-it:free"
$env:OPENAI_API_KEY = "YOUR_OPENAI_API_KEY"
$env:OPENAI_MODEL = "gpt-5.6-terra"
$env:GROQ_API_KEY = "YOUR_GROQ_API_KEY"
$env:GROQ_MODEL = "openai/gpt-oss-120b"
$env:LLM_FALLBACK_PROVIDERS = "openai,groq"

# Used only during token exchange.
$env:THREADS_SHORT_LIVED_ACCESS_TOKEN = "YOUR_SHORT_LIVED_THREADS_TOKEN"

# Build OAuth URL:
# .\threads-build-auth-url.ps1 -Open

# Exchange callback code for a short-lived token:
# .\threads-exchange-code.ps1 -Code "CODE_FROM_REDIRECT_URL"

# Exchange short-lived token for long-lived token:
# .\threads-exchange-long-lived-token.ps1

# Verify identity and find user id:
# .\threads-get-me.ps1

# Test approved-thread-chain.txt without publishing:
# .\scripts\publish-approved-chain.ps1 -DryRun

# Publish approved-thread-chain.txt and record metrics:
# .\scripts\publish-approved-chain.ps1
