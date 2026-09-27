#!/usr/bin/env python3
"""Prepare a narrowly scoped deployment plan; --execute runs exactly one phase.

Requires preprovisioned resources and independently accepted product source.
Never deploys a default database, creates service accounts, or grants project IAM.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
import tempfile


def stop(message):
    raise SystemExit(message)


def git(source, *args):
    p = subprocess.run(['git', '-C', str(source), *args], capture_output=True)
    if p.returncode:
        stop('Git inspection failed; verify source, revision and evidence path')
    return p.stdout


def safe_relative(value):
    path = Path(value)
    if path.is_absolute() or '..' in path.parts or not path.parts:
        stop('Evidence must be a tracked relative path without traversal')
    return path.as_posix()


def scan_build_context(files):
    """Conservative reject-only screen, not a substitute for source review."""
    patterns = [rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
                rb'"type"\s*:\s*"service_account"', rb'\bya29\.[A-Za-z0-9._~-]+',
                rb'\bAIza[0-9A-Za-z_-]{30,}', rb'\bsk-(?:proj-)?[A-Za-z0-9_-]{32,}']
    for name, content, _ in files:
        base = Path(name).name.lower()
        if base in ('.env', 'credentials.json', 'application_default_credentials.json') or base.endswith(('.pem', '.key', '.p12')):
            stop('Credential-shaped file in build context: ' + name)
        if any(re.search(pattern, content) for pattern in patterns):
            stop('Potential credential detected in build context: ' + name + '; value withheld')


def redact(text):
    for pattern in [r'(?i)authorization\s*[:=]\s*bearer\s+\S+',
                    r'\bya29\.[A-Za-z0-9._~-]+',
                    r'\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+',
                    r'(?i)(access_token|refresh_token|client_secret)\s*[=:]\s*[^\s,]+']:
        text = re.sub(pattern, '[REDACTED]', text)
    return text


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('project', 'site', 'database', 'service', 'region', 'runtime-sa', 'scheduler-sa',
                 'accepted-revision', 'acceptance-evidence', 'artifact-repository'):
        p.add_argument('--' + name, required=True)
    p.add_argument('--source', type=Path, default=Path.cwd(), help='Repository containing accepted product/; default current directory')
    p.add_argument('--output-dir', type=Path, required=True, help='Private directory outside the source repository')
    p.add_argument('--phase', choices=('plan', 'build', 'datastore', 'service', 'cleanup-job', 'cleanup-initial', 'cleanup-invoker', 'cleanup-schedule', 'hosting'), default='plan')
    p.add_argument('--cleanup-job', help='Explicit dedicated job name; default SERVICE-cleanup')
    p.add_argument('--scheduler-name', help='Explicit dedicated scheduler name; default SERVICE-cleanup-hourly')
    p.add_argument('--image-digest', help='sha256 digest built from this accepted product tree')
    p.add_argument('--execute', action='store_true')
    p.add_argument('--confirm-reviewed', action='store_true', help='Operator has reviewed independent acceptance, build context and exact resource scope')
    p.add_argument('--confirm-live-checks', action='store_true', help='For Hosting: operator verified backend, isolation, persistence and cleanup')
    args = p.parse_args()
    for value in (args.project, args.site, args.service, args.region, args.artifact_repository):
        if not re.fullmatch(r'[a-z][a-z0-9-]{1,62}', value):
            p.error('Invalid resource identifier')
    if args.database == '(default)' or not re.fullmatch(r'[a-z][a-z0-9-]{2,62}', args.database):
        p.error('An explicit non-default named database is required')
    for identity in (args.runtime_sa, args.scheduler_sa):
        if not re.fullmatch(r'[a-z][a-z0-9-]{4,28}[a-z0-9]@' + re.escape(args.project) + r'\.iam\.gserviceaccount\.com', identity):
            p.error('Service accounts must be explicit identities in the selected project')
    if args.runtime_sa == args.scheduler_sa:
        p.error('Use a separate scheduler identity')
    if not re.fullmatch(r'[0-9a-f]{40}', args.accepted_revision):
        p.error('Use an immutable full 40-character commit SHA')
    if args.image_digest and not re.fullmatch(r'sha256:[0-9a-f]{64}', args.image_digest):
        p.error('Use a full sha256 image digest')
    needs_image = args.phase not in ('plan', 'build', 'datastore')
    if needs_image and not args.image_digest:
        p.error('This phase requires --image-digest from the accepted build')
    if args.execute and (args.phase == 'plan' or not args.confirm_reviewed):
        p.error('Execution requires a non-plan phase and explicit --confirm-reviewed')
    if args.execute and args.phase == 'hosting' and not args.confirm_live_checks:
        p.error('Hosting publication requires --confirm-live-checks')
    source = Path(git(args.source.resolve(), 'rev-parse', '--show-toplevel').decode().strip())
    output = args.output_dir.resolve()
    if output == source or source in output.parents:
        p.error('Private output directory must be outside the repository')
    evidence_path = safe_relative(args.acceptance_evidence)
    commit = args.accepted_revision
    if git(source, 'rev-parse', commit + '^{commit}').decode().strip() != commit:
        stop('Commit mismatch')
    evidence = git(source, 'show', commit + ':' + evidence_path)
    if not evidence.strip():
        stop('Acceptance evidence is empty')
    tree = git(source, 'rev-parse', commit + ':product').decode().strip()
    files = []
    with tarfile.open(fileobj=io.BytesIO(git(source, 'archive', '--format=tar', commit, 'product'))) as archive:
        for member in archive.getmembers():
            path = Path(member.name)
            if path.is_absolute() or '..' in path.parts or not (member.isdir() or member.isfile()):
                stop('Unsafe archive path or nonregular file')
            if member.isfile():
                files.append((member.name, archive.extractfile(member).read(), member.mode))
    scan_build_context(files)
    os.umask(0o077)
    output.mkdir(parents=True, exist_ok=True)
    run = Path(tempfile.mkdtemp(prefix='tablekeeper-deploy-', dir=output))
    for name, content, mode in files:
        target = run/'snapshot'/name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        target.chmod(0o700 if mode & 0o111 else 0o600)
    product = run/'snapshot'/'product'
    for name in ('Dockerfile', 'requirements.txt', 'firestore.rules', 'firestore.indexes.json'):
        if not (product/name).is_file():
            stop('Accepted product missing deployment input: ' + name)
    (run/'hosting-empty').mkdir()
    for name in ('firestore.rules', 'firestore.indexes.json'):
        shutil.copyfile(product/name, run/name)
    config = {
        'firestore': [{'database': args.database, 'rules': 'firestore.rules', 'indexes': 'firestore.indexes.json'}],
        'hosting': {'site': args.site, 'public': 'hosting-empty', 'ignore': ['**/.*'],
                    'rewrites': [{'source': '**', 'run': {'serviceId': args.service, 'region': args.region, 'pinTag': True}}],
                    'headers': [{'source': '**', 'headers': [{'key': 'Cache-Control', 'value': 'private, no-store'}]}]},
    }
    (run/'firebase.json').write_text(json.dumps(config, indent=2))
    env = {'TABLEKEEPER_MODE': 'production', 'TABLEKEEPER_STORAGE': 'firestore',
           'GOOGLE_CLOUD_PROJECT': args.project, 'TABLEKEEPER_DATABASE': args.database,
           'TABLEKEEPER_COLLECTION': 'proofline_demo', 'TABLEKEEPER_PUBLIC_ORIGIN': f'https://{args.site}.web.app',
           'TABLEKEEPER_PUBLIC_DEMO': '1'}
    (run/'runtime-env.yaml').write_text(json.dumps(env, indent=2))
    registry = f'{args.region}-docker.pkg.dev/{args.project}/{args.artifact_repository}/{args.service}'
    tag = registry + ':accepted-' + commit
    image = registry + '@' + (args.image_digest or 'sha256:' + '0'*64)
    job = args.cleanup_job or args.service + '-cleanup'
    scheduler = args.scheduler_name or args.service + '-cleanup-hourly'
    if not all(re.fullmatch(r'[a-z][a-z0-9-]{1,62}', name) for name in (job, scheduler)):
        p.error('Invalid dedicated cleanup resource name')
    if len(job)>63 or len(scheduler)>63:
        p.error('Service name is too long for derived cleanup resource names')
    common = ['--project', args.project, '--region', args.region]
    commands = {
        'build': ['gcloud', 'builds', 'submit', str(product), *common, '--tag', tag, '--quiet'],
        'datastore': ['firebase', 'deploy', '--project', args.project, '--config', str(run/'firebase.json'), '--only', 'firestore', '--non-interactive'],
        'service': ['gcloud', 'run', 'deploy', args.service, *common, '--image', image, '--service-account', args.runtime_sa,
                    '--allow-unauthenticated', '--min', '0', '--max', '2', '--min-instances', '0', '--max-instances', '2',
                    '--cpu', '2', '--memory', '2Gi', '--concurrency', '16', '--timeout', '30', '--port', '8080',
                    '--env-vars-file', str(run/'runtime-env.yaml'), '--clear-secrets', '--quiet'],
        'cleanup-job': ['gcloud', 'run', 'jobs', 'deploy', job, *common, '--image', image, '--service-account', args.runtime_sa,
                        '--cpu', '2', '--memory', '2Gi', '--tasks', '1', '--parallelism', '1', '--max-retries', '0',
                        '--task-timeout', '300s', '--env-vars-file', str(run/'runtime-env.yaml'), '--clear-secrets',
                        '--command', 'python', '--args=-m,tablekeeper.operations,cleanup,--limit,100', '--quiet'],
        'cleanup-initial': ['gcloud', 'run', 'jobs', 'execute', job, *common, '--wait', '--quiet'],
        'cleanup-invoker': ['gcloud', 'run', 'jobs', 'add-iam-policy-binding', job, *common,
                            '--member=serviceAccount:'+args.scheduler_sa, '--role=roles/run.invoker', '--quiet'],
        'cleanup-schedule': ['gcloud', 'scheduler', 'jobs', 'create', 'http', scheduler, '--project', args.project,
                            '--location', args.region, '--schedule=0 * * * *', '--time-zone=UTC',
                            '--uri='+f'https://run.googleapis.com/v2/projects/{args.project}/locations/{args.region}/jobs/{job}:run',
                            '--http-method=POST', '--oauth-service-account-email='+args.scheduler_sa,
                            '--oauth-token-scope=https://www.googleapis.com/auth/cloud-platform',
                            '--headers=Content-Type=application/json', '--message-body={}', '--max-retry-attempts=0', '--quiet'],
        'hosting': ['firebase', 'deploy', '--project', args.project, '--config', str(run/'firebase.json'), '--only', 'hosting', '--non-interactive'],
    }
    manifest = {'status': 'plan only', 'accepted_revision': commit, 'product_tree': tree,
                'acceptance_evidence': evidence_path, 'acceptance_evidence_sha256': hashlib.sha256(evidence).hexdigest(),
                'project': args.project, 'database': args.database, 'site': args.site,
                'image_tag': tag, 'image_digest': args.image_digest, 'runtime': env, 'commands': commands}
    (run/'plan.json').write_text(json.dumps(manifest, indent=2))
    print('Private deployment record: ' + str(run))
    if not args.execute:
        print('Plan only. No cloud commands executed.')
        return
    command = commands[args.phase]
    if not shutil.which(command[0]):
        stop(command[0] + ' must be installed and authenticated on PATH')
    result = subprocess.run(command, cwd=run, capture_output=True, text=True)
    (run/(args.phase+'.log')).write_text(redact(result.stdout+'\n'+result.stderr))
    manifest.update(status='phase command finished; not full deployment acceptance', phase=args.phase, exit=result.returncode)
    (run/'plan.json').write_text(json.dumps(manifest, indent=2))
    print(args.phase + ' exit ' + str(result.returncode) + '; inspect private log before proceeding')
    if result.returncode:
        stop('Stopped without retry, force or broader fallback')
    if args.phase == 'build':
        result = subprocess.run(['gcloud', 'artifacts', 'docker', 'images', 'describe', tag,
                                 '--project', args.project, '--format=value(image_summary.digest)'],capture_output=True,text=True)
        digest = result.stdout.strip()
        if result.returncode or not re.fullmatch(r'sha256:[0-9a-f]{64}', digest):
            stop('Build finished; digest lookup failed. Inspect build before deployment')
        (run/'built-image.json').write_text(json.dumps({'accepted_revision':commit,'product_tree':tree,'image_digest':digest,'image':registry+'@'+digest},indent=2))
        print('Immutable image digest recorded privately in built-image.json')


if __name__ == '__main__':
    main()
