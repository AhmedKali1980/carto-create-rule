# Processes

## Inputs and trigger

Source: `main` process-export section and `build_final_excel`. The worksheet is created only if normalised process rows are nonempty. An empty process export/header does not create an empty Processes tab.

## Construction

1. Use the explicit final-process stub if present. Otherwise use a bulk-process stub when provided, copying it to `export_processes.csv` or writing an empty header if it is unavailable/empty.
2. Without process stubs, select managed scope workload hrefs, write `derived/list_href.managed.csv` and invoke the bulk wrapper. If no usable bulk file exists, try the single-process wrapper; if still unavailable, write the canonical empty CSV header.
3. Read `raw/export_processes.csv`. Resolve aliases for hostname (host/name), process path (path/exe/binary/command), service name, listen port, protocol, labels and href.
4. Build columns `hostname,process_path,service_name,port,proto,role,app,env,loc,OS,href`. Coerce port to numeric when possible. Sort stably by hostname and role.
5. Write the sheet, freeze A2, enable filtering, format port as an integer and alternate light-blue row groups whenever hostname changes. All rows of one hostname have the same band colour.

## Interpretation and checks

The live process request is scope-derived. A provided process CSV is not independently scoped again before writing, so a broad stub can expose extra hosts. Missing wrappers or failed extraction can legitimately leave no Processes tab while later phases proceed. The bulk retry path may use a nonempty existing output despite a nonzero command result; verify provenance.

Streaming inserts flow tabs after Processes when that sheet exists and otherwise appends them later. A change to this title affects workbook order. Confirm normalised column aliases, sample host/service/port values and process-source coverage before treating absence as proof that no listening process exists.
