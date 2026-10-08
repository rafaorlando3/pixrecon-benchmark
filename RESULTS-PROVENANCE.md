# Results provenance

The CSV and raw-response directory are the direct OpenRouter grid dated 2026-10-07: seven models, 73 cases each, 511 logical receipts and 520 transport attempts. The directory contains the 511 selected final provider responses. Nine transport-level 429 attempts preceded selected retries; their unknown costs remain unknown and their reservations are preserved in the public audit summary. Empty outputs and two provider errors remain in the denominator, with 73 cases per model.

I0 is an earlier, frozen Kaggle result, kept outside every direct-grid average. This repository does not claim that I0 was rerun or that its historic unknown costs were zero. Historical Kaggle I1/easy-000 with HTTP 429 and cost NULL/UNKNOWN is not the direct OpenRouter I1/easy-000 valid response.

Task Page publication and a new evaluation are distinct operations. Publishing these frozen artifacts does not execute the analysis, notebook or a model, and does not assert that the seven-model grid was run by Kaggle.

Packaged raw JSON files have one appended final LF. Each CSV `response_sha256` matches the exact stored bytes with that one LF removed (511 of 511). The `answer_sha256` bindings also match all 511 selected responses. Release file hashes cover the stored bytes including their final LF.
