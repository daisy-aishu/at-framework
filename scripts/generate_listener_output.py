import json
import os
import subprocess
import urllib.request

repo = os.environ.get('REPO','')
branch = os.environ.get('BRANCH','')
before_sha = os.environ.get('BEFORE_SHA','')
sha = os.environ.get('SHA','')
msg = os.environ.get('MSG','')
token = os.environ.get('SOURCE_REPO_TOKEN','')

if branch.startswith('refs/heads/'):
  branch = branch[len('refs/heads/'):]

def gh_compare(owner_repo: str, before: str, after: str):
  url = f"https://api.github.com/repos/{owner_repo}/compare/{before}...{after}"
  req = urllib.request.Request(url)
  req.add_header('Accept', 'application/vnd.github+json')
  if token:
    req.add_header('Authorization', f"Bearer {token}")
  with urllib.request.urlopen(req, timeout=60) as resp:
    return json.loads(resp.read().decode('utf-8'))

changed_files = []
diffs = []

zeros = '0' * 40
if repo and before_sha and sha and before_sha != zeros:
  data = gh_compare(repo, before_sha, sha)
  for f in (data.get('files') or []):
    path = (f.get('filename') or '').replace('\\','/')
    status = (f.get('status') or 'modified').lower()
    if status not in ('added','modified','removed'):
      status = 'modified'
    if path:
      changed_files.append({'path': path, 'status': status})
      if 'patch' in f and f.get('patch'):
        diffs.append({'path': path, 'patch': f.get('patch')})
else:
  # Fallback: use git diff (no patch content)
  try:
    out = subprocess.check_output(['git','-C','source','diff','--name-status','HEAD~1..HEAD'], text=True)
  except Exception:
    out = ''
  for line in out.splitlines():
    line = line.strip()
    if not line:
      continue
    parts = line.split(None, 1)
    if len(parts) == 2:
      st, path = parts[0], parts[1]
    else:
      st, path = 'M', parts[0]
    st = st.lower()
    if st in ('a','added'):
      status = 'added'
    elif st in ('d','deleted','remove','removed'):
      status = 'removed'
    else:
      status = 'modified'
    path = path.replace('\\','/').strip()
    if path:
      changed_files.append({'path': path, 'status': status})

commit_url = f"https://github.com/{repo}/commit/{sha}" if repo and sha else ''

out = {
  'repo': repo,
  'branch': branch,
  'commit_sha': sha,
  'commit_message': msg,
  'commit_url': commit_url,
  'changed_files': changed_files,
  'diffs': diffs,
}

with open('listener_output.json','w',encoding='utf-8') as f:
  json.dump(out,f,ensure_ascii=False,indent=2)

print(json.dumps(out, ensure_ascii=False, indent=2))