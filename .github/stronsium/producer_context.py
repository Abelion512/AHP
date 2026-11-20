"""Independent producer collection through an injected authenticated READ transport.
No candidate-supplied context/digest is accepted and no candidate code runs.
"""
import base64
import binascii
import hashlib
import re
from urllib.parse import quote
from proof_context import normalize_context
from triage import collect
from p4_semantic import ScopeNotApplicable

MAX_PROOF_FILES = 30
MAX_SOURCE_BYTES = 240000


def source_text(raw):
    """Deterministic text for a changed file; non-UTF-8 bytes are marked, never lossily decoded.

    A binary file has no AST-equivalence proof. The marker keeps the context digest
    reproducible across the producer's two independent collections, and the semantic
    classifier refuses the file by path/status before its (non-text) diff section is parsed.
    """
    try:
        return raw.decode('utf-8','strict')
    except UnicodeDecodeError:
        return 'binary-source sha256='+hashlib.sha256(raw).hexdigest()

REPO='Abelion512/Stellarium'
ROOT='/repos/'+REPO

def collect_context(gh,pr_number,*,repo_id,bot_id,owner_id,bot_slug,request_comment_id):
    """Fetch full source/diff and reviewer snapshot, reject concurrent movement.

    Adapter must expose strict UTF-8 `raw=True` diff reads and complete pages.
    Token permissions, network limits and GET-only behavior belong to adapter.
    This function never dispatches a workflow or trusts an input context hash.
    """
    if type(pr_number) is not int or pr_number<=0:raise ValueError('invalid_pr')
    if type(repo_id) is not int or repo_id<=0:raise ValueError('invalid_repo_id')
    try:
        pr=gh.request(ROOT+'/pulls/'+str(pr_number))
        if pr['state']!='open' or pr.get('draft') is not False or pr['head']['repo']['id']!=repo_id:
            raise ValueError('producer_pr_not_eligible')
        head,base=pr['head']['sha'],pr['base']['sha']
        if any(type(sha) is not str or not re.fullmatch('[a-f0-9]{40}',sha) for sha in (head,base)):
            raise ValueError('invalid_producer_sha')
        discussions,fingerprint,_=collect(gh,pr_number,bot_id,request_comment_id,owner_id,bot_slug)
        files=gh.pages(ROOT+'/pulls/'+str(pr_number)+'/files')
        if type(files) is not list or not 0<len(files)<=MAX_PROOF_FILES:raise ValueError('producer_file_count')
        if type(pr.get('changed_files')) is not int or pr['changed_files']!=len(files):raise ValueError('producer_file_coverage_mismatch')
        paths=[];sources={}
        for f in files:
            path=f['filename'];status=f['status']
            if type(path) is not str or type(status) is not str:raise ValueError('producer_source_status')
            # A removed or renamed file has no head source and no AST-equivalence proof.
            # Refuse the PR for this lane instead of failing the producer.
            if status not in ('added','modified'):raise ScopeNotApplicable('p4_sem_status_not_modified')
            if (not path or path.startswith('/') or '\\' in path
                    or any(part in ('','.','..') for part in path.split('/'))
                    or any(ord(c)<32 for c in path)):
                raise ValueError('invalid_producer_path')
            if path in sources:raise ValueError('producer_duplicate_path')
            item=gh.request(ROOT+'/contents/'+quote(path,safe='/')+'?ref='+head)
            if item.get('encoding')!='base64' or item.get('type','file')!='file':raise ValueError('producer_source_encoding')
            encoded=item['content']
            if type(encoded) is not str:raise ValueError('producer_source_encoding')
            raw=base64.b64decode(''.join(encoded.split()),validate=True)
            if len(raw)>MAX_SOURCE_BYTES:raise ScopeNotApplicable('p4_sem_source_out_of_bounds')
            sources[path]=source_text(raw)
            paths.append({'filename':path,'status':status})
        diff=gh.request(ROOT+'/compare/'+base+'...'+head,raw=True)
        if type(diff) is bytes:diff=diff.decode('utf-8','strict')
        if type(diff) is not str:raise ValueError('producer_diff_type')
        try:
            context=normalize_context({'pr':pr_number,'sha':head,'base':base,'paths':paths,'sources':sources,
                'diff':diff,'comments_fingerprint':fingerprint,
                'finding_ids':[str(d['kind'])+':'+str(d['id']) for d in discussions]})
        except ValueError as exc:
            # A context over MAX_CONTEXT is out of this lane's bounds, not malformed
            # evidence: no proof, not a producer failure.
            if str(exc)!='context_limit':raise
            raise ScopeNotApplicable('p4_sem_context_out_of_bounds') from exc
        newest=gh.request(ROOT+'/pulls/'+str(pr_number))
        if (newest['head']['sha']!=head or newest['base']['sha']!=base or newest['state']!='open'
                or newest.get('draft') is not False or type(newest.get('changed_files')) is not int or newest.get('changed_files')!=len(files)):raise ValueError('producer_head_or_base_changed')
        _,latest_fingerprint,_=collect(gh,pr_number,bot_id,request_comment_id,owner_id,bot_slug)
        if latest_fingerprint!=fingerprint:raise ValueError('producer_comments_changed')
        return context
    except (KeyError,TypeError,AttributeError,UnicodeError,binascii.Error) as exc:
        raise ValueError('malformed_producer_source') from exc
