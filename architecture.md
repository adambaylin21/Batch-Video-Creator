# Batch Video Creator Architecture

## System Architecture Diagram

```mermaid
graph TD
    A[User Interface] --> B[Flask Backend]
    B --> C[Video Scanner]
    B --> D[Video Selector]
    B --> E[Batch Processor]
    E --> F[merge_videos.py]
    F --> G[Video Processing]
    G --> H[Output Videos]
    
    subgraph Configuration
        I[Input Folder Path]
        J[Output Folder Path]
        K[Video Count]
        L[Video Duration]
        M[Output Count]
    end
    
    A --> I
    A --> J
    A --> K
    A --> L
    A --> M
    B --> I
    B --> J
    B --> K
    B --> L
    B --> M
```

## Data Flow Diagram

```mermaid
sequenceDiagram
    participant User
    participant UI
    participant Backend
    participant Scanner
    participant Selector
    participant Processor
    participant Merger
    participant FileSystem
    
    User->>UI: Select input folder path
    User->>UI: Select output folder path
    User->>UI: Set configuration
    UI->>Backend: POST /api/scan-folder
    Backend->>Scanner: Scan input folder
    Scanner->>FileSystem: List videos
    FileSystem-->>Scanner: Video files
    Scanner->>Backend: Video metadata
    Backend-->>UI: Video list
    
    UI->>Backend: POST /api/process-batch
    Backend->>Selector: Select videos
    Selector->>Backend: Selected videos
    
    loop Output Count times
        Backend->>Selector: Randomly select videos
        Selector-->>Backend: Selected video paths
        Backend->>Processor: Process batch
        Processor->>Merger: Merge videos
        Merger->>FileSystem: Read video files
        Merger->>FileSystem: Write output
        FileSystem-->>Merger: Output path
        Merger-->>Processor: Result
        Processor-->>Backend: Output file
    end
    
    Backend-->>UI: Processing complete
    UI->>User: Show download links
```

## Component Interaction

```mermaid
graph LR
    subgraph Frontend
        A[HTML UI]
        B[JavaScript]
    end
    
    subgraph Backend
        C[Flask Routes]
        D[Video Processor]
        E[Batch Manager]
    end
    
    subgraph External
        F[merge_videos.py]
        G[File System]
    end
    
    A --> C
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
    G --> F
    F --> E
    E --> D
    D --> C
    C --> A
```

## State Management

```mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> Scanning: Scan folder
    Scanning --> Ready: Scan complete
    Scanning --> Error: Scan failed
    
    Ready --> Processing: Start batch
    Processing --> Completed: All outputs done
    Processing --> Error: Processing failed
    Processing --> Processing: Next output
    
    Completed --> Idle: Reset
    Error --> Idle: Reset
```

## Video Processing Pipeline

```mermaid
flowchart TD
    A[Input Folder] --> B[Scan Videos]
    B --> D[Random Selection]
    D --> E[Merge Videos]
    E --> F[Save Output]
    F --> G{More Outputs?}
    G -->|Yes| D
    G -->|No| H[Complete]
    
    subgraph Batch Loop
        D
        E
        F
        G
    end
```

## Error Handling Flow

```mermaid
flowchart TD
    A[Start Operation] --> B{Validate Input}
    B -->|Invalid| C[Return Error]
    B -->|Valid| D[Execute Operation]
    
    D --> E{Success?}
    E -->|Yes| F[Return Result]
    E -->|No| G{Retry?}
    G -->|Yes| D
    G -->|No| C
    
    C --> H[Log Error]
    F --> I[Update State]
    H --> J[Update State]