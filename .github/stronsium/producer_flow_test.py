"""Offline producer tests: issue_comment producer -> proof.json -> real ProofVerifier. No network, no subprocess."""
import base64, hashlib, io, os, pathlib, tempfile, unittest, zipfile
from unittest import mock
import producer_test as T
import producer_identity as I
import run_producer_comment as RC
import p4_semantic as S
from producer_context import collect_context
from proof_context import context_digest
from proof_evidence import ProofVerifier, REPO

SHA = 'a' * 40
FIX = dict(I.IDENTITY, repo_id=1111, bot_id=4242)  # ids used by the synthetic ReadService fixture
ENV = {'GITHUB_RUN_ID': '10', 'GITHUB_RUN_ATTEMPT': '1', 'GITHUB_EVENT_NAME': 'pull_request_target', 'GITHUB_SHA': SHA}
ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
HEAD_SRC = "import os\n\n# explain\ndef f(x):\n    return x + 1\n"
HDR = "diff --git a/plugins/a/m.py b/plugins/a/m.py\nindex 1..2 100644\n--- a/plugins/a/m.py\n+++ b/plugins/a/m.py\n"
GOOD = HDR + "@@ -1,4 +1,5 @@\n import os\n \n+# explain\n def f(x):\n     return x + 1\n"
BAD = HDR + "@@ -1,5 +1,5 @@\n import os\n \n # explain\n def f(x):\n-    return x + 0\n+    return x + 1\n"


class Svc(T.ReadService):
    def __init__(s, src=HEAD_SRC, diff=GOOD, status='modified'):
        super().__init__(); s.source = src; s.diff = diff; s.status = status

    def pages(s, path, **kw):
        if path.endswith('/files'):
            s.calls.append(('GET', path)); return [{'filename': 'plugins/a/m.py', 'status': s.status}]
        return super().pages(path, **kw)


class BinarySvc(Svc):
    """A PR whose only changed file is a non-UTF-8 (image) file."""
    def __init__(s, *, filename='docs/a.png', status='added', raw=b'\x89PNG\r\n\x1a\n\xff\xfe'):
        super().__init__(status=status); s.filename = filename; s.raw = raw

    def pages(s, path, **kw):
        if path.endswith('/files'):
            s.calls.append(('GET', path)); return [{'filename': s.filename, 'status': s.status}]
        return super().pages(path, **kw)

    def request(s, path, method='GET', **kw):
        if '/contents/' in path:
            s.calls.append(('GET', path))
            return {'type': 'file', 'encoding': 'base64', 'content': base64.b64encode(s.raw).decode()}
        return super().request(path, method, **kw)


class Flow(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory(); self.addCleanup(self.d.cleanup)
        cwd = os.getcwd(); os.chdir(self.d.name); self.addCleanup(os.chdir, cwd)
        self.pol, self.prog = I.load({'GITHUB_SHA': SHA, 'GITHUB_REPOSITORY': REPO, 'GITHUB_REF': 'refs/heads/main'})
        for n in ('socket.create_connection', 'subprocess.run', 'subprocess.Popen'):
            p = mock.patch(n, side_effect=AssertionError('network/process forbidden')); p.start(); self.addCleanup(p.stop)
        ENV['GITHUB_WORKSPACE'] = str(ROOT)

    def produce(self, svc, env=ENV):
        return RC.run(1, 0, 'proof.json', env, dict(FIX), self.pol, self.prog, svc, I.SEMANTIC)

    def zipped(self):
        b = io.BytesIO()
        with zipfile.ZipFile(b, 'w') as z: z.write('proof.json')
        return b.getvalue()

    def test_positive_digest_in_run_and_verifier_accepts(self):
        digest = self.produce(Svc())
        self.assertEqual(pathlib.Path('digest.txt').read_text().strip(), digest)
        ctx = collect_context(Svc(), 1, request_comment_id=0, **FIX)
        self.assertEqual(context_digest(ctx), digest)
        raw = self.zipped()
        run = {'id': 10, 'run_attempt': 1, 'repository': {'full_name': REPO}, 'workflow_id': 1, 'path': I.WORKFLOW_PATH, 'head_sha': SHA,
               'event': 'pull_request_target', 'status': 'completed', 'conclusion': 'success', 'actor': {'id': 206803862},
               'triggering_actor': {'id': 353707643}, 'head_branch': 'main'}
        art = {'id': 11, 'expired': False, 'workflow_run': {'id': 10, 'head_sha': SHA}, 'digest': 'sha256:' + hashlib.sha256(raw).hexdigest()}
        def get(p):
            if '/contents/' in p:  # the real closure, served from this checkout
                rel = p.split('/contents/')[1].split('?')[0]
                return {'type': 'file', 'encoding': 'base64', 'content': base64.b64encode((ROOT / rel).read_bytes()).decode()}
            return run if '/runs/' in p else art
        rc = ProofVerifier(self.pol, get).verify(raw, ctx, run_id=10, attempt=1, artifact_id=11)
        self.assertEqual(rc.test_ids, ('diff-covers-files',))
        self.assertEqual(self.pol.event, 'pull_request_target'); self.assertEqual(self.pol.allowed_actor_ids, (206803862, 353707643))

    def test_behavior_change_and_added_file_yield_no_proof(self):
        with self.assertRaisesRegex(ValueError, 'p4_sem_ast_changed'): self.produce(Svc(diff=BAD))
        self.assertFalse(pathlib.Path('proof.json').exists())
        with self.assertRaises(ValueError): self.produce(Svc(status='added'))

    def test_wrong_event_inputs_and_moving_head(self):
        for ev in ('workflow_dispatch', 'pull_request', 'issue_comment', None):
            env = dict(ENV); env.pop('GITHUB_EVENT_NAME') if ev is None else env.update(GITHUB_EVENT_NAME=ev)
            with self.assertRaisesRegex(ValueError, 'wrong_event'): self.produce(Svc(), env)
        for pr, c in ((0, 0), (1, -1), (True and 1, 'x')):
            with self.assertRaises(ValueError): RC.run(pr, c, 'proof.json', ENV, dict(FIX), self.pol, self.prog, Svc(), I.SEMANTIC)
        s = Svc(); s.mutate_head = True
        with self.assertRaises(ValueError): self.produce(s)

    def test_issue_comment_variant_needs_real_comment_id(self):
        pol, prog = I.load({'GITHUB_SHA': SHA, 'GITHUB_REPOSITORY': REPO, 'GITHUB_REF': 'refs/heads/main'}, event='issue_comment')
        with self.assertRaisesRegex(ValueError, 'invalid_comment'):
            RC.run(1, 0, 'proof.json', dict(ENV, GITHUB_EVENT_NAME='issue_comment'), dict(FIX), pol, prog, Svc(), I.SEMANTIC)

    def test_identity_refuses_off_default_branch(self):
        env = {'GITHUB_SHA': SHA, 'GITHUB_REPOSITORY': REPO, 'GITHUB_REF': 'refs/heads/main'}
        for bad in (dict(env, GITHUB_REF='refs/heads/x'), dict(env, GITHUB_REPOSITORY='x/y'), dict(env, GITHUB_SHA='zz'), {}):
            with self.assertRaises(ValueError): I.load(bad)

    def test_proof_binds_run_commit_and_closure_digest(self):
        self.produce(Svc())
        import json
        prod = json.loads(pathlib.Path('proof.json').read_text())['producer']
        self.assertEqual(prod['head_sha'], SHA)
        self.assertEqual(prod['closure_sha256'], self.pol.closure_sha256)
        from proof_closure import local_closure_digest
        self.assertEqual(prod['closure_sha256'], local_closure_digest(str(ROOT)))


class ScopeReporting(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        cwd = os.getcwd()
        os.chdir(self.temp.name)
        self.addCleanup(os.chdir, cwd)
        self.env = dict(ENV, GITHUB_REPOSITORY=REPO, GITHUB_REF='refs/heads/main',
                        GITHUB_OUTPUT='outputs.txt', GITHUB_STEP_SUMMARY='summary.md')
        self.pr = {'state': 'open', 'draft': False, 'changed_files': 1,
                   'head': {'sha': 'a' * 40, 'repo': {'id': I.IDENTITY['repo_id']}},
                   'base': {'sha': 'b' * 40, 'repo': {'id': I.IDENTITY['repo_id'], 'full_name': REPO}}}

    def call(self, *, failure=None, digest='d' * 64):
        transport = mock.Mock()
        transport.request.return_value = self.pr
        with mock.patch.object(RC, 'GitHubProofTransport', return_value=transport), mock.patch.object(
                RC, 'run', side_effect=failure, return_value=digest) as run:
            RC.main(['producer', '30', '0', 'proof.json'], self.env)
            return run

    def status(self):
        import json
        return json.loads(pathlib.Path('proof-status.json').read_text())

    def test_canonical_identity_and_old_name_refused(self):
        from producer_context import REPO as collector_repo
        self.assertEqual(REPO, 'Abelion512/AHP')
        self.assertEqual(collector_repo, REPO)
        I.load(self.env)
        with self.assertRaises(ValueError):
            I.load(dict(self.env, GITHUB_REPOSITORY='/'.join(['Abelion512', 'abelion-hermes-plugins'])))

    def test_fork_scope_clears_stale_proof_and_never_runs(self):
        pathlib.Path('proof.json').write_text('stale')
        pathlib.Path('digest.txt').write_text('stale')
        self.pr['head']['repo']['id'] = 9001
        run = self.call()
        run.assert_not_called()
        self.assertEqual(self.status(), {'status': 'not_applicable', 'proof_available': False,
                         'autoapprove_granted': False, 'reason': 'fork_head_outside_proof_scope'})
        self.assertFalse(pathlib.Path('proof.json').exists())
        self.assertFalse(pathlib.Path('digest.txt').exists())
        self.assertEqual(pathlib.Path('outputs.txt').read_text(), 'proof_available=false\n')
        self.assertIn('No proof artifact and no auto-approval', pathlib.Path('summary.md').read_text())

    def test_file_limit_and_draft_do_not_expand_scope(self):
        for change, reason in [({'changed_files': 31}, 'changed_file_limit_outside_proof_scope'),
                               ({'draft': True}, 'draft_pr')]:
            with self.subTest(reason=reason):
                original = dict(self.pr)
                self.pr.update(change)
                self.call().assert_not_called()
                self.assertEqual(self.status()['reason'], reason)
                self.pr = original

    def test_known_semantic_refusals_are_no_proof_only(self):
        for reason in ['p4_sem_not_python', 'p4_sem_ast_changed', 'p4_sem_source_sensitive',
                       'p4_sem_status_not_modified', 'p4_sem_directive_comment_changed', 'p4_sem_header_lines_changed',
                       'p4_sem_structural_change', 'open_findings_unverified']:
            with self.subTest(reason=reason):
                self.call(failure=S.ScopeNotApplicable(reason)).assert_called_once()
                self.assertEqual(self.status()['status'], 'not_applicable')
                self.assertFalse(pathlib.Path('proof.json').exists())

    def test_malformed_provenance_and_unknown_failures_still_fail(self):
        for field, value in [('base', {}), ('head', {}), ('changed_files', True), ('draft', 'false')]:
            with self.subTest(field=field):
                previous = self.pr[field]
                self.pr[field] = value
                with self.assertRaises(ValueError):
                    self.call()
                self.assertFalse(pathlib.Path('proof-status.json').exists())
                self.pr[field] = previous
        for failure in [ValueError('producer_head_or_base_changed'), ValueError('test_failed'),
                        S.ScopeNotApplicable('unexpected_reason')]:
            with self.subTest(failure=failure), self.assertRaises(ValueError):
                self.call(failure=failure)

    def test_wrong_event_and_missing_runner_cannot_be_skip(self):
        for update in [{'GITHUB_EVENT_NAME': 'pull_request'}, {'GITHUB_RUN_ID': ''},
                       {'GITHUB_REPOSITORY': 'other/repo'}, {'GITHUB_REF': 'refs/heads/other'}]:
            with self.subTest(update=update):
                original = self.env
                self.env = dict(original, **update)
                with self.assertRaises(ValueError):
                    self.call()
                self.env = original

    def test_draft_rule_matches_existing_collector(self):
        service = T.ReadService()
        original = service.request
        def request(path, **kwargs):
            result = original(path, **kwargs)
            if path.endswith('/pulls/1'):
                result['draft'] = True
            return result
        service.request = request
        with self.assertRaisesRegex(ValueError, 'producer_pr_not_eligible'):
            collect_context(service, 1, request_comment_id=0, **FIX)
        self.pr['draft'] = True
        self.assertEqual(RC.eligibility(mock.Mock(request=mock.Mock(return_value=self.pr)), 1, I.IDENTITY), 'draft_pr')

    def test_shared_file_limit_matches_collector_boundary(self):
        from producer_context import MAX_PROOF_FILES
        self.assertEqual(MAX_PROOF_FILES, 30)
        self.pr['changed_files'] = MAX_PROOF_FILES
        service = mock.Mock(request=mock.Mock(return_value=self.pr))
        self.assertIsNone(RC.eligibility(service, 1, I.IDENTITY))
        self.pr['changed_files'] += 1
        self.assertEqual(RC.eligibility(service, 1, I.IDENTITY), 'changed_file_limit_outside_proof_scope')

    def test_real_main_classifier_refusal_has_no_proof(self):
        class CanonicalService(Svc):
            def request(service, path, **kwargs):
                value = super().request(path, **kwargs)
                if path.endswith('/pulls/1'):
                    value['head']['repo']['id'] = I.IDENTITY['repo_id']
                    value['base']['repo'] = {'id': I.IDENTITY['repo_id'], 'full_name': REPO}
                return value
        self.env['GITHUB_WORKSPACE'] = str(ROOT)
        with mock.patch.object(RC, 'GitHubProofTransport', return_value=CanonicalService(diff=BAD)):
            RC.main(['producer', '1', '0', 'proof.json'], self.env)
        self.assertEqual(self.status()['reason'], 'p4_sem_ast_changed')
        self.assertFalse(pathlib.Path('proof.json').exists())
        self.assertFalse(pathlib.Path('digest.txt').exists())

    def test_binary_file_is_no_proof_not_a_crash(self):
        # Regression: a PR carrying an image used to crash the collector with a strict
        # UTF-8 decode error (job exited 1). It is now a scope refusal: no proof, exit 0.
        class CanonicalBinary(BinarySvc):
            def request(service, path, method='GET', **kwargs):
                value = super().request(path, method, **kwargs)
                if path.endswith('/pulls/1'):
                    value['head']['repo']['id'] = I.IDENTITY['repo_id']
                    value['base']['repo'] = {'id': I.IDENTITY['repo_id'], 'full_name': REPO}
                return value
        self.env['GITHUB_WORKSPACE'] = str(ROOT)
        with mock.patch.object(RC, 'GitHubProofTransport', return_value=CanonicalBinary()):
            RC.main(['producer', '1', '0', 'proof.json'], self.env)
        self.assertEqual(self.status(), {'status': 'not_applicable', 'proof_available': False,
                         'autoapprove_granted': False, 'reason': 'p4_sem_status_not_modified'})
        self.assertFalse(pathlib.Path('proof.json').exists())
        self.assertFalse(pathlib.Path('digest.txt').exists())
        self.assertEqual(pathlib.Path('outputs.txt').read_text(), 'proof_available=false\n')

    def test_open_review_findings_are_no_proof_not_a_failure(self):
        class FindingSvc(Svc):
            def pages(s, path, **kw):
                if '/pulls/' in path and path.endswith('/comments'):
                    s.calls.append(('GET', path))
                    return [{'id': 7, 'user': {'id': 999}, 'body': 'reviewer finding', 'updated_at': 'before'}]
                return super().pages(path, **kw)
        class CanonicalFinding(FindingSvc):
            def request(service, path, method='GET', **kwargs):
                value = super().request(path, method, **kwargs)
                if path.endswith('/pulls/1'):
                    value['head']['repo']['id'] = I.IDENTITY['repo_id']
                    value['base']['repo'] = {'id': I.IDENTITY['repo_id'], 'full_name': REPO}
                return value
        self.env['GITHUB_WORKSPACE'] = str(ROOT)
        with mock.patch.object(RC, 'GitHubProofTransport', return_value=CanonicalFinding()):
            RC.main(['producer', '1', '0', 'proof.json'], self.env)
        self.assertEqual(self.status(), {'status': 'not_applicable', 'proof_available': False,
                         'autoapprove_granted': False, 'reason': 'open_findings_unverified'})
        self.assertFalse(pathlib.Path('proof.json').exists())
        self.assertFalse(pathlib.Path('digest.txt').exists())

    def test_success_outputs_proof_available_not_autoapproval(self):
        self.call().assert_called_once()
        self.assertEqual(self.status()['status'], 'proof_produced')
        self.assertFalse(self.status()['autoapprove_granted'])
        self.assertIn('proof_available=true', pathlib.Path('outputs.txt').read_text())
        self.assertFalse(S.OBSERVATIONAL_SCOPE_OWNER_ACCEPTED)


if __name__ == '__main__':
    unittest.main()
