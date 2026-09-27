"""Operator-run deployment. Requires preprovisioned billing, APIs, database and service identity."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', required=True)
    parser.add_argument('--region', required=True)
    parser.add_argument('--service-identity', required=True)
    parser.add_argument('--setup-secret', required=True, help='Existing Secret Manager NAME:VERSION, never the value')
    parser.add_argument('--site', default='proofline-tablekeeper')
    parser.add_argument('--service', default='tablekeeper')
    args = parser.parse_args()
    for item in (args.project, args.region, args.site, args.service):
        if not re.fullmatch('[a-z][a-z0-9-]{1,62}', item):
            parser.error('Invalid deployment identifier')
    if not re.fullmatch(r'[a-zA-Z0-9_-]+:[0-9]+', args.setup_secret):
        parser.error('Pin an existing setup secret version as NAME:NUMBER')
    root = Path(__file__).resolve().parent.parent
    origin = 'https://' + args.site + '.web.app'
    subprocess.run(['gcloud', 'run', 'deploy', args.service, '--project', args.project, '--region', args.region,
        '--source', str(root), '--service-account', args.service_identity, '--allow-unauthenticated',
        '--min-instances', '0', '--max-instances', '2', '--concurrency', '16', '--cpu', '2', '--memory', '2Gi',
        '--timeout', '30', '--port', '8080', '--set-env-vars',
        f'TABLEKEEPER_MODE=production,TABLEKEEPER_STORAGE=firestore,GOOGLE_CLOUD_PROJECT={args.project},TABLEKEEPER_PUBLIC_ORIGIN={origin},TABLEKEEPER_PUBLIC_DEMO=0',
        '--set-secrets', 'TABLEKEEPER_SETUP_SECRET=' + args.setup_secret], check=True)
    config = json.loads((root / 'firebase.json').read_text())
    config['hosting']['site'] = args.site
    config['hosting']['rewrites'][0]['run'].update(serviceId=args.service, region=args.region)
    # Keep temporary configuration beside source so Firebase resolves relative paths correctly.
    with tempfile.NamedTemporaryFile(mode='w', prefix='.firebase-deploy-', suffix='.json', dir=root) as target:
        json.dump(config, target)
        target.flush()
        subprocess.run(['firebase', 'deploy', '--project', args.project, '--config', target.name,
                        '--only', 'hosting,firestore:rules,firestore:indexes'], cwd=root, check=True)


if __name__ == '__main__':
    main()
