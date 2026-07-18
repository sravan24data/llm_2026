from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
# from opentelemetry.sdk.trace.export import (
#     ConsoleSpanExporter,
#     SimpleSpanProcessor,
# )
from opentelemetry.sdk.trace.export import (
    SpanExporter,
    SpanExportResult,
    SimpleSpanProcessor,
)

import sqlite3

class SQLiteSpanExporter(SpanExporter):

    def __init__(self, db_path="traces.db"):
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS spans (
                name TEXT,
                start_time INTEGER,
                end_time INTEGER,
                input_tokens INTEGER,
                output_tokens INTEGER,
                cost REAL
            )
        """)
        self.conn.commit()

    def export(self, spans):
        for span in spans:
            attrs = dict(span.attributes or {})

            self.conn.execute(
                "INSERT INTO spans VALUES (?, ?, ?, ?, ?, ?)",
                (
                    span.name,
                    span.start_time,
                    span.end_time,
                    attrs.get("input_tokens"),
                    attrs.get("output_tokens"),
                    attrs.get("cost"),
                ),
            )

        self.conn.commit()
        return SpanExportResult.SUCCESS

    def shutdown(self):
        self.conn.close()

    def force_flush(self):
        return True

# Setup OpenTelemetry
provider = TracerProvider()
# provider.add_span_processor(
#     SimpleSpanProcessor(ConsoleSpanExporter())
# )

provider.add_span_processor(
    SimpleSpanProcessor(SQLiteSpanExporter("traces.db"))
)

trace.set_tracer_provider(provider)

tracer = trace.get_tracer("llm-zoomcamp")


from starter import rag as base_rag
from rag_helper import RAGBase


class RAGTraced(RAGBase):

    def search(self, query, num_results=5):
        with tracer.start_as_current_span("search") as span:
            return super().search(query, num_results)

    def llm(self, prompt):
        with tracer.start_as_current_span("llm") as span:
            response = super().llm(prompt)

            usage = response.usage

            span.set_attribute(
                "input_tokens",
                usage.input_tokens
            )
            span.set_attribute(
                "output_tokens",
                usage.output_tokens
            )

            # Optional: cost calculation
            input_price = 0.25 / 1_000_000
            output_price = 2.00 / 1_000_000

            cost = (
                usage.input_tokens * input_price
                + usage.output_tokens * output_price
            )

            span.set_attribute("cost", cost)

            return response

    def rag(self, query):
        with tracer.start_as_current_span("rag") as span:
            return super().rag(query)


# Create traced RAG using the objects loaded by starter.py
rag = RAGTraced(
    index=base_rag.index,
    llm_client=base_rag.llm_client,
    instructions=base_rag.instructions,
    prompt_template=base_rag.prompt_template,
    model=base_rag.model,
)


if __name__ == "__main__":
    query = "How does the agentic loop keep calling the model until it stops?"

    answer = rag.rag(query)

    print("\nANSWER:")
    print(answer)


### Terminal 
# (llm-2026) @sravan24data ➜ /workspaces/llm_2026 (main) $ /workspaces/llm_2026/.venv/bin/python /workspaces/llm_2026/w5_monitoring/hw5.py
# {
#     "name": "search",
#     "context": {
#         "trace_id": "0xfa2fdc5ab1c700aa39abe33a11a110ae",
#         "span_id": "0x9294be7e7bfe39ff",
#         "trace_state": "[]"
#     },
#     "kind": "SpanKind.INTERNAL",
#     "parent_id": "0x8b33bebf04478b39",
#     "start_time": "2026-07-18T22:06:31.079847Z",
#     "end_time": "2026-07-18T22:06:31.081547Z",
#     "status": {
#         "status_code": "UNSET"
#     },
#     "attributes": {},
#     "events": [],
#     "links": [],
#     "resource": {
#         "attributes": {
#             "telemetry.sdk.language": "python",
#             "telemetry.sdk.name": "opentelemetry",
#             "telemetry.sdk.version": "1.44.0",
#             "service.instance.id": "70759f59-a8b5-487d-aac3-783ad33a0f09",
#             "service.name": "unknown_service"
#         },
#         "schema_url": ""
#     }
# }
# {
#     "name": "llm",
#     "context": {
#         "trace_id": "0xfa2fdc5ab1c700aa39abe33a11a110ae",
#         "span_id": "0x9516e57a79df81b1",
#         "trace_state": "[]"
#     },
#     "kind": "SpanKind.INTERNAL",
#     "parent_id": "0x8b33bebf04478b39",
#     "start_time": "2026-07-18T22:06:31.081929Z",
#     "end_time": "2026-07-18T22:06:33.688386Z",
#     "status": {
#         "status_code": "UNSET"
#     },
#     "attributes": {
#         "input_tokens": 7111,
#         "output_tokens": 102,
#         "cost": 0.00198175
#     },
#     "events": [],
#     "links": [],
#     "resource": {
#         "attributes": {
#             "telemetry.sdk.language": "python",
#             "telemetry.sdk.name": "opentelemetry",
#             "telemetry.sdk.version": "1.44.0",
#             "service.instance.id": "70759f59-a8b5-487d-aac3-783ad33a0f09",
#             "service.name": "unknown_service"
#         },
#         "schema_url": ""
#     }
# }
# {
#     "name": "rag",
#     "context": {
#         "trace_id": "0xfa2fdc5ab1c700aa39abe33a11a110ae",
#         "span_id": "0x8b33bebf04478b39",
#         "trace_state": "[]"
#     },
#     "kind": "SpanKind.INTERNAL",
#     "parent_id": null,
#     "start_time": "2026-07-18T22:06:31.079780Z",
#     "end_time": "2026-07-18T22:06:33.688757Z",
#     "status": {
#         "status_code": "UNSET"
#     },
#     "attributes": {},
#     "events": [],
#     "links": [],
#     "resource": {
#         "attributes": {
#             "telemetry.sdk.language": "python",
#             "telemetry.sdk.name": "opentelemetry",
#             "telemetry.sdk.version": "1.44.0",
#             "service.instance.id": "70759f59-a8b5-487d-aac3-783ad33a0f09",
#             "service.name": "unknown_service"
#         },
#         "schema_url": ""
#     }
# }

# ANSWER:
# It keeps calling the model inside a `while True` loop.

# Each iteration:
# 1. Sends the full `messages` history to the model.
# 2. Checks the response for any `function_call` items.
# 3. Runs those tools and appends the tool outputs to `messages`.
# 4. If there were no function calls in that response, it `break`s.

# So the stop condition is פשוט: **when the model returns a response with no function calls, the loop ends**.
# (llm-2026) @sravan24data ➜ /workspaces/llm_2026 (main) $ 


# Q6:
# >>> import sqlite3
# >>> import pandas as pd
# >>> 
# >>> conn = sqlite3.connect("traces.db")
# >>> 
# >>> df = pd.read_sql(
# ...     "SELECT * FROM spans",
# ...     conn
# ... )
# >>> 
# >>> llm_spans = df[df.name == "llm"]
# >>> 
# >>> print(llm_spans[["input_tokens", "output_tokens"]])
#     input_tokens  output_tokens
# 1         7111.0           91.0
# 4         7111.0          143.0
# 7         7111.0           94.0
# 10        7111.0          121.0
# >>> print(
# ...     (llm_spans.input_tokens.max() - llm_spans.input_tokens.min())
# ...     / llm_spans.input_tokens.min()
# ...     * 100
# ... )
# 0.0
# >>> print(llm_spans[["input_tokens", "output_tokens"]])
#     input_tokens  output_tokens
# 1         7111.0           91.0
# 4         7111.0          143.0
# 7         7111.0           94.0
# 10        7111.0          121.0