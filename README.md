# MCP Journaling Server / Server MCP per Journaling

A professional MCP (Message Control Protocol) server for interactive journaling with emotional analysis, conversation management, and SQLite database persistence.

*Un server MCP (Message Control Protocol) professionale per journaling interattivo con analisi emotiva, gestione conversazioni e persistenza database SQLite.*

<a href="https://glama.ai/mcp/servers/kiay3i2li7"><img width="380" height="200" src="https://glama.ai/mcp/servers/kiay3i2li7/badge" alt="Journaling Server MCP server" /></a>

## English

### Features

- **Interactive Journaling Sessions**: Manage conversation sessions with unique IDs
- **SQLite Database Storage**: Persistent storage of all conversations and messages
- **Automatic Journal Generation**: Convert conversations to structured markdown entries
- **Emotional Analysis Support**: Built-in support for emotional analysis and reflections
- **Backup System**: Automatic backup creation for journal files
- **Statistics Tracking**: Comprehensive statistics on conversations and entries
- **Professional Architecture**: Modular design with proper error handling and logging
- **Configuration Management**: Environment-based configuration with validation

### Architecture

The project follows a professional Python package structure with:

```
src/journaling_mcp/
├── __init__.py                 # Package entry point
├── main.py                     # CLI entry point
├── server.py                   # Main MCP server class
├── config/
│   └── settings.py             # Configuration management
├── models/
│   ├── conversation.py         # Conversation data models
│   ├── journal.py              # Journal entry models
│   └── database.py             # SQLite database models
├── services/
│   ├── conversation_service.py # Conversation management
│   ├── journal_service.py      # Journal file operations
│   └── database_service.py     # Database operations
├── exceptions/                 # Custom exception hierarchy
└── utils/
    └── logging.py              # Logging configuration
```

### Database Schema

The server uses SQLite for persistent storage:

**Conversations Table:**
- `id`: Primary key
- `session_id`: Unique session identifier
- `created_at`, `updated_at`: Timestamps
- `metadata`: JSON metadata

**Messages Table:**
- `id`: Primary key
- `conversation_id`: Foreign key to conversations
- `speaker`: "user" or "assistant"
- `message`: Message content
- `timestamp`: Message timestamp
- `metadata`: JSON metadata

### Installation

#### Using Claude Desktop

Add to your Claude Desktop configuration:

```json
{
    "mcpServers": {
        "journaling": {
            "command": "uv",
            "args": [
                "--directory",
                "/path/to/journaling_mcp",
                "run",
                "main.py"
            ]
        }
    }
}
```

#### Manual Installation

1. Clone the repository
2. Install dependencies: `uv sync`
3. Run the server: `uv run main.py`

### Configuration

Configure the server using environment variables in a `.env` file:

```bash
# Directory for journal storage (default: "journal")
JOURNAL_DIR=~/Documents/my-journal

# Database settings (default: true and journal/conversations.db)
ENABLE_DATABASE=true
DATABASE_PATH=/custom/path/conversations.db

# File settings
FILENAME_PREFIX=journal         # Default: "journal"
FILE_EXTENSION=md              # Default: "md"

# Behavior settings
MAX_RECENT_ENTRIES=10          # Default: 5
ENABLE_BACKUP=true             # Default: true
BACKUP_DIR=/custom/backup      # Default: journal_dir/backups
```

### MCP Tools

- **`start_new_session()`**: Initialize new conversation session with unique ID
- **`record_interaction(user_message, assistant_message)`**: Record message pairs with metadata
- **`generate_session_summary(summary, emotional_analysis, reflections, tags, mood_rating)`**: Create comprehensive journal entry
- **`get_journal_statistics()`**: Get collection statistics and metrics
- **`add_journal_tags(filepath, tags)`**: Add tags to existing entries

### MCP Resources

- **`journals://recent`**: Access recent journal entries
- **`journals://statistics`**: Get database statistics as JSON

### Entry Format

Journal entries are saved as structured markdown files with:

1. **Header**: Title with date, tags, and mood rating
2. **Conversation**: Timestamped transcript of all messages
3. **Summary**: AI-generated session summary
4. **Emotional Analysis**: Emotional insights and patterns
5. **Reflections**: Personal thoughts and insights
6. **Statistics Footer**: Word count, entry count, timestamps

---

## Italiano

### Caratteristiche

- **Sessioni di Journaling Interattive**: Gestione sessioni conversazionali con ID univoci
- **Database SQLite**: Archiviazione persistente di tutte le conversazioni e messaggi
- **Generazione Automatica Journal**: Conversione di conversazioni in journal markdown strutturati
- **Supporto Analisi Emotiva**: Supporto integrato per analisi emotiva e riflessioni
- **Sistema di Backup**: Creazione automatica backup per i file journal
- **Tracciamento Statistiche**: Statistiche complete su conversazioni e voci
- **Architettura Professionale**: Design modulare con gestione errori e logging appropriati
- **Gestione Configurazione**: Configurazione basata su ambiente con validazione

### Architettura

Il progetto segue una struttura professionale di package Python con:

```
src/journaling_mcp/
├── __init__.py                 # Entry point del package
├── main.py                     # Entry point CLI
├── server.py                   # Classe principale server MCP
├── config/
│   └── settings.py             # Gestione configurazione
├── models/
│   ├── conversation.py         # Modelli dati conversazione
│   ├── journal.py              # Modelli journal entry
│   └── database.py             # Modelli database SQLite
├── services/
│   ├── conversation_service.py # Gestione conversazioni
│   ├── journal_service.py      # Operazioni file journal
│   └── database_service.py     # Operazioni database
├── exceptions/                 # Gerarchia eccezioni personalizzate
└── utils/
    └── logging.py              # Configurazione logging
```

### Schema Database

Il server utilizza SQLite per l'archiviazione persistente:

**Tabella Conversations:**
- `id`: Chiave primaria
- `session_id`: Identificatore sessione univoco
- `created_at`, `updated_at`: Timestamp
- `metadata`: Metadata JSON

**Tabella Messages:**
- `id`: Chiave primaria
- `conversation_id`: Chiave esterna a conversations
- `speaker`: "user" o "assistant"
- `message`: Contenuto messaggio
- `timestamp`: Timestamp messaggio
- `metadata`: Metadata JSON

### Installazione

#### Utilizzando Claude Desktop

Aggiungi alla configurazione di Claude Desktop:

```json
{
    "mcpServers": {
        "journaling": {
            "command": "uv",
            "args": [
                "--directory",
                "/percorso/a/journaling_mcp",
                "run",
                "main.py"
            ]
        }
    }
}
```

#### Installazione Manuale

1. Clona il repository
2. Installa le dipendenze: `uv sync`
3. Avvia il server: `uv run main.py`

### Configurazione

Configura il server utilizzando variabili d'ambiente in un file `.env`:

```bash
# Directory per l'archiviazione journal (default: "journal")
JOURNAL_DIR=~/Documents/mio-journal

# Impostazioni database (default: true e journal/conversations.db)
ENABLE_DATABASE=true
DATABASE_PATH=/percorso/personalizzato/conversations.db

# Impostazioni file
FILENAME_PREFIX=journal         # Default: "journal"
FILE_EXTENSION=md              # Default: "md"

# Impostazioni comportamento
MAX_RECENT_ENTRIES=10          # Default: 5
ENABLE_BACKUP=true             # Default: true
BACKUP_DIR=/backup/personalizzato  # Default: journal_dir/backups
```

### Strumenti MCP

- **`start_new_session()`**: Inizializza nuova sessione conversazionale con ID univoco
- **`record_interaction(user_message, assistant_message)`**: Registra coppie di messaggi con metadata
- **`generate_session_summary(summary, emotional_analysis, reflections, tags, mood_rating)`**: Crea journal entry completo
- **`get_journal_statistics()`**: Ottieni statistiche collezione e metriche
- **`add_journal_tags(filepath, tags)`**: Aggiungi tag a voci esistenti

### Risorse MCP

- **`journals://recent`**: Accesso a journal entry recenti
- **`journals://statistics`**: Ottieni statistiche database come JSON

### Formato Entry

Le voci del journal sono salvate come file markdown strutturati con:

1. **Header**: Titolo con data, tag e valutazione umore
2. **Conversazione**: Trascrizione timestampata di tutti i messaggi
3. **Riassunto**: Riassunto sessione generato dall'AI
4. **Analisi Emotiva**: Insights emotivi e pattern
5. **Riflessioni**: Pensieri personali e intuizioni
6. **Footer Statistiche**: Conteggio parole, conteggio voci, timestamp

## Development / Sviluppo

### Commands / Comandi

```bash
# Run the professional server / Avvia il server professionale
uv run main.py

# Run the legacy server / Avvia il server legacy
uv run server.py

# Install dependencies / Installa dipendenze
uv sync

# Run tests (when available) / Esegui test (quando disponibili)
pytest src/tests/
```

### Contributing / Contribuire

1. Fork the repository / Fai fork del repository
2. Create a feature branch / Crea un branch feature
3. Make your changes / Fai le tue modifiche
4. Add tests / Aggiungi test
5. Submit a pull request / Invia una pull request

### License / Licenza

This project is licensed under the MIT License. See LICENSE file for details.

*Questo progetto è rilasciato sotto licenza MIT. Vedi il file LICENSE per i dettagli.*

## Support / Supporto

For issues and questions, please use the GitHub Issues page.

*Per problemi e domande, utilizza la pagina GitHub Issues.*