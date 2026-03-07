# Backend Analysis Findings

## 1. Backend Capabilities (d:\Tiga\backend\app\services\pathway\)

### Data Sources (Connectors)
- **Streaming**: Kafka (`pw.io.kafka`), Database (Postgres via replication), S3 (`pw.io.s3`).
- **Batch/Snapshot**: GenericSQL (SQLAlchemy -> Pandas -> Pathway Table).
- **Other**: REST (Polling).

### Transformation Operators
- **Text**: Case conversion, Regex, Tokenization (Jieba), Stemming, Similarity.
- **Data Cleaning**: FillNA, Cast, Arithmetic, Outlier Detection (Z-Score).
- **Aggregation**: GroupBy (Sum, Count, Avg, Min, Max, HLL).
- **Custom**: UDF support via external Python files.

### Sinks (Destinations)
- **Analytics**: ClickHouse.
- **Cache/KV**: Redis.
- **Search**: Elasticsearch.
- **Graph**: Neo4j.
- **AI/RAG**: LightRAG, VectorObject.

### Execution Model
- **Engine**: Pathway (Streaming first).
- **Management**: Multiprocessing for isolation.
- **Monitoring**: Built-in Pathway dashboard, Prometheus metrics.

## 2. Frontend Implications

### Node Categories Needed
1.  **Input Nodes**: Kafka, Postgres, S3, REST, SQL Generic.
2.  **Process Nodes**:
    *   *Cleaning*: Text ops, FillNA, Cast.
    *   *Math*: Arithmetic, Outlier.
    *   *Structure*: Flatten, JSON Parse.
    *   *Aggregation*: GroupBy + Windowing (implicit in streaming?).
    *   *Custom*: UDF Node (needs file upload/code editor).
3.  **Output Nodes**: ClickHouse, Redis, ES, Neo4j, Vector DB.

### Configuration Requirements
- **Source Config**: Connection strings, topics, polling intervals.
- **Sink Config**: Host, port, credentials, batch size.
- **Operator Config**:
    - Columns selection.
    - Parameters (e.g., regex pattern, fill value).
    - UDF script path.

### Feedback & Monitoring
- Need to poll `GET /jobs/{name}` for status.
- Need to display Prometheus metrics if possible, or link to Pathway dashboard.
- Error logs need to be fetched and associated with specific nodes if possible.
