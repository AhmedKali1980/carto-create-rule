#!/usr/bin/env python3
"""Exercise the documented workbook paths with synthetic, fully stubbed exports.

No PCE or SMTP request is made. The placeholder executable/config satisfy only
preflight checks; all export steps are supplied with local fixtures and PCE
FQDN enrichment is explicitly disabled. Temporary artifacts are deleted on exit.
Run with the project's Python environment from any working directory.
"""
import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from openpyxl import load_workbook

def validate(work: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    py = sys.executable
    root = work / 'fixtures'
    root.mkdir(exist_ok=True)

    def write(name, cols, rows):
        p = root / name
        with p.open('w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(rows)
        return p
    app = 'APMA_SAMPLE'
    env = 'PRD'
    write('labels.csv', ['href', 'key', 'value'], [{'href': f'/orgs/1/labels/{i}', 'key': k, 'value': v} for i, (k, v) in enumerate([('app', app), ('env', env), ('role', 'DB'), ('role', 'WEB')], 1)])
    write('groups.csv', ['name', 'key', 'member_labels', 'fully_expanded_members', 'member_label_groups'], [{'name': 'APP_GROUP', 'key': 'app', 'member_labels': app, 'fully_expanded_members': app}])
    write('iplist.csv', ['name', 'href', 'include'], [{'name': n, 'href': f'/orgs/1/sec_policy/draft/ip_lists/{i}', 'include': inc} for i, (n, inc) in enumerate([('NZ0_TEST', '10.0.0.0/24'), ('ZNOT_NZ0_TEST', '0.0.0.0/0;!10.0.0.0/24'), ('USR_PEER', '10.0.1.0/24')], 1)])
    wcols = ['href', 'hostname', 'role', 'app', 'env', 'loc', 'OS', 'interfaces', 'managed', 'enforcement']
    write('managed.csv', wcols, [dict(zip(wcols, [f'/orgs/1/workloads/00000000-0000-0000-0000-00000000000{i}', f'host{i}', role, app, env, 'EU', 'Linux', f'10.0.0.{i}', 'true', 'full'])) for i, role in [(1, 'DB'), (2, 'WEB')]])
    write('unmanaged.csv', wcols, [])
    write('process.csv', ['hostname', 'process_path', 'service_name', 'port', 'proto', 'role', 'app', 'env', 'loc', 'OS', 'href'], [{'hostname': 'host1', 'process_path': '/usr/bin/database', 'service_name': 'db', 'port': '443', 'proto': 'TCP', 'role': 'DB', 'app': app, 'env': env}])
    write('rulesets.csv', ['href', 'enabled'], [{'href': '/orgs/1/sec_policy/draft/rule_sets/1', 'enabled': 'true'}])
    rcols = ['rule_href', 'rule_enabled', 'ruleset_name', 'ruleset_scope', 'ruleset_enabled', 'rule_type', 'rule_description', 'services', 'src_labels', 'dst_labels', 'src_iplists', 'dst_iplists']
    write('rules.csv', rcols, [{'rule_href': '/orgs/1/sec_policy/draft/rule_sets/1/sec_rules/1', 'rule_enabled': 'true', 'ruleset_name': app + '-PRD-RS', 'ruleset_scope': f'app:{app};env:PRD', 'ruleset_enabled': 'true', 'rule_type': 'intra_scope', 'rule_description': 'Synthetic sample', 'services': 'tcp/443', 'src_labels': f'app:{app};env:PRD;role:WEB', 'dst_labels': f'app:{app};env:PRD;role:DB'}])
    write('dupe.csv', ['href', 'reason'], [])
    fcols = ['Source IP', 'Destination IP', 'Source Application', 'Source Environment', 'Source Role', 'Destination Application', 'Destination Environment', 'Destination Role', 'Source IPList', 'Destination IPList', 'Protocol', 'Port', 'Num Flows', 'Transmission', 'Source Name', 'Destination Name']
    flows = [{'Source IP': '10.0.0.2', 'Destination IP': '10.0.0.1', 'Source Application': app, 'Source Environment': env, 'Source Role': 'WEB', 'Destination Application': app, 'Destination Environment': env, 'Destination Role': 'DB', 'Protocol': 'TCP', 'Port': '443', 'Num Flows': '5', 'Transmission': 'Outgoing'}, {'Source IP': '10.0.0.1', 'Destination IP': '10.0.1.8', 'Source Application': app, 'Source Environment': env, 'Source Role': 'DB', 'Destination IPList': 'USR_PEER', 'Protocol': 'TCP', 'Port': '22', 'Num Flows': '3', 'Transmission': 'Outgoing'}, {'Source IP': '10.0.1.8', 'Destination IP': '10.0.0.1', 'Destination Application': app, 'Destination Environment': env, 'Destination Role': 'DB', 'Source IPList': 'NZ0_TEST', 'Protocol': 'TCP', 'Port': '443', 'Num Flows': '2', 'Transmission': 'Incoming'}]
    write('out.csv', fcols, flows[:2])
    write('in.csv', fcols, [flows[0], flows[2]])
    for mode, extra in [('normal', []), ('stream', ['--excel-stream-update']), ('zone', ['--network-zone', 'NZ0_TEST', '--excel-stream-update'])]:
        cwd = work / mode
        cwd.mkdir(exist_ok=True)
        cfg = cwd / 'pce-placeholder.yaml'
        cfg.write_text('# Not used: all exports are stubbed\n')
        (cwd / 'carto.conf').write_text(f'EXECUTABLE=/bin/true\nEXECUTABLE_CONFIG_FILE={cfg}\nEXPORT_ROOT={cwd}/RUNS\nENABLE_SERVICES_CATALOG=1\nIPLIST_ALLOWED_PREFIXES=USR_;NZ0_\nIPLIST_NAME_PRIORITY=USR_;NZ0_\nPORTS_ADMIN=TCP/22\nALLOWED_PORTS=TCP/443\n')
        cmd = [py, str(repo / 'carto_ng_orchestrator.py'), '--days', '30', '--app', app, '--env', env, '--strategy-intra-app', 'allow', '--strategy-ingress', 'finegrained', '--strategy-egress', 'finegrained', '--skip-pce-fqdn-enrichment', '--dns-timeout', '0.01', '--dev-flow-stub', '--dev-flow-stub-out', str(root / 'out.csv'), '--dev-flow-stub-in', str(root / 'in.csv')]
        for opt, name in [('label', 'labels'), ('labelgroup', 'groups'), ('iplists', 'iplist'), ('wkld-m', 'managed'), ('wkld-u', 'unmanaged'), ('processes', 'process'), ('ruleset', 'rulesets'), ('rules-enabled', 'rules'), ('dupecheck', 'dupe')]:
            cmd += ['--dev-stub-' + opt, str(root / (name + '.csv'))]
        with (cwd / 'run.log').open('w') as log:
            r = subprocess.run(cmd + extra, cwd=cwd, stdout=log, stderr=subprocess.STDOUT)
        assert r.returncode == 0, (mode, r.returncode, (cwd / 'run.log').read_text()[-4000:])
        book = next((cwd / 'RUNS').glob('*/excel/carto_*.xlsx'))
        wb = load_workbook(book)
        titles = wb.sheetnames
        assert 'Flow-Rule Match' in titles and 'Flow-in' in titles and ('Flow-out' in titles) and ('Proposed rules1' in titles), titles
        assert 'Proposed Rules' not in titles and 'Action Plan' not in titles, titles

        def data(sheet):
            rows = list(wb[sheet].values)
            headers = list(rows[0])
            return [dict(zip(headers, row)) for row in rows[1:] if row[0] is not None]
        catalogue = {row['port']: row for row in data('Service Catalogue')}
        assert catalogue[22]['category'] == 'ADMIN' and catalogue[22]['flows_total'] == 3, catalogue
        assert catalogue[443]['category'] == 'ALLOWED' and catalogue[443]['flows_total'] == 12, catalogue
        rules = data('Scope Applicable Rules')
        assert len(rules) == 1 and rules[0]['Rule Category'] == 'Business Rule in Scope', rules
        matches = data('Flow-Rule Match')
        assert any((row['Info'] == 'Business in scope' for row in matches)), matches
        assert len(matches) == (2 if mode == 'zone' else 4), matches
        proposals = data('Proposed rules1')
        assert proposals and 'num_aggregated_rows' in proposals[0] and ('Comment' in proposals[0]), proposals
        if mode == 'zone':
            assert any((row['East-West (Y/N)'] == 'N' and row['Destination'] == 'ZNOT_NZ0_TEST' for row in proposals)), proposals
        investigation = data('To investigate')
        assert len(investigation) == 2 and {row['Unknown IP'] for row in investigation} == {'10.0.1.8'}, investigation
        assert len(data('Egress IP to investigate')) == 1 and len(data('Ingress IP to investigate')) == 1
        print(mode, ': PASS data, applicability, matching, proposals, investigation and worksheet titles')
        (cwd / 'observed-sheets.json').write_text(json.dumps(titles, indent=2) + '\n')
        wb.close()
if __name__ == '__main__':
    with tempfile.TemporaryDirectory(prefix='carto-doc-workflow-') as directory:
        validate(Path(directory))
