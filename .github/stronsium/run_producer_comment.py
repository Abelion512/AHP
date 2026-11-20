"""Runs inside the pinned default-branch producer workflow (pull_request_target; issue_comment also supported). GET-only. Never checks out or runs PR code.
The context digest is computed HERE from independently collected data; no digest or context is an input.
Inputs: PR number and triggering comment id (workflow event fields, validated as digits). Output: proof.json plus
a one-line digest file used only to NAME the artifact (the consumer re-derives the name from its own context)."""
import io,json,os,pathlib,re,sys,zipfile
from github_proof_transport import GitHubProofTransport
from producer_context import collect_context, MAX_PROOF_FILES
from proof_closure import local_closure_digest
from proof_context import context_digest
from proof_producer import ProofProducer

def run(pr_number,comment_id,out,env,identity,policy,program,transport,semantic=None):
    for k in ('GITHUB_RUN_ID','GITHUB_RUN_ATTEMPT'):
        if not env.get(k,'').isdigit():raise ValueError('runner_identity_missing')
    head_sha=env.get('GITHUB_SHA','')
    if not re.fullmatch('[a-f0-9]{40}',head_sha):raise ValueError('runner_head_sha_missing')
    # The closure pin is computed HERE from the default-branch checkout; produce()
    # refuses when it does not match the pinned policy digest.
    closure=local_closure_digest(env.get('GITHUB_WORKSPACE',''))
    if policy is None or program is None:raise ValueError('producer_policy_unset')
    if env.get('GITHUB_EVENT_NAME')!=policy.event or policy.event not in ('issue_comment','pull_request_target'):raise ValueError('wrong_event')
    if type(pr_number) is not int or not 0<pr_number<=999999999:raise ValueError('invalid_pr')
    # pull_request_target has no request comment: id 0 (nothing to exclude). issue_comment needs a real id.
    if type(comment_id) is not int or not 0<=comment_id<=9007199254740991 or (comment_id==0 and policy.event=='issue_comment'):raise ValueError('invalid_comment')
    if out!='proof.json':raise ValueError('invalid_output_path')
    ident=dict(identity);ident['request_comment_id']=comment_id
    context=collect_context(transport,pr_number,**ident)
    digest=context_digest(context)
    producer=ProofProducer(policy,program,semantic)
    archive=producer.produce(context,run_id=int(env['GITHUB_RUN_ID']),attempt=int(env['GITHUB_RUN_ATTEMPT']),
        head_sha=head_sha,closure_sha256=closure)
    latest=collect_context(transport,pr_number,**ident)
    if context_digest(latest)!=digest:raise ValueError('producer_snapshot_changed_during_checks')
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        if z.namelist()!=['proof.json']:raise ValueError('producer_archive_shape')
        body=z.read('proof.json')
    pathlib.Path(out).write_bytes(body)
    pathlib.Path('digest.txt').write_text(digest+'\n')
    return digest

def eligibility(transport, pr_number, identity):
    """Read-only scope preflight. Unsupported PRs receive no proof, not approval."""
    from proof_evidence import REPO
    pr = transport.request('/repos/' + REPO + '/pulls/' + str(pr_number))
    try:
        if (pr['base']['repo']['id'] != identity['repo_id']
                or pr['base']['repo']['full_name'] != REPO):
            raise ValueError('producer_repository_mismatch')
        for ref in ('head', 'base'):
            if not isinstance(pr[ref]['sha'], str) or not re.fullmatch('[a-f0-9]{40}', pr[ref]['sha']):
                raise ValueError('invalid_producer_sha')
        head_id = pr['head']['repo']['id']
        count = pr['changed_files']
        if type(head_id) is not int or head_id <= 0 or type(count) is not int or count <= 0:
            raise ValueError('malformed_producer_source')
        if pr['state'] != 'open' or type(pr['draft']) is not bool:
            raise ValueError('producer_pr_not_eligible')
        if pr['draft']:
            return 'draft_pr'
        if head_id != identity['repo_id']:
            return 'fork_head_outside_proof_scope'
        if count > MAX_PROOF_FILES:
            return 'changed_file_limit_outside_proof_scope'
        return None
    except (KeyError, TypeError, AttributeError) as exc:
        raise ValueError('malformed_producer_source') from exc


def report_outcome(env, *, digest=None, reason=None):
    # Reasons are fixed application constants, never PR text or exception prose.
    available = digest is not None
    result = {'status': 'proof_produced' if available else 'not_applicable',
              'proof_available': available, 'autoapprove_granted': False}
    if reason:
        result['reason'] = reason
    pathlib.Path('proof-status.json').write_text(json.dumps(result, sort_keys=True) + '\n')
    if env.get('GITHUB_OUTPUT'):
        with open(env['GITHUB_OUTPUT'], 'a') as target:
            target.write('proof_available=' + str(available).lower() + '\n')
            if available:
                target.write('digest=' + digest + '\n')
    if env.get('GITHUB_STEP_SUMMARY'):
        with open(env['GITHUB_STEP_SUMMARY'], 'a') as target:
            target.write('## Stronsium proof\n\n')
            target.write('Proof produced; approval still requires independent verification.\n' if available else
                         'Not applicable: ' + reason + '. No proof artifact and no auto-approval. Runtime tests and review remain required.\n')
    print(json.dumps(result, sort_keys=True))


def main(argv,env):
    import producer_identity as I
    from p4_semantic import ScopeNotApplicable
    if len(argv)!=4 or not re.fullmatch('[0-9]{1,9}',argv[1]) or not re.fullmatch('[0-9]{1,16}',argv[2]) or argv[3]!='proof.json':raise ValueError('usage')
    pr_number = int(argv[1])
    if pr_number <= 0:
        raise ValueError('invalid_pr')
    policy,program=I.load(env)
    if env.get('GITHUB_EVENT_NAME') != policy.event:
        raise ValueError('wrong_event')
    for key in ('GITHUB_RUN_ID', 'GITHUB_RUN_ATTEMPT'):
        if not env.get(key, '').isdigit():
            raise ValueError('runner_identity_missing')
    if int(argv[2]) == 0 and policy.event == 'issue_comment':
        raise ValueError('invalid_comment')
    # Workspace reuse must never upload an earlier run's proof on a scope refusal.
    for filename in ('proof.json', 'digest.txt', 'proof-status.json'):
        pathlib.Path(filename).unlink(missing_ok=True)
    transport = GitHubProofTransport(lambda:env.get('GH_TOKEN',''))
    # run() independently re-collects context and rejects head/base/review movement;
    # this preflight cannot turn an older metadata snapshot into a positive proof.
    reason = eligibility(transport, pr_number, I.IDENTITY)
    if reason:
        report_outcome(env, reason=reason)
        return
    try:
        digest = run(pr_number,int(argv[2]),argv[3],env,I.IDENTITY,policy,program,transport,I.SEMANTIC)
    except ScopeNotApplicable as exc:
        # This type is raised only for known scope refusals by the pinned classifier.
        allowed = {'p4_sem_status_not_modified', 'p4_sem_not_python', 'p4_sem_ast_changed',
                   'p4_sem_source_sensitive', 'p4_sem_directive_comment_changed', 'p4_sem_header_lines_changed',
                   'p4_sem_structural_change', 'p4_sem_unparseable', 'p4_sem_source_out_of_bounds',
                   'p4_sem_review_context_out_of_bounds', 'p4_sem_context_out_of_bounds',
                   'open_findings_unverified'}
        if str(exc) not in allowed:
            raise
        report_outcome(env, reason=str(exc))
        return
    report_outcome(env, digest=digest)

if __name__=='__main__':main(sys.argv,dict(os.environ))
