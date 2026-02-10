"""Interactive setup wizard for Mnemosyne."""

import os
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table

from mnemosyne.config.schema import (
    LLMProvider,
    EmbeddingProvider,
    CuriosityMode,
    LLMConfig,
    EmbeddingConfig,
    CuriosityConfig,
)
from mnemosyne.config.settings import Settings, save_settings, ensure_config_dir


console = Console()


def run_setup():
    """Run the interactive setup wizard."""
    console.print(Panel(
        "[bold cyan]Welcome to Mnemosyne Setup[/bold cyan]\n\n"
        "This wizard will help you configure Mnemosyne.\n"
        "Your configuration will be saved to ~/.mnemosyne/config.toml",
        title="Mnemosyne Setup",
    ))
    console.print()
    
    # Step 1: LLM Provider
    llm_config = setup_llm_provider()
    console.print()
    
    # Step 2: Embedding Provider
    embedding_config = setup_embedding_provider()
    console.print()
    
    # Step 3: Curiosity Mode
    curiosity_config = setup_curiosity_mode()
    console.print()
    
    # Save configuration
    settings = Settings(
        llm=llm_config,
        embedding=embedding_config,
        curiosity=curiosity_config,
    )
    
    config_dir = ensure_config_dir()
    config_path = config_dir / "config.toml"
    save_settings(settings, config_path)
    
    console.print(Panel(
        f"[bold green]Setup complete![/bold green]\n\n"
        f"Configuration saved to: {config_path}\n\n"
        f"You can now start recording with:\n"
        f"  [cyan]mnemosyne record[/cyan]",
        title="Setup Complete",
    ))


def setup_llm_provider() -> LLMConfig:
    """Setup LLM provider interactively."""
    console.print("[bold]Step 1/3: LLM Provider[/bold]")
    console.print("─" * 40)
    
    # Show provider options
    table = Table(show_header=True, header_style="bold")
    table.add_column("#", style="dim", width=3)
    table.add_column("Provider", width=15)
    table.add_column("Models", width=40)
    
    providers = [
        ("OpenAI", "GPT-4o, GPT-4-turbo, GPT-4o-mini"),
        ("Anthropic", "Claude 3.5 Sonnet, Claude 3 Opus/Haiku"),
        ("Google", "Gemini 1.5 Pro, Gemini 1.5 Flash"),
        ("Ollama", "Llama 3, Mistral, etc. (Local)"),
        ("Custom", "Any OpenAI-compatible API"),
    ]
    
    for i, (name, models) in enumerate(providers, 1):
        table.add_row(str(i), name, models)
    
    console.print(table)
    console.print()
    
    choice = Prompt.ask(
        "Choose your LLM provider",
        choices=["1", "2", "3", "4", "5"],
        default="2",
    )
    
    provider_map = {
        "1": LLMProvider.OPENAI,
        "2": LLMProvider.ANTHROPIC,
        "3": LLMProvider.GOOGLE,
        "4": LLMProvider.OLLAMA,
        "5": LLMProvider.CUSTOM,
    }
    provider = provider_map[choice]
    
    # Get API key (if needed)
    api_key = None
    api_key_env = None
    base_url = None
    
    if provider != LLMProvider.OLLAMA:
        env_var_map = {
            LLMProvider.OPENAI: "OPENAI_API_KEY",
            LLMProvider.ANTHROPIC: "ANTHROPIC_API_KEY",
            LLMProvider.GOOGLE: "GOOGLE_API_KEY",
            LLMProvider.CUSTOM: None,
        }
        
        env_var = env_var_map.get(provider)
        
        if env_var and os.environ.get(env_var):
            console.print(f"[green]Found {env_var} in environment[/green]")
            api_key_env = env_var
        else:
            console.print()
            if provider == LLMProvider.CUSTOM:
                base_url = Prompt.ask("Enter API base URL")
            
            api_key = Prompt.ask(
                f"Enter your API key",
                password=True,
            )
            
            # Verify the key
            console.print("Verifying API key...", end=" ")
            if verify_api_key(provider, api_key, base_url):
                console.print("[green]Valid[/green]")
            else:
                console.print("[yellow]Could not verify (continuing anyway)[/yellow]")
    else:
        base_url = Prompt.ask(
            "Enter Ollama URL",
            default="http://localhost:11434",
        )
    
    # Select model
    model = select_model(provider)
    
    return LLMConfig(
        provider=provider,
        model=model,
        api_key=api_key,
        api_key_env=api_key_env,
        base_url=base_url,
    )


def select_model(provider: LLMProvider) -> str:
    """Select a model for the given provider."""
    models_map = {
        LLMProvider.OPENAI: [
            ("gpt-4o", "Best overall (Recommended)"),
            ("gpt-4-turbo", "Most capable"),
            ("gpt-4o-mini", "Fastest, cheapest"),
        ],
        LLMProvider.ANTHROPIC: [
            ("claude-3-5-sonnet-20241022", "Best balance (Recommended)"),
            ("claude-3-opus-20240229", "Most capable"),
            ("claude-3-haiku-20240307", "Fastest, cheapest"),
        ],
        LLMProvider.GOOGLE: [
            ("gemini-1.5-pro", "Most capable (Recommended)"),
            ("gemini-1.5-flash", "Faster, cheaper"),
        ],
        LLMProvider.OLLAMA: [
            ("llama3.2", "Meta Llama 3.2 (Recommended)"),
            ("mistral", "Mistral 7B"),
            ("llava", "LLaVA (Vision)"),
        ],
        LLMProvider.CUSTOM: [],
    }
    
    models = models_map.get(provider, [])
    
    if not models:
        return Prompt.ask("Enter model name")
    
    console.print()
    console.print("[bold]Select model:[/bold]")
    
    for i, (model, desc) in enumerate(models, 1):
        console.print(f"  [{i}] {model} - {desc}")
    
    console.print()
    choice = Prompt.ask(
        "Choose model",
        choices=[str(i) for i in range(1, len(models) + 1)],
        default="1",
    )
    
    return models[int(choice) - 1][0]


def setup_embedding_provider() -> EmbeddingConfig:
    """Setup embedding provider interactively."""
    console.print("[bold]Step 2/3: Embedding Provider[/bold]")
    console.print("─" * 40)
    console.print("Embeddings are used for semantic memory search.")
    console.print()
    
    table = Table(show_header=True, header_style="bold")
    table.add_column("#", style="dim", width=3)
    table.add_column("Provider", width=15)
    table.add_column("Note", width=40)
    
    options = [
        ("Ollama (Local)", "No API key needed, runs locally"),
        ("OpenAI", "Requires OpenAI API key"),
        ("Google", "Requires Google API key"),
        ("Voyage AI", "Optimized for Claude, requires API key"),
    ]
    
    for i, (name, note) in enumerate(options, 1):
        table.add_row(str(i), name, note)
    
    console.print(table)
    console.print()
    
    choice = Prompt.ask(
        "Choose embedding provider",
        choices=["1", "2", "3", "4"],
        default="1",
    )
    
    provider_map = {
        "1": EmbeddingProvider.OLLAMA,
        "2": EmbeddingProvider.OPENAI,
        "3": EmbeddingProvider.GOOGLE,
        "4": EmbeddingProvider.VOYAGE,
    }
    provider = provider_map[choice]
    
    model_map = {
        EmbeddingProvider.OLLAMA: "nomic-embed-text",
        EmbeddingProvider.OPENAI: "text-embedding-3-small",
        EmbeddingProvider.GOOGLE: "text-embedding-004",
        EmbeddingProvider.VOYAGE: "voyage-3",
    }
    
    base_url = None
    if provider == EmbeddingProvider.OLLAMA:
        base_url = "http://localhost:11434"
    
    return EmbeddingConfig(
        provider=provider,
        model=model_map[provider],
        base_url=base_url,
    )


def setup_curiosity_mode() -> CuriosityConfig:
    """Setup curiosity mode interactively."""
    console.print("[bold]Step 3/3: Curiosity Mode[/bold]")
    console.print("─" * 40)
    console.print("How actively should Mnemosyne explore and ask questions?")
    console.print()
    
    table = Table(show_header=True, header_style="bold")
    table.add_column("#", style="dim", width=3)
    table.add_column("Mode", width=15)
    table.add_column("Behavior", width=50)
    
    modes = [
        ("Passive", "Observe only, no questions generated"),
        ("Curious", "Generate questions internally (Recommended)"),
        ("Interactive", "Ask you questions when curious"),
        ("Proactive", "Actively suggest improvements"),
    ]
    
    for i, (name, desc) in enumerate(modes, 1):
        table.add_row(str(i), name, desc)
    
    console.print(table)
    console.print()
    
    choice = Prompt.ask(
        "Choose curiosity mode",
        choices=["1", "2", "3", "4"],
        default="2",
    )
    
    mode_map = {
        "1": CuriosityMode.PASSIVE,
        "2": CuriosityMode.CURIOUS,
        "3": CuriosityMode.INTERACTIVE,
        "4": CuriosityMode.PROACTIVE,
    }
    
    return CuriosityConfig(mode=mode_map[choice])


def verify_api_key(provider: LLMProvider, api_key: str, base_url: str | None = None) -> bool:
    """Verify that an API key is valid."""
    try:
        if provider == LLMProvider.ANTHROPIC:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}],
            )
            return True
        elif provider == LLMProvider.OPENAI or provider == LLMProvider.CUSTOM:
            import openai
            client = openai.OpenAI(api_key=api_key, base_url=base_url)
            client.chat.completions.create(
                model="gpt-4o-mini" if provider == LLMProvider.OPENAI else "gpt-3.5-turbo",
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}],
            )
            return True
        elif provider == LLMProvider.GOOGLE:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            model.generate_content("Hi")
            return True
    except Exception:
        pass
    return False
