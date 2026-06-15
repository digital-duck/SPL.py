## Summary

This workflow crawls a user-supplied website, extracts text and links from each page within the same domain, then uses an LLM (GPT-4) to classify and summarize each page's content in batches. The result is a structured analysis report covering summaries, topics, and content types for every crawled page. It benefits content auditors, SEO analysts, and researchers who need a quick, structured inventory of a site's content without manual review.

---

## Detailed Specification

### 1. Purpose

Crawl a bounded website domain, extract page content, and produce a per-page LLM analysis report covering summaries, topic keywords, and content-type classifications.

---

### 2. High-level Description

This workflow implements a three-stage linear pipeline: crawl, analyze, report. In the first stage, a deterministic web crawler (`WebCrawler`) fetches up to `max_pages` pages from a user-supplied base URL, staying within the same domain and collecting raw text and link data for each page. In the second stage, the crawled pages are divided into batches of five and passed to a `GENERATE` call (`analyze_site`) that invokes an LLM (GPT-4) to produce a structured analysis for each page, returning a summary sentence, a list of main topic keywords, and a content-type label. The batch processing pattern maps to SPL's `GENERATE` inside a collection loop over grouped page slices, with results flattened back into a single list stored in shared state (`@analyzed_results`). In the third stage, a deterministic formatting step assembles all per-page analyses into a human-readable report stored in `@report` and printed to stdout. There is no iterative refinement loop, no semantic branching, and no exception handling in this implementation; control flow is strictly sequential. The only LLM interaction is the per-page content classification in the batch analysis stage.

---

### 3. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW WebCrawlerAnalysis` | `create_flow()` + `Flow(start=crawl)` | Top-level orchestration unit |
| `INPUT: base_url, max_pages` | `shared = {"base_url": url, "max_pages": 1}` | Shared state dict is SPL's input namespace |
| `CALL crawler(...) INTO @crawl_results` | `CrawlWebsiteNode.exec()` → `WebCrawler.crawl()` | Pure tool call; no LLM involved |
| `GENERATE analyze_page(...) INTO @page_analysis` | `AnalyzeContentBatchNode.exec(batch)` → `analyze_site(batch)` | LLM call per batch of pages |
| `@crawl_results`, `@analyzed_results`, `@report` | `shared["crawl_results"]`, `shared["analyzed_results"]`, `shared["report"]` | SPL variables = keys in the shared dict |
| `CALL format_report(...) INTO @report` | `GenerateReportNode.exec(results)` | Deterministic string assembly; no LLM |
| `BATCH` / collection iteration | `BatchNode` with `prep` returning `[results[i:i+5] ...]` | SPL has no native batch node; model as a loop over grouped slices |
| `OUTPUT: @report` | `shared["report"]` printed in `post()` | Final workflow output |

---

### 4. Logical Functions / Prompts

**`analyze_site(batch: List[Dict]) → List[Dict]`**
- **Role:** The sole LLM interaction in the workflow. Receives a batch of up to five raw page records (each with URL, title, and extracted text) and returns a structured analysis for each.
- **Key prompt conventions:** Expected to return a structured object per page containing three fields — `summary` (one or two sentence description of the page), `topics` (list of keyword strings representing main themes), and `content_type` (a category label such as "article", "landing page", "documentation", etc.). The prompt drives GPT-4 to classify and summarize simultaneously in a single call per batch rather than per page, trading granularity for throughput.
- **Output format:** JSON-like dict per page; accessed downstream as `page.get("analysis", {})`.

**`GenerateReportNode.exec(results)` (deterministic)**
- **Role:** Formats the list of analyzed page dicts into a human-readable plain-text report. Not an LLM call — purely string assembly.
- **Key conventions:** Inserts a header with total page count, then one block per page with URL, title, summary, comma-joined topics, and content type, separated by an 80-character rule.

---

### 5. Control Flow

```
START
  → CrawlWebsiteNode
      CALL WebCrawler(base_url, max_pages) INTO @crawl_results
  → AnalyzeContentBatchNode
      partition @crawl_results into slices of 5
      FOR EACH slice:
          GENERATE analyze_site(slice) INTO @batch_analysis
      flatten all @batch_analysis results INTO @analyzed_results
  → GenerateReportNode
      CALL format_report(@analyzed_results) INTO @report
      print @report
END
```

No WHILE loop, no EVALUATE branch, no EXCEPTION handler. The only non-trivial control structure is the batch partitioning before the LLM call and the subsequent flatten of results.

---

### 6. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (paste Section 2, High-level Description, as input)
spl3 text2spl --description "Crawl a bounded website domain up to max_pages pages, \
staying within the same domain. Partition crawled pages into batches of 5. \
For each batch, GENERATE an LLM analysis that returns a summary, topic keywords, \
and content_type per page. Flatten all batch results into @analyzed_results. \
Then CALL a deterministic formatter to assemble a plain-text report stored in @report." \
--mode workflow

# Step 2 — compile to any target
spl3 splc compile web_crawler_analysis.spl --lang python/pocketflow
spl3 splc compile web_crawler_analysis.spl --lang python/langgraph
spl3 splc compile web_crawler_analysis.spl --lang go
```