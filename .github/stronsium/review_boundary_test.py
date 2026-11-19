"""Review regressions: reject malformed remote metadata before contents reads."""
import unittest
from unittest.mock import patch
from producer_test import ReadService
from producer_context import collect_context
from github_proof_transport import GitHubProofTransport, SelectedArtifactProof
from proof_evidence import receipt_matches
from proof_test import CONTEXT
import producer_test as T
from p4_semantic import reverse_apply

IDENTITY = dict(repo_id=1111,bot_id=4242,owner_id=777,bot_slug='stronsium',request_comment_id=1)

class ReviewBoundaries(unittest.TestCase):
    def test_bad_sha_rejected_before_other_reads(self):
        for sha in ('a'*39, 'a'*40+'?ref=elsewhere', None, True):
            gh=ReadService(); original=gh.request
            def request(path,**kw):
                result=original(path,**kw);result['head']['sha']=sha;return result
            gh.request=request
            with self.subTest(sha=sha),self.assertRaisesRegex(ValueError,'invalid_producer_sha'):
                collect_context(gh,1,**IDENTITY)
            self.assertEqual(len(gh.calls),1)

    def test_bad_paths_rejected_before_source_fetch(self):
        for path in ('','a//b.py','../b.py','/a.py','a/../b.py','a\\b.py','a\nb.py'):
            gh=ReadService();original=gh.pages
            def pages(url,**kw):
                return [{'filename':path,'status':'modified'}] if url.endswith('/files') else original(url,**kw)
            gh.pages=pages
            with self.subTest(path=path),self.assertRaisesRegex(ValueError,'invalid_producer_path'):
                collect_context(gh,1,**IDENTITY)
            self.assertFalse(any('/contents/' in url for method,url in gh.calls))

    def test_bad_base64_named_refusal(self):
        gh=ReadService();original=gh.request
        def request(path,**kw):
            return {'type':'file','encoding':'base64','content':'!!!!'} if '/contents/' in path else original(path,**kw)
        gh.request=request
        with self.assertRaisesRegex(ValueError,'malformed_producer_source'):collect_context(gh,1,**IDENTITY)

    def test_transport_rejects_empty_segments(self):
        gh=GitHubProofTransport(lambda:'test-placeholder')
        # A valid Stellarium path must pass the root check, so the refusal below
        # proves the empty-segment guard rather than a wrong-root rejection.
        request=gh._api('/repos/Abelion512/Stellarium/contents/a/b.py')
        self.assertEqual(request.get_method(),'GET')
        with self.assertRaisesRegex(ValueError,'api_path_outside_repository'):
            gh._api('/repos/Abelion512/Stellarium/contents/a//b.py')

    def test_zero_count_add_delete_and_unicode_line_separator(self):
        self.assertEqual(reverse_apply('x=1\n','@@ -0,0 +1,1 @@\n+x=1\n'),'')
        self.assertEqual(reverse_apply('','@@ -1,1 +0,0 @@\n-x=1\n'),'x=1\n')
        head='x="a\u2028b"\n# explain\n'
        section='@@ -1,1 +1,2 @@\n x="a\u2028b"\n+# explain\n'
        self.assertEqual(reverse_apply(head,section),'x="a\u2028b"\n')
        self.assertEqual(reverse_apply(head.replace('\n','\r\n'),section.replace('\n','\r\n')),'x="a\u2028b"\n')

class MissingArtifactBoundary(unittest.TestCase):
    def test_no_artifact_id_cannot_create_proof_source(self):
        transport = GitHubProofTransport(lambda:'test-placeholder')
        policy = T.policy(T.program())
        for artifact_id in (None, 0, False, -1):
            with self.subTest(artifact_id=artifact_id), self.assertRaisesRegex(ValueError, 'invalid_selected_proof'):
                SelectedArtifactProof(policy, transport, run_id=10, attempt=1, artifact_id=artifact_id)

    def test_missing_artifact_download_cannot_yield_receipt(self):
        import urllib.error
        transport = GitHubProofTransport(lambda:'test-placeholder')
        selected = SelectedArtifactProof(T.policy(T.program()), transport, run_id=10, attempt=1, artifact_id=11)
        with patch.object(transport, 'artifact_zip', side_effect=urllib.error.HTTPError(
                'https://api.github.com', 404, 'not found', {}, None)):
            with self.assertRaises(urllib.error.HTTPError):
                selected(CONTEXT)
        self.assertFalse(receipt_matches(None, CONTEXT))
        self.assertFalse(receipt_matches({'status':'success', 'conclusion':'success'}, CONTEXT))

if __name__=='__main__':unittest.main()
